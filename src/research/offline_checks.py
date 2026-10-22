"""Reviewed additional tests, with fail-closed IO guards before test imports.

Run from the repository root: python -m src.research.offline_checks [--inventory].
This is a guard for reviewed Python tests, not a sandbox for hostile native code.
"""
from __future__ import annotations

import argparse
import ast
from contextlib import contextmanager, ExitStack
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / 'tests/offline_inventory.json'


class ForbiddenOperation(BaseException):
    """Avoid being mistaken for an expected application ValueError/OSError."""


class Guard:
    def __init__(self, root, scratch, readable):
        self.root = Path(root).resolve()
        self.scratch = Path(scratch).resolve()
        self.readable = {Path(p).resolve() for p in readable}
        self.runtime = {Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve()}
        self.active = False
        self.violations = []

    def deny(self, reason):
        self.violations.append(reason)
        raise ForbiddenOperation('Offline CI prohibited: ' + reason)

    def path(self, value, *, write=False):
        if isinstance(value, int):
            return  # Existing descriptors (stdout/stderr and temporary files).
        p = Path(os.fsdecode(value)).resolve()
        if p.is_relative_to(self.scratch):
            return
        if write:
            self.deny('write outside fixture scratch: ' + str(p))
        if any(part.lower() in {'.env', '.aws', '.ssh', '.azure', '.claude',
                               '.claude-research', '.config', '.netrc'}
               or part.lower().startswith(('.env.', '.claude.')) for part in p.parts):
            self.deny('account or credential path: ' + str(p))
        if p == Path(os.devnull).resolve():
            return
        if p in self.readable or (not p.is_relative_to(self.root)
                                 and any(p.is_relative_to(base) for base in self.runtime)):
            return
        self.deny('read outside reviewed tracked files/runtime: ' + str(p))

    def audit(self, event, args):
        if not self.active:
            return
        if event == 'open':
            _, mode, flags = args
            write = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            self.path(args[0], write=write)
        elif event.startswith('socket.') and event in {
            'socket.connect', 'socket.bind', 'socket.getaddrinfo', 'socket.gethostbyname',
            'socket.gethostbyaddr', 'socket.sendto', 'socket.sendmsg'}:
            self.deny(event)
        elif event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.posix_spawnp',
                       'os.exec', 'os.fork', 'os.forkpty', 'pty.spawn'}:
            self.deny(event)
        elif event in {'os.remove', 'os.rmdir', 'os.mkdir', 'os.chmod', 'os.utime', 'os.truncate'}:
            fd_index = {'os.remove': 1, 'os.rmdir': 1, 'os.mkdir': 2,
                        'os.chmod': 2, 'os.utime': 3}.get(event)
            fd = args[fd_index] if fd_index is not None else -1
            self.path(self.relative_fd(args[0], fd), write=True)
        elif event in {'os.rename', 'os.link'}:
            self.path(self.relative_fd(args[0], args[2]), write=True)
            self.path(self.relative_fd(args[1], args[3]), write=True)
        elif event == 'os.symlink':
            self.deny('symlink creation')
        elif event == 'sqlite3.connect' and str(args[0]) != ':memory:':
            self.path(args[0], write=True)

    def relative_fd(self, value, fd):
        if fd is None or fd == -1 or Path(os.fsdecode(value)).is_absolute():
            return value
        # Linux shutil cleanup uses fd-relative unlink/rmdir. Resolve the actual
        # directory, never treat its relative name as relative to the cwd.
        if sys.platform != 'linux':
            self.deny('unreviewed dir_fd platform')
        return Path(os.readlink(f'/proc/self/fd/{fd}')) / os.fsdecode(value)


@contextmanager
def guarded(guard):
    # Audit hooks cannot be removed. Disable this instance on exit; every CLI
    # invocation runs in a fresh interpreter. Mock replacements cannot bypass it.
    sys.addaudithook(guard.audit)
    guard.active = True
    try:
        yield guard
    finally:
        guard.active = False


