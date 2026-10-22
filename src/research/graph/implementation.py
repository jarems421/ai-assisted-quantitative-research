"""Exact Graph implementation pinning for prospective pilot packets (Graph Pilot R4 readiness, Phase A).

A prospective packet snapshot binds the implementation that will run every arm query, replay and blinding check:

* ``commit`` - the git HEAD at freeze time, recorded for audit;
* ``tree_digest`` - a digest of every implementation file's content (``files``: path -> sha256), which is what
  verification enforces.

Rules
-----
* **Pinned set.** Every ``*.py`` file under ``src/research/graph/`` and ``src/research/discovery/``, plus
  ``src/research/spec.py``: the code that determines graph outputs, suggestion ids and pilot validation. The
  historical catalogue is pinned separately by the snapshot's catalogue hash. ``src/research/sec_pilot/parsing.py``
  (the demo network guard) cannot change graph outputs and is excluded.
* **Line endings.** File digests normalise CRLF to LF, so the same commit checked out with different ``autocrlf``
  settings verifies identically. Any other byte change is a mismatch.
* **Freezing** requires git metadata and a clean pinned set: no modified, staged, deleted or untracked
  implementation file. A dirty or unversioned implementation cannot be pinned (``PinError``). Uncommitted changes
  outside the pinned set are allowed and reported.
* **Verification** compares the current pinned-set content with ``tree_digest``. Any added, removed or changed file
  refuses. A different HEAD with identical implementation content is a legitimate unrelated change (for example,
  ``main`` advancing with other work) and passes as ``UNRELATED_COMMIT_CHANGE``. Missing git metadata at
  verification time still enforces content (``GIT_UNAVAILABLE_CONTENT_VERIFIED``). Commit identity is never
  inferred.
* **Legacy snapshots** (R2 dry run, R3) carry no pin and are never checked.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PIN_VERSION = 'GRAPH_IMPLEMENTATION_PIN_V001'
PINNED_DIRS = ('src/research/graph', 'src/research/discovery')
PINNED_FILES = ('src/research/spec.py',)
NORMALISATION = 'CRLF_TO_LF'


class PinError(ValueError):
    pass


def pinned_paths(root=ROOT):
    root = Path(root); out = []
    for d in PINNED_DIRS:
        out += [p for p in (root / d).rglob('*.py') if '__pycache__' not in p.parts]
    out += [root / f for f in PINNED_FILES if (root / f).is_file()]
    return sorted({p.relative_to(root).as_posix() for p in out})


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def content(root=ROOT):
    """Current pinned-set content: path -> normalised sha256, and their combined digest."""
    files = {p: file_digest(Path(root) / p) for p in pinned_paths(root)}
    return {'tree_digest': hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(), 'files': files}


def git_state(root=ROOT):
    """HEAD and the dirty pinned paths, or GIT_UNAVAILABLE when git or the repository metadata is missing."""
    def run(*args):
        return subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True, timeout=60)
    try:
        head = run('rev-parse', '--verify', 'HEAD')
        if head.returncode != 0 or not (Path(root) / '.git').exists():return {'status': 'GIT_UNAVAILABLE', 'commit': None, 'dirty': None}
        status = run('status', '--porcelain', '--untracked-files=all', '--', *PINNED_DIRS, *PINNED_FILES)
        if status.returncode != 0:return {'status': 'GIT_UNAVAILABLE', 'commit': None, 'dirty': None}
    except (OSError, subprocess.SubprocessError):
        return {'status': 'GIT_UNAVAILABLE', 'commit': None, 'dirty': None}
    dirty = sorted(line[3:].strip().strip('"') for line in status.stdout.splitlines() if line.strip() and '__pycache__' not in line)
    return {'status': 'DIRTY' if dirty else 'CLEAN', 'commit': head.stdout.strip(), 'dirty': dirty}


def pin(root=ROOT):
    """The implementation pin for a prospective snapshot. Refuses a dirty pinned set or missing git metadata."""
    state = git_state(root)
    if state['status'] == 'GIT_UNAVAILABLE':raise PinError('cannot pin the Graph implementation: git metadata is unavailable; freeze from a git checkout')
    if state['status'] == 'DIRTY':raise PinError(f"cannot pin the Graph implementation: uncommitted changes in {state['dirty']}; commit them first")
    return {'version': PIN_VERSION, 'commit': state['commit'], **content(root), 'normalisation': NORMALISATION,
            'pinned_set': {'dirs': list(PINNED_DIRS), 'files': list(PINNED_FILES), 'glob': '*.py'}}


def verify(pinned, root=ROOT, with_git=True):
    """Refuse unless the current implementation content equals the pin; report how the commit relates to it."""
    if pinned.get('version') != PIN_VERSION:raise PinError(f'unknown implementation pin version {pinned.get("version")}')
    now = content(root)
    if now['tree_digest'] != pinned['tree_digest']:
        old, new = pinned['files'], now['files']
        diff = {'changed': sorted(p for p in set(old) & set(new) if old[p] != new[p]), 'added': sorted(set(new) - set(old)),
                'removed': sorted(set(old) - set(new))}
        raise PinError(f"the Graph implementation differs from the snapshot pin (commit {pinned['commit'][:12]}): {diff}")
    if not with_git:return {'status': 'CONTENT_VERIFIED', 'pinned_commit': pinned['commit']}
    state = git_state(root)
    if state['status'] == 'GIT_UNAVAILABLE':status = 'GIT_UNAVAILABLE_CONTENT_VERIFIED'
    elif state['commit'] == pinned['commit']:status = 'EXACT_COMMIT'
    else:status = 'UNRELATED_COMMIT_CHANGE'
    return {'status': status, 'pinned_commit': pinned['commit'], 'current_commit': state['commit'], 'dirty_pinned_paths': state['dirty'] or []}
