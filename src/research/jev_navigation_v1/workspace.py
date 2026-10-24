"""Write-once offline navigation bundles. Only this new workspace is ever mutated."""
from __future__ import annotations

from pathlib import Path
from src.research.spec import canonical, digest
from . import contracts as K, navigation as N


def write(path, value, *, raw=False):
    with Path(path).open('xb') as handle:
        handle.write(value if raw else canonical(value))


def new_directory(out):
    target = Path(out).resolve()
    K.need(not target.exists(), 'workspace must be a new directory')
    if target.is_relative_to(N.ROOT):
        relative = target.relative_to(N.ROOT)
        K.need(len(relative.parts) >= 2 and relative.parts[0] == '.research' and relative.parts[1].startswith('jev-navigation-v1-'),
               'repository workspaces must be ignored .research/jev-navigation-v1-* directories')
    else:
        K.need(not any((p / '.git').exists() for p in target.parents), 'cannot write navigation artifacts into another Git checkout')
    return target


def prepare(input_path, out):
    bundle = N.derive(input_path)
    target = new_directory(out)
    K.need(not any(Path(p).is_relative_to(target) for p in bundle['pins']), 'workspace cannot contain its own source inputs')
    target.mkdir(parents=True, exist_ok=False)
    write(target / 'bundle.json', bundle)
    return {'workspace': str(target), 'request_sha256': bundle['request_sha256'], 'task': bundle['request']['task'],
            'records': len(bundle['request']['records']), 'provider_activated': False, 'authorises': []}


def load(path):
    K.need(not Path(path).is_symlink(), 'linked workspace refused')
    root = Path(path).resolve()
    bundle = K.loads((root / 'bundle.json').read_bytes())
    K.need(bundle == N.derive(bundle['input_file']), 'STALE_OR_ALTERED_BUNDLE: input, code, records or question definitions changed')
    return root, bundle


def parse_saved(bundle, raw):
    saved = K.loads(raw)
    K.need(isinstance(saved, dict) and set(saved) == {'schema', 'fixture', 'request_sha256', 'response'}, 'strict saved-response envelope required')
    K.need(saved['schema'] == K.SAVED and saved['fixture'] == 'SYNTHETIC_NOT_MODEL_OUTPUT', 'only explicitly synthetic saved classifications are supported; live import is not implemented')
    K.need(saved['request_sha256'] == bundle['request_sha256'], 'response belongs to another request/version')
    return K.answer_set(bundle['request'], saved['response'])


def import_response(workspace, path):
    root, bundle = load(workspace)
    source = Path(path).resolve()
    K.need(not source.is_relative_to(root), 'response source must be outside the write-once workspace')
    raw = N.supplied_bytes(source, 1024 * 1024)
    # Exclusive creation claims the sole import before parsing. Refusals stay as received.
    write(root / 'response.raw', raw, raw=True)
    try:
        answers = parse_saved(bundle, raw)
    except (ValueError, TypeError, KeyError) as error:
        write(root / 'import.json', {'status': 'INVALID', 'raw_sha256': N.sha(raw), 'error': str(error), 'authorises': []})
        raise
    write(root / 'import.json', {'status': 'SYNTHETIC_VALID', 'raw_sha256': N.sha(raw), 'request_sha256': bundle['request_sha256'],
                                  'answered_questions': len(answers), 'provider_verified': False, 'authorises': []})
    return {'status': 'SYNTHETIC_VALID', 'raw_sha256': N.sha(raw), 'provider_verified': False, 'authorises': []}


def report(workspace):
    root, bundle = load(workspace)
    answers, raw_hash = None, None
    if (root / 'response.raw').exists():
        K.need((root / 'import.json').is_file(), 'interrupted import: retain files and reconcile; no retry')
        record = K.loads((root / 'import.json').read_bytes())
        raw = (root / 'response.raw').read_bytes()
        answers, raw_hash = parse_saved(bundle, raw), N.sha(raw)
        expected = {'status': 'SYNTHETIC_VALID', 'raw_sha256': raw_hash, 'request_sha256': bundle['request_sha256'],
                    'answered_questions': len(answers), 'provider_verified': False, 'authorises': []}
        K.need(record == expected, 'invalid, interrupted or altered saved response')
    return N.report(bundle, answers, raw_hash)
