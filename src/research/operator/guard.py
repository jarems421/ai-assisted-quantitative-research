"""Coordinator-level execution boundary, enforced in code rather than by prompts.

While ``offline(...)`` is active, a Python audit hook refuses network sockets, every form of process creation and
writes outside the run's declared directories, and refuses opening account or credential paths. Delegated stages
run in-process, so the same boundary covers them. Audit hooks cannot be removed: one hook is installed per process
and is inert outside the context. This guards reviewed Python code; it is not a sandbox for hostile native code."""
from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import sys
import threading

NETWORK = {'socket.connect', 'socket.bind', 'socket.getaddrinfo', 'socket.gethostbyname', 'socket.gethostbyaddr',
           'socket.sendto', 'socket.sendmsg', 'http.client.connect', 'urllib.Request', 'webbrowser.open'}
PROCESS = {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.posix_spawnp', 'os.exec', 'os.fork', 'os.forkpty',
           'pty.spawn', 'os.startfile', '_winapi.CreateProcess'}
MUTATE = {'os.mkdir', 'os.remove', 'os.rmdir', 'os.rename', 'os.link', 'os.truncate', 'os.chmod', 'os.utime', 'shutil.rmtree'}
CREDENTIAL = {'.env', '.ssh', '.aws', '.azure', '.codex', '.config', '.netrc', '.claude', '.claude-research', 'keys'}
WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND


class BoundaryViolation(BaseException):
    """Never caught as an application ValueError/OSError by delegated code."""


class Boundary:
    def __init__(self):
        self.roots, self.active, self.denials, self.local = (), False, [], threading.local()

    def deny(self, reason):
        self.denials.append(reason)
        raise BoundaryViolation('Research OS operator boundary: ' + reason)

    def writable(self, value):
        p = Path(os.fsdecode(value)).absolute()
        return p == Path(os.devnull).absolute() or any(p.is_relative_to(r) for r in self.roots)

    def check_path(self, value, write):
        if isinstance(value, int):
            return
        parts = [x.lower() for x in Path(os.fsdecode(value)).absolute().parts]
        if any(x in CREDENTIAL or x.startswith(('.env.', '.claude.')) for x in parts):
            self.deny('account or credential path: ' + os.fsdecode(value))
        if write and not self.writable(value):
            self.deny('write outside the run directories: ' + os.fsdecode(value))

    def audit(self, event, args):
        if not self.active or getattr(self.local, 'busy', False):
            return
        self.local.busy = True
        try:
            if event in NETWORK:
                self.deny('network ' + event)
            elif event in PROCESS:
                self.deny('process creation ' + event)
            elif event == 'os.symlink':
                self.deny('symlink creation')
            elif event == 'open':
                path, mode, flags = args
                write = bool(flags & WRITE_FLAGS) if isinstance(flags, int) else any(c in (mode or '') for c in 'wax+')
                self.check_path(path, write)
            elif event in MUTATE:
                for value in args[:2] if event in ('os.rename', 'os.link') else args[:1]:
                    self.check_path(value, True)
        finally:
            self.local.busy = False


BOUNDARY = Boundary()
_installed = False


@contextmanager
def offline(write_roots):
    """Activate the boundary for one coordinator invocation; never nested."""
    global _installed
    if BOUNDARY.active:
        raise RuntimeError('the operator boundary is already active')
    if not _installed:
        sys.addaudithook(BOUNDARY.audit)
        _installed = True
    previous = sys.dont_write_bytecode
    BOUNDARY.roots, BOUNDARY.denials = tuple(Path(r).absolute() for r in write_roots), []
    sys.dont_write_bytecode = True  # lazy imports must not write __pycache__ outside the run directories
    BOUNDARY.active = True
    try:
        yield BOUNDARY
    finally:
        BOUNDARY.active = False
        sys.dont_write_bytecode = previous
