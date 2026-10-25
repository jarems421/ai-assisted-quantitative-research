"""Call existing Research OS command lines in-process, exactly as documented, under the operator boundary.

Each call runs the component's own ``main(argv)``, so validation, refusals and error strings stay the component's.
Permission is checked on the whole argv before the component is imported: only listed read-only or create-only
commands, and every create-only command's target must lie inside the run's directories. Anything that records a
human act, imports a model reply, dispatches a provider, runs a pipeline or acquires a source is refused.
Discovery writes are not in the general list at all: ``preview`` admits only ``init`` of a SYNTHETIC preview
campaign and ``add source`` / ``add candidate`` to that preview ledger, inside the run's ``artifacts/anvil-preview-*``."""
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import importlib
import io
import json
from pathlib import Path
import time

from .guard import BoundaryViolation, resolved

SCOUT, CRITIC, PIPELINE = 'src.research.opportunity_scout', 'src.research.opportunity_scout.critic_v1', 'src.research.opportunity_scout.automation_v001'
QUARRY, JEV, JEVI = 'src.research.quarry_v1', 'src.research.jev_navigation_v1', 'src.research.jev_navigation_integration_v1'
DISCOVERY, GRAPH = 'src.research.discovery', 'src.research.graph'
ENTRY = {SCOUT: ('src.research.opportunity_scout.cli', {'validate', 'list', 'card', 'handoff'}),
         CRITIC: ('src.research.opportunity_scout.critic_v1.cli', {'status'}),
         PIPELINE: ('src.research.opportunity_scout.automation_v001.__main__', {'status', 'report'}),
         QUARRY: ('src.research.quarry_v1.__main__', {'import-file', 'status', 'export', 'validate-export'}),
         JEV: ('src.research.jev_navigation_v1.__main__', {'prepare', 'report'}),
         JEVI: ('src.research.jev_navigation_integration_v1.__main__', {'compose-quarry'}),
         DISCOVERY: ('src.research.discovery.cli', {'validate', 'checklist', 'source'}),
         GRAPH: ('src.research.graph.cli', {'same-gap', 'search', 'trace', 'failures'})}
# Create-only commands and the argv positions of what they write: a store argument or the value after --out.
WRITES = {(SCOUT, 'handoff'): 'store', (QUARRY, 'import-file'): '--out', (QUARRY, 'export'): '--out',
          (JEV, 'prepare'): '--out', (JEVI, 'compose-quarry'): '--out'}
PREVIEW_KINDS = ('source', 'candidate')
PREVIEW_AUTHORITY = 'SYNTHETIC_FIXTURE_NO_AUTHORITY'
STDERR_LIMIT = 4000


class NotPermitted(ValueError):
    pass


def shell(module, argv):
    """The equivalent command for manual debugging (PowerShell or POSIX quoting of spaces)."""
    quote = lambda x: f'"{x}"' if any(c in x for c in ' \t;&|') else x
    return ' '.join(['python', '-m', module, *map(quote, map(str, argv))])


def inside(path, roots):
    p = resolved(path)
    return any(p.is_relative_to(resolved(r)) for r in roots)


def targets(module, argv):
    how = WRITES.get((module, argv[0]))
    if how is None:
        return []
    if how == 'store':
        return [argv[1]] if len(argv) > 1 else [None]
    found = [argv[i + 1] for i, x in enumerate(argv[:-1]) if x == '--out']
    return found if len(found) == 1 and argv.count('--out') == 1 else [None]


def call(module, argv, roots=None):
    if module not in ENTRY or not argv or argv[0] not in ENTRY[module][1]:
        raise NotPermitted(f'not an operator-permitted command: {module} {argv[:1]}')
    argv = [str(x) for x in argv]
    for target in targets(module, argv):
        if target is None or roots is None or not inside(target, roots):
            raise NotPermitted(f'{module} {argv[0]} may write only inside the run directories, not {target}')
    return invoke(module, argv)


def first_record(ledger):
    with Path(ledger).open('rb') as handle:
        return json.loads(handle.readline())['record']


def synthetic_campaign(value):
    return (isinstance(value, dict) and value.get('fixture') == 'SYNTHETIC' and value.get('authority') == PREVIEW_AUTHORITY
            and value.get('acquisition_authorized') is False and value.get('budget') == {'analyst_hours': 0, 'source_starts': 0, 'external_bytes': 0})


def preview(artifacts, argv):
    """The only Discovery writes: a SYNTHETIC preview ledger in artifacts/anvil-preview-*, source and candidate records."""
    argv = [str(x) for x in argv]
    shape = (len(argv) == 3 and argv[0] == 'init') or (len(argv) == 4 and argv[0] == 'add' and argv[2] in PREVIEW_KINDS)
    if not shape:
        raise NotPermitted(f'preview admits only init <ledger> <campaign> and add <ledger> source|candidate <record>, not {argv[:3]}')
    ledger, record = Path(argv[1]).absolute(), Path(argv[-1]).absolute()
    folder = ledger.parent
    if ledger.name != 'ledger.jsonl' or not folder.name.startswith('anvil-preview-') or resolved(folder.parent) != resolved(artifacts) \
            or resolved(record.parent) != resolved(folder) or record.suffix != '.json':
        raise NotPermitted('preview ledgers and their records live only in the run artifacts/anvil-preview-* directory')
    if argv[0] == 'init':
        if ledger.exists() or not synthetic_campaign(json.loads(record.read_bytes())):
            raise NotPermitted('preview init needs a new ledger and a SYNTHETIC, unauthorised, zero-budget campaign')
    elif not ledger.is_file() or not synthetic_campaign(first_record(ledger)):
        raise NotPermitted('preview add appends only to an existing SYNTHETIC preview ledger')
    return invoke(DISCOVERY, argv)


def invoke(module, argv):
    out, err, started = io.StringIO(), io.StringIO(), time.perf_counter()
    fault = None
    try:
        with redirect_stdout(out), redirect_stderr(err):
            try:
                code = importlib.import_module(ENTRY[module][0]).main(argv)
            except SystemExit as stop:  # argparse, Discovery refusals
                code = stop.code if isinstance(stop.code, int) else (0 if stop.code is None else 2)
                if isinstance(stop.code, str):
                    err.write(stop.code)
    except BoundaryViolation:
        raise
    except Exception as error:  # a component crash is a software finding, never a research result
        code, fault = None, f'{type(error).__name__}: {error}'
    text = out.getvalue()
    try:
        parsed = json.loads(text) if text.strip() else None
    except ValueError:
        parsed = None
    return {'command': shell(module, argv), 'module': module, 'argv': argv, 'exit_code': 0 if code is None and fault is None else code,
            'fault': fault, 'stdout_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(), 'stdout_chars': len(text),
            'json': parsed, 'text': None if parsed is not None else text[:STDERR_LIMIT],
            'stderr': err.getvalue()[:STDERR_LIMIT], 'elapsed_seconds': round(time.perf_counter() - started, 3)}


def ok(result):
    return result['fault'] is None and result['exit_code'] == 0


def refusal(result):
    """The component's own refusal text: stderr first, then a JSON status/reason/error body."""
    body = result['json'] if isinstance(result['json'], dict) else {}
    return (result['stderr'].strip() or body.get('reason') or body.get('error') or result['fault'] or 'UNKNOWN').strip()
