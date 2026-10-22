"""Exact Graph implementation pinning for prospective pilot packets (Graph Pilot R4 readiness, Phase A).

A prospective packet snapshot binds the implementation that will run every arm query, structured search, replay,
blinding, accounting and report:

* ``commit`` - the git HEAD at freeze time, recorded for audit;
* ``tree_digest`` - a digest of every pinned file's content (``files``: path -> sha256), which verification enforces;
* ``runtime`` - the Python version and implementation, and the installed versions of the third-party distributions the
  pinned code imports (plus ``tzdata`` when ``zoneinfo`` is used), which verification also enforces.

Dependency boundary
-------------------
The pinned set is computed, not hand-listed. Roots: every ``*.py`` under ``src/research/graph/`` and
``src/research/discovery/``, ``src/research/spec.py``, and the R4 source-acquisition tool
``docs/strategy/graph_pilot/fetch_one.py``. To the roots is added the static closure of their ``src.*`` imports (including
imports inside functions) and every package ``__init__.py`` on those import paths. This brings in, for example,
``src/research/sec_pilot/parsing.py``, whose ``offline`` guard enforces the network block in graph rehearsals. Standard
library modules are pinned through the Python version; third-party ones through ``runtime.dependencies``. The historical
catalogue and the generic-identifier register are pinned by hash in the snapshot itself.

Rules
-----
* **Line endings.** File digests normalise CRLF to LF; any other byte change is a mismatch.
* **Freezing** requires git metadata and a clean pinned set: no modified, staged, deleted or untracked pinned file
  (``PinError`` otherwise). Uncommitted changes outside the pinned set are allowed.
* **Verification** refuses unless the whole pinned content equals ``tree_digest`` (any changed, added or removed file
  refuses) and the runtime equals ``runtime``. Only then may HEAD differ from the pinned commit: that is reported as
  ``UNRELATED_COMMIT_CHANGE`` together with the actual running commit. Missing git metadata at verification time still
  enforces content and runtime (``GIT_UNAVAILABLE_CONTENT_VERIFIED``); a commit is never inferred.
* **Legacy snapshots** (R2 dry run, R3) carry no pin and are never checked.
"""
from __future__ import annotations

import ast
import copy
import functools
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PIN_VERSION = 'GRAPH_IMPLEMENTATION_PIN_V002'
ROOT_DIRS = ('src/research/graph', 'src/research/discovery')
ROOT_FILES = ('src/research/spec.py', 'docs/strategy/graph_pilot/fetch_one.py')
NORMALISATION = 'CRLF_TO_LF'
BOUNDARY = ('roots: *.py under src/research/graph/ and src/research/discovery/, src/research/spec.py and docs/strategy/graph_pilot/fetch_one.py; '
            'plus the static closure of their src.* imports and the package __init__.py files on those paths')


class PinError(ValueError):
    pass


def roots(root=ROOT):
    root = Path(root); out = []
    for d in ROOT_DIRS:
        out += [p for p in (root / d).rglob('*.py') if '__pycache__' not in p.parts]
    out += [root / f for f in ROOT_FILES if (root / f).is_file()]
    return sorted({p.relative_to(root).as_posix() for p in out})


def imports(path):
    """Module names imported anywhere in a file (top level or inside functions)."""
    tree = ast.parse(Path(path).read_text(encoding='utf-8'))
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):out |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            out.add(node.module); out |= {f'{node.module}.{a.name}' for a in node.names}
    return out


def module_files(root, name):
    """The repository files a src.* module name executes: the module or package, and each parent package __init__."""
    parts, found = name.split('.'), []
    for i in range(1, len(parts) + 1):
        base = Path(root, *parts[:i])
        if (base / '__init__.py').is_file():found.append(base / '__init__.py')
        elif i == len(parts) and base.with_suffix('.py').is_file():found.append(base.with_suffix('.py'))
    return found


def closure(root=ROOT):
    """Pinned paths and the third-party top-level modules they import."""
    root = Path(root); todo, seen, external = list(roots(root)), set(), set()
    while todo:
        rel = todo.pop()
        if rel in seen:continue
        seen.add(rel)
        for name in imports(root / rel):
            top = name.split('.')[0]
            if top == 'src':todo += [f.relative_to(root).as_posix() for f in module_files(root, name)]
            elif top not in sys.stdlib_module_names and top != '__future__':external.add(top)
            elif top == 'zoneinfo':external.add('zoneinfo')
    return sorted(seen), sorted(external)


@functools.lru_cache(maxsize=1)
def distributions():
    """Module -> distribution map, resolved once per process (installed distributions do not change mid-process)."""
    return importlib.metadata.packages_distributions()


def runtime(external):
    """Python and the third-party distributions behind the imported modules (tzdata backs zoneinfo where installed)."""
    by_module = distributions()
    dists = {d for m in external if m != 'zoneinfo' for d in by_module.get(m, [m])}
    if 'zoneinfo' in external:dists.add('tzdata')
    versions = {}
    for d in sorted(dists):
        try:versions[d] = importlib.metadata.version(d)
        except importlib.metadata.PackageNotFoundError:versions[d] = 'NOT_INSTALLED'
    return {'python': platform.python_version(), 'implementation': platform.python_implementation(), 'dependencies': versions}


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes().replace(b'\r\n', b'\n')).hexdigest()


