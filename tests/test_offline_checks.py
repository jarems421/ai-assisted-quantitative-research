"""Exercise guards with real denied operations against fictional paths only."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest

from src.research.offline_checks import ForbiddenOperation, Guard, guarded, inventory


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.scratch = self.root / 'scratch'
        self.scratch.mkdir()
        self.fixture = self.root / 'fixture.txt'
        self.fixture.write_text('fixture')
        self.guard = Guard(self.root, self.scratch, [self.fixture])

    def refused(self, action):
        with guarded(self.guard), self.assertRaises(ForbiddenOperation):
            action()
        self.assertTrue(self.guard.violations)

    def test_open_os_open_and_write_guards(self):
        self.refused(lambda: open(self.root / 'private.txt'))
        self.refused(lambda: os.open(self.root / 'private.txt', os.O_RDONLY))
        self.refused(lambda: self.fixture.write_text('changed'))
        self.refused(lambda: self.fixture.unlink())
        self.refused(lambda: self.fixture.rename(self.scratch / 'moved'))
        self.assertEqual(self.fixture.read_text(), 'fixture')

    def test_allowed_fixture_reads_and_scratch_atomic_writes(self):
        with guarded(self.guard):
            self.assertEqual(self.fixture.read_text(), 'fixture')
            a, b = self.scratch / 'a', self.scratch / 'b'
            a.write_text('temporary')
            os.replace(a, b)
            self.assertEqual(b.read_text(), 'temporary')
            b.unlink()
        self.assertEqual(self.guard.violations, [])

    def test_credentials_even_when_accidentally_allowlisted(self):
        account = self.root / '.claude/settings.json'
        self.guard.readable.add(account)
        self.refused(lambda: account.read_bytes())

    def test_native_fd_relative_cleanup_where_supported(self):
        if os.unlink not in os.supports_dir_fd:
            return  # Windows path-based cleanup is exercised above.
        target = self.scratch / 'temporary'
        target.write_text('temporary')
        fd = os.open(self.scratch, os.O_RDONLY)
        try:
            with guarded(self.guard):
                os.unlink('temporary', dir_fd=fd)
        finally:
            os.close(fd)
        self.assertFalse(target.exists())
        fd = os.open(self.root, os.O_RDONLY)
        try:
            self.refused(lambda: os.unlink('fixture.txt', dir_fd=fd))
        finally:
            os.close(fd)

    def test_dns_tcp_loopback_and_udp_denied(self):
        self.refused(lambda: socket.getaddrinfo('example.invalid', 443))
        with socket.socket() as sock:
            self.refused(lambda: sock.connect(('127.0.0.1', 9)))
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            self.refused(lambda: sock.sendto(b'fixture', ('127.0.0.1', 9)))

    def test_shell_and_hosted_process_denied_before_launch(self):
        self.refused(lambda: subprocess.Popen([sys.executable, '-c', 'raise SystemExit(99)']))
        self.refused(lambda: os.system('this-command-must-never-run'))

    def test_swallowed_violation_still_latched(self):
        with guarded(self.guard):
            try:
                socket.getaddrinfo('example.invalid', 443)
            except BaseException:
                pass
        self.assertEqual(self.guard.violations, ['socket.getaddrinfo'])

    def test_inventory_covers_every_module_and_rejects_new_tests(self):
        from src.research.offline_checks import ROOT
        self.assertTrue(inventory(ROOT))
        (self.scratch / 'tests').mkdir()
        (self.scratch / 'tests/offline_inventory.json').write_text('{}')
        (self.scratch / 'tests/test_new.py').write_text('')
        with self.assertRaisesRegex(ValueError, 'Unreviewed'):
            inventory(self.scratch)


if __name__ == '__main__':
    unittest.main()