def inventory(root=ROOT):
    entries = json.loads((root / 'tests/offline_inventory.json').read_text(encoding='utf-8'))
    actual = {p.relative_to(root).as_posix() for p in (root / 'tests').rglob('test_*.py')}
    if actual != set(entries):
        raise ValueError(f'Unreviewed/stale test modules: added={sorted(actual-set(entries))}; '
                         f'removed={sorted(set(entries)-actual)}')
    for name, entry in entries.items():
        if entry['runner'] not in {'public', 'scout', 'process', 'additional', 'excluded', 'guard-tests'}:
            raise ValueError('Unknown runner: ' + name)
        if not entry['reason']:
            raise ValueError('Missing review reason: ' + name)
        tree = ast.parse((root / name).read_text(encoding='utf-8'))
        declared = sorted(f'{c.name}.{m.name}' for c in tree.body if isinstance(c, ast.ClassDef)
                          for m in c.body if isinstance(m, ast.FunctionDef) and m.name.startswith('test_'))
        if declared != entry['declared_tests']:
            raise ValueError('Test methods changed; review inventory: ' + name)
    return entries


def flatten(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from flatten(test)
        else:
            yield test


def load_additional(entries):
    # Some original modules use sibling imports; preserve their existing names.
    sys.path.insert(0, str(ROOT / 'tests'))
    selected, excluded = [], []
    for path, entry in sorted(entries.items()):
        if entry['runner'] != 'additional':
            continue
        module = Path(path).stem
        tests = list(flatten(unittest.defaultTestLoader.loadTestsFromName(module)))
        exclusions = entry.get('exclude', {})
        seen = set()
        for test in tests:
            short = test.id().removeprefix(module + '.')
            matches = [key for key in exclusions if short == key or short.startswith(key + '.')]
            if matches:
                seen.update(matches)
                excluded.append({'id': test.id(), 'reason': exclusions[matches[0]]})
            else:
                selected.append(test)
        if seen != set(exclusions):
            raise ValueError('Stale exclusions: ' + path)
    return unittest.TestSuite(selected), excluded


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory', action='store_true', help='print reviewed module/method inventory without importing tests')
    args = parser.parse_args()
    entries = inventory()
    if args.inventory:
        print(json.dumps(entries, indent=2))
        return
    # Only git ls-files runs before the guard. No test-supplied command or path.
    tracked = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT, capture_output=True, check=True).stdout
    readable = [ROOT / os.fsdecode(p) for p in tracked.split(b'\0') if p
                and not os.fsdecode(p).startswith(('data/raw/', '.research/'))]
    # No credential environment is passed to tests. Fixtures may add fictional values.
    env = {k: os.environ[k] for k in ('PATH', 'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATHEXT',
                                     'LD_LIBRARY_PATH') if k in os.environ}
    sys.dont_write_bytecode = True
    with tempfile.TemporaryDirectory(prefix='research-offline-') as tmp:
        scratch = Path(tmp)
        env.update(HOME=tmp, USERPROFILE=tmp, TMP=tmp, TEMP=tmp, TMPDIR=tmp,
                   MPLCONFIGDIR=str(scratch / 'mpl'), MPLBACKEND='Agg')
        guard = Guard(ROOT, scratch, readable)
        with patch.dict(os.environ, env, clear=True), patch.object(tempfile, 'tempdir', tmp), \
                patch.object(sys, 'pycache_prefix', str(scratch / 'pycache')), guarded(guard), ExitStack() as stack:
            # Pure portfolio/HTML helpers are allowed; real SDK clients are not.
            from nexustrade.client import NexusTradeClient
            stack.enter_context(patch.object(NexusTradeClient, '__init__',
                                side_effect=lambda *a, **kw: guard.deny('NexusTrade client creation')))
            suite, excluded = load_additional(entries)
            planned = suite.countTestCases()
            for row in excluded:
                print(f"EXCLUDED {row['id']}: {row['reason']}", flush=True)
            result = unittest.TextTestRunner(verbosity=2).run(suite)
            summary = {'planned': planned, 'run': result.testsRun, 'failures': len(result.failures),
                       'errors': len(result.errors), 'skipped': len(result.skipped),
                       'excluded': len(excluded), 'forbidden_operations': guard.violations}
            print('OFFLINE_RESULT ' + json.dumps(summary), flush=True)
            if (not result.wasSuccessful() or result.skipped or guard.violations
                    or result.testsRun != planned or not planned):
                raise SystemExit(1)


if __name__ == '__main__':
    run()