_CONTENT, _GIT = {}, {}


def signature(root, paths):
    """Modification time and size of each file; any edit, addition or removal changes it."""
    out = []
    for rel in sorted(paths):
        f = Path(root) / rel
        st = f.stat() if f.is_file() else None
        out.append((rel, st.st_mtime_ns if st else None, st.st_size if st else None))
    return tuple(out)


def content(root=ROOT):
    """Current pinned-set content: path -> normalised sha256, their combined digest, and the current runtime.

    Memoised per process on the files' modification times and sizes (and the current root file set); a new process always
    recomputes from bytes."""
    key = str(Path(root).resolve())
    cached = _CONTENT.get(key)
    if cached and signature(root, set(roots(root)) | set(cached[1]['files'])) == cached[0]:return copy.deepcopy(cached[1])
    paths, external = closure(root)
    files = {p: file_digest(Path(root) / p) for p in paths}
    value = {'tree_digest': hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(), 'files': files, 'runtime': runtime(external)}
    _CONTENT[key] = (signature(root, set(roots(root)) | set(files)), value)
    return copy.deepcopy(value)


def git_signature(root, paths):
    git_dir = Path(root) / '.git'
    if not git_dir.is_dir():return None  # a worktree's .git file points elsewhere: never cached
    meta = [git_dir / 'HEAD', git_dir / 'index', git_dir / 'logs' / 'HEAD']
    return tuple((str(m), m.stat().st_mtime_ns if m.is_file() else None) for m in meta) + signature(root, paths)


def git_state(root=ROOT, paths=None):
    """HEAD and the dirty pinned paths, or GIT_UNAVAILABLE when git or the repository metadata is missing.

    Memoised on the repository's HEAD, index and reflog file times and the pinned files' signature."""
    paths = paths if paths is not None else closure(root)[0]
    key, sig = str(Path(root).resolve()), git_signature(root, paths)
    if sig is not None and _GIT.get(key, (None,))[0] == sig:return dict(_GIT[key][1])
    state = git_state_uncached(root, paths)
    if sig is not None:_GIT[key] = (sig, state)
    return dict(state)


def git_state_uncached(root, paths):

    def run(*args):
        return subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True, timeout=60)
    try:
        head = run('rev-parse', '--verify', 'HEAD')
        if head.returncode != 0 or not (Path(root) / '.git').exists():return {'status': 'GIT_UNAVAILABLE', 'commit': None, 'dirty': None}
        status = run('status', '--porcelain', '--untracked-files=all', '--', *ROOT_DIRS, *paths)
        if status.returncode != 0:return {'status': 'GIT_UNAVAILABLE', 'commit': None, 'dirty': None}
    except (OSError, subprocess.SubprocessError):
        return {'status': 'GIT_UNAVAILABLE', 'commit': None, 'dirty': None}
    dirty = sorted({line[3:].strip().strip('"') for line in status.stdout.splitlines() if line.strip() and '__pycache__' not in line})
    return {'status': 'DIRTY' if dirty else 'CLEAN', 'commit': head.stdout.strip(), 'dirty': dirty}


def pin(root=ROOT):
    """The implementation pin for a prospective snapshot. Refuses a dirty pinned set or missing git metadata."""
    now = content(root)
    state = git_state(root, list(now['files']))
    if state['status'] == 'GIT_UNAVAILABLE':raise PinError('cannot pin the Graph implementation: git metadata is unavailable; freeze from a git checkout')
    if state['status'] == 'DIRTY':raise PinError(f"cannot pin the Graph implementation: uncommitted changes in {state['dirty']}; commit them first")
    return {'version': PIN_VERSION, 'commit': state['commit'], **now, 'normalisation': NORMALISATION, 'boundary': BOUNDARY}


def verify(pinned, root=ROOT, with_git=True):
    """Refuse unless the current implementation content and runtime equal the pin; report the actual running commit."""
    if pinned.get('version') != PIN_VERSION:raise PinError(f'unknown implementation pin version {pinned.get("version")}')
    now = content(root)
    if now['tree_digest'] != pinned['tree_digest']:
        old, new = pinned['files'], now['files']
        diff = {'changed': sorted(p for p in set(old) & set(new) if old[p] != new[p]), 'added': sorted(set(new) - set(old)),
                'removed': sorted(set(old) - set(new))}
        raise PinError(f"the Graph implementation differs from the snapshot pin (commit {pinned['commit'][:12]}): {diff}")
    if now['runtime'] != pinned['runtime']:
        raise PinError(f"the runtime differs from the snapshot pin: pinned {pinned['runtime']}, running {now['runtime']}")
    if not with_git:return {'status': 'CONTENT_VERIFIED', 'pinned_commit': pinned['commit']}
    state = git_state(root, list(now['files']))
    if state['status'] == 'GIT_UNAVAILABLE':status = 'GIT_UNAVAILABLE_CONTENT_VERIFIED'
    elif state['commit'] == pinned['commit']:status = 'EXACT_COMMIT'
    else:status = 'UNRELATED_COMMIT_CHANGE'
    return {'status': status, 'pinned_commit': pinned['commit'], 'running_commit': state['commit'] or 'UNKNOWN', 'dirty_pinned_paths': state['dirty'] or []}
