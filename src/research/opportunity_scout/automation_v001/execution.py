"""Executing-code provenance V001 for pipeline runs (Forge Pilot 001 correction).

The Scout batch ``base_commit`` is a fixed historical constant of the Scout workflow, not the revision that ran; Pilot
001 recorded no executing revision at all. A run now writes ``pipeline-execution.json`` (write-once) right after its
claim and before any process starts, and its receipt binds that file by hash. The record has three parts:

* ``revision``: HEAD read from the git metadata files (``.git``, worktree ``gitdir``/``commondir``, loose ref or
  ``packed-refs``). No git process is launched, so nothing outside the authorised commands runs. Anything unreadable
  or unrecognised is UNKNOWN with a reason, never inferred.
* ``implementation``: the content hash (CRLF normalised to LF) of every repository file in the static ``src.*`` import
  closure of ``automation_v001``, relative imports included, and their combined digest. This identifies the code
  even when HEAD is UNKNOWN or the tree is dirty. It is read after import, so an edit in between is not detected.
* ``worktree_clean``: always UNKNOWN. Establishing it needs the index and object store (``git status``), which this
  record never reads or launches; a CLEAN claim would be unsupported.

Provenance never blocks or alters a run: a failure to compute a part is recorded as UNKNOWN."""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path
import platform
import re

from src.research.spec import digest
from .. import schema as S

VERSION = 'SCOUT_PIPELINE_EXECUTION_PROVENANCE_V001'
ROOTS = ('src/research/opportunity_scout/automation_v001',)
HEX = re.compile(r'[0-9a-f]{40}(?:[0-9a-f]{24})?')
REF = re.compile(r'refs/[A-Za-z0-9._/-]+')
LIMIT = 16 * 1024 * 1024  # packed-refs can be large; metadata beyond this is not read
BASE_MEANING = 'HISTORICAL_SCOUT_BASELINE_CONSTANT_NOT_THE_EXECUTING_REVISION'
CLEAN_REASON = 'NOT_DETERMINED: the index and object store are never read and no git process is launched'


def bounded(path):
    with Path(path).open('rb') as f:data = f.read(LIMIT + 1)
    if len(data) > LIMIT:raise ValueError('git metadata file too large')
    return data.decode('utf-8').strip()


def resolve(gitdir, ref):
    """A ref from the worktree's own directory, then the common directory's loose refs, then ``packed-refs``."""
    common = gitdir
    if (gitdir / 'commondir').is_file():common = (gitdir / bounded(gitdir / 'commondir')).resolve()
    for base in dict.fromkeys((gitdir, common)):
        if (base / ref).is_file():return bounded(base / ref)
    if (common / 'packed-refs').is_file():
        for line in bounded(common / 'packed-refs').splitlines():
            parts = line.split(' ')
            if len(parts) == 2 and parts[1] == ref:return parts[0]
    return None


def revision(root):
    out = {'commit': S.UNKNOWN, 'ref': S.UNKNOWN, 'basis': 'GIT_METADATA_FILES_READ_WITHOUT_A_PROCESS'}
    try:
        dotgit = Path(root) / '.git'
        if dotgit.is_dir():gitdir = dotgit
        elif dotgit.is_file():
            line = bounded(dotgit)
            if not line.startswith('gitdir: '):return {**out, 'reason': 'UNRECOGNISED_GIT_FILE'}
            gitdir = Path(line[len('gitdir: '):])
            gitdir = gitdir if gitdir.is_absolute() else Path(root) / gitdir
        else:return {**out, 'reason': 'NO_GIT_METADATA'}
        head = bounded(gitdir / 'HEAD')
        if HEX.fullmatch(head):return {**out, 'commit': head, 'ref': 'DETACHED'}
        ref = head[len('ref: '):] if head.startswith('ref: ') else ''
        if not REF.fullmatch(ref) or '..' in ref.split('/'):return {**out, 'reason': 'UNRECOGNISED_HEAD'}
        commit = resolve(gitdir, ref)
        if commit is None or not HEX.fullmatch(commit):return {**out, 'ref': ref, 'reason': 'REF_NOT_RESOLVED'}
        return {**out, 'commit': commit, 'ref': ref}
    except (OSError, UnicodeError, ValueError):
        return {**out, 'reason': 'GIT_METADATA_UNREADABLE'}


def imports(rel, source):
    """Absolute module names a file imports anywhere, with relative imports resolved against its package."""
    package = list(Path(rel).parent.parts)
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):yield from (a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = (package[:len(package) - node.level + 1] if node.level else []) + (node.module.split('.') if node.module else [])
            yield '.'.join(base)
            yield from ('.'.join(base + [a.name]) for a in node.names)


def module_files(root, name):
    """The repository files a src.* module name executes: each package __init__ on its path and the module itself."""
    parts, found = name.split('.'), []
    for i in range(1, len(parts) + 1):
        base = Path(root, *parts[:i])
        if (base / '__init__.py').is_file():found.append(base / '__init__.py')
        elif i == len(parts) and base.with_suffix('.py').is_file():found.append(base.with_suffix('.py'))
    return found


def implementation(root):
    root = Path(root)
    todo = sorted(p.relative_to(root).as_posix() for d in ROOTS for p in (root / d).glob('*.py'))
    files = {}
    while todo:
        rel = todo.pop()
        if rel in files:continue
        data = (root / rel).read_bytes()
        files[rel] = hashlib.sha256(data.replace(b'\r\n', b'\n')).hexdigest()
        for name in imports(rel, data.decode('utf-8')):
            if name.split('.')[0] == 'src':todo += [f.relative_to(root).as_posix() for f in module_files(root, name)]
    return {'boundary': 'static src.* import closure of ' + ', '.join(ROOTS), 'normalisation': 'CRLF_TO_LF',
            'files': dict(sorted(files.items())), 'digest': digest(dict(sorted(files.items())))}


def record(root, base_commit, now):
    try:impl = implementation(root)
    except (OSError, UnicodeError, SyntaxError, ValueError) as error:impl = {'digest': S.UNKNOWN, 'reason': type(error).__name__}
    return {'schema': VERSION, 'revision': revision(root), 'worktree_clean': S.UNKNOWN, 'worktree_clean_reason': CLEAN_REASON,
            'implementation': impl, 'runtime': {'python': platform.python_version(), 'implementation': platform.python_implementation()},
            'scout_batch_base_commit': {'value': base_commit, 'meaning': BASE_MEANING}, 'recorded_at': now}
