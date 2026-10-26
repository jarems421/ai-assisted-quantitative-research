"""Source Retrieval V001 real HTTPS transport against a loopback-only local TLS server.

A separately scoped target: it opens sockets on 127.0.0.1 only, so it cannot run under the restricted offline
runner. DNS is denied and every client connection is asserted to target loopback. Certificates are fictional,
offline-test-only fixtures (tests/fixtures/source_retrieval_tls/README.md). No external host is contacted.
"""
import socket
import ssl
import struct
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from src.research.source_v1 import contracts as C, retrieve as R, transport as N

TLS = Path(__file__).resolve().parent / 'fixtures' / 'source_retrieval_tls'
HOST = 'documents.example.org'
URL = f'https://{HOST}/orders/1.pdf?part=a'
LOOPBACK = '127.0.0.1'


class Server:
    """One TLS connection: records the request head, then runs a scripted response."""

    def __init__(self, script, cert='server'):
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.context.load_cert_chain(TLS / f'{cert}.pem', TLS / f'{cert}-key.pem')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((LOOPBACK, 0))
        self.sock.listen(1)
        self.sock.settimeout(10)
        self.port, self.script, self.requests, self.errors = self.sock.getsockname()[1], script, [], []
        self.thread = threading.Thread(target=self.serve, daemon=True)
        self.thread.start()

    def serve(self):
        try:
            raw, _ = self.sock.accept()
            try:
                conn = self.context.wrap_socket(raw, server_side=True)
            except (ssl.SSLError, OSError) as error:
                self.errors.append(type(error).__name__)
                raw.close()
                return
            data = b''
            while b'\r\n\r\n' not in data:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data += chunk
            self.requests.append(data)
            self.script(conn)
        except OSError as error:
            self.errors.append(type(error).__name__)
        finally:
            self.sock.close()

    def join(self):
        self.thread.join(10)


def send(*parts, reset=False):
    def script(conn):
        for part in parts:
            conn.sendall(part)
        if reset:  # Abortive close: RST instead of an orderly shutdown.
            conn.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('HH' if sys.platform == 'win32' else 'ii', 1, 0))
        conn.close()
    return script


class Loopback(N.HttpsTransport):
    """The real transport, given a fictional public DNS answer whose connection is redirected to loopback."""

    def resolve(self, host):
        return ['93.184.216.34']

    def open(self, url, host, address, timeout):
        return super().open(url, host, LOOPBACK, timeout)


def loopback_only(address, timeout=None, *args, **kwargs):
    """Stands in for socket.create_connection: loopback only, and without the DNS lookup it would make."""
    assert address[0] == LOOPBACK, 'transport test attempted a non-loopback connection'
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    sock.connect(address)
    return sock


class TransportTests(unittest.TestCase):
    def setUp(self):
        for target, effect in (('socket.getaddrinfo', AssertionError('DNS is denied in transport tests')),
                               ('socket.create_connection', loopback_only)):
            p = patch(target, side_effect=effect)
            p.start()
            self.addCleanup(p.stop)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.attempt = Path(self.tmp.name) / 'attempt'
        self.attempt.mkdir()
        self.trusted = ssl.create_default_context(cafile=str(TLS / 'ca.pem'))
        self.index = 0

    def fetch(self, script, cert='server', context=None, cap=4096):
        server = Server(script, cert)
        self.index += 1
        receipt = R.fetch(Loopback(context or self.trusted, port=server.port), self.attempt, 'T1', self.index, 'TARGET',
                          URL, HOST, cap, 10, lambda: '2026-10-26T12:00:00.000000+00:00', __import__('time').monotonic)
        server.join()
        C.validate(C.RECEIPT_SCHEMA, receipt)
        self.assertEqual(R.classify(receipt), receipt)  # The recorded classification follows from the recorded facts.
        return receipt, server

    def body(self, receipt):
        return (self.attempt / receipt['body_path']).read_bytes() if receipt['body_path'] else b''

    def test_request_framing_and_framed_complete_response(self):
        payload = b'%PDF-1.4 fictional\x00\xff'
        receipt, server = self.fetch(send(b'HTTP/1.1 200 OK\r\nContent-Length: %d\r\nContent-Type: application/pdf\r\n\r\n' % len(payload), payload))
        self.assertEqual((receipt['termination'], receipt['framing'], receipt['coverage']), ('COMPLETE', 'CONTENT_LENGTH', 'COMPLETE'))
        self.assertEqual(self.body(receipt), payload)
        head = server.requests[0].decode('latin-1').split('\r\n')
        self.assertEqual(head[0], 'GET /orders/1.pdf?part=a HTTP/1.1')
        headers = {line.split(':', 1)[0].lower(): line.split(':', 1)[1].strip() for line in head[1:] if ':' in line}
        self.assertEqual(headers, {'host': HOST, 'user-agent': N.USER_AGENT, 'accept-encoding': 'identity', 'connection': 'close'})

    def test_chunked_unframed_and_partial_transfers(self):
        cases = [
            ('chunked', send(b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n5\r\nhello\r\n6\r\n world\r\n0\r\n\r\n'),
             'COMPLETE', 'COMPLETE', b'hello world'),
            ('unframed', send(b'HTTP/1.1 200 OK\r\nConnection: close\r\n\r\nclose-delimited body'), 'UNVERIFIED_LENGTH', 'UNVERIFIED',
             b'close-delimited body'),
            ('short content-length', send(b'HTTP/1.1 200 OK\r\nContent-Length: 100\r\n\r\nonly-some'), 'TRANSPORT_FAILED', 'PREFIX', b'only-some'),
            ('truncated chunks', send(b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n5\r\nhello\r\n10\r\nabc'), 'TRANSPORT_FAILED', None, None),
            ('reset after headers', send(b'HTTP/1.1 200 OK\r\nContent-Length: 50\r\n\r\npart', reset=True), 'TRANSPORT_FAILED', None, None)]
        for name, script, termination, coverage, body in cases:
            with self.subTest(name):
                receipt, _ = self.fetch(script)
                self.assertEqual(receipt['termination'], termination)
                self.assertFalse(receipt['complete'] and termination != 'COMPLETE')
                if coverage:
                    self.assertEqual(receipt['coverage'], coverage)
                if body is not None:
                    self.assertEqual(self.body(receipt), body)

    def test_non_200_success_unexpected_encoding_conflicts_and_redirects(self):
        cases = [
            ('206', b'HTTP/1.1 206 Partial Content\r\nContent-Length: 4\r\nContent-Range: bytes 0-3/10\r\n\r\npart', 'UNEXPECTED_RESPONSE'),
            ('204', b'HTTP/1.1 204 No Content\r\n\r\n', 'UNEXPECTED_RESPONSE'),
            ('gzip', b'HTTP/1.1 200 OK\r\nContent-Encoding: gzip\r\nContent-Length: 4\r\n\r\n\x1f\x8b\x08\x00', 'UNEXPECTED_ENCODING'),
            ('te and length', b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nContent-Length: 5\r\n\r\n5\r\nhello\r\n0\r\n\r\n', 'FRAMING_CONFLICT'),
            ('redirect', b'HTTP/1.1 302 Found\r\nLocation: https://elsewhere.example.net/x\r\nContent-Length: 0\r\n\r\n', 'REDIRECT_REFUSED')]
        for name, response, termination in cases:
            with self.subTest(name):
                receipt, server = self.fetch(send(response))
                self.assertEqual((receipt['termination'], receipt['complete']), (termination, False))
                self.assertNotEqual(receipt['coverage'], 'COMPLETE')
                self.assertEqual(len(server.requests), 1)  # Never followed or retried.

    def test_tls_hostname_and_certificate_are_verified(self):
        receipt, server = self.fetch(send(b'HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n'), cert='wrong-host')
        self.assertEqual((receipt['termination'], receipt['failure'], receipt['http_status']),
                         ('TRANSPORT_FAILED', 'SSLCertVerificationError', None))
        self.assertEqual(server.requests, [])
        untrusted = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        receipt, server = self.fetch(send(b'HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n'), context=untrusted)
        self.assertEqual((receipt['termination'], receipt['failure']), ('TRANSPORT_FAILED', 'SSLCertVerificationError'))
        self.assertEqual(server.requests, [])

    def test_byte_ceiling_stops_a_real_stream(self):
        payload = b'z' * 20000
        receipt, _ = self.fetch(send(b'HTTP/1.1 200 OK\r\nConnection: close\r\n\r\n', payload), cap=4096)
        self.assertEqual((receipt['termination'], receipt['stopped_by'], receipt['bytes_received']), ('SIZE_STOP', 'SIZE', 4096))
        self.assertEqual(self.body(receipt), payload[:4096])
        receipt, _ = self.fetch(send(b'HTTP/1.1 200 OK\r\nContent-Length: 20000\r\n\r\n', payload), cap=4096)
        self.assertEqual((receipt['termination'], receipt['stopped_by'], receipt['body_path']), ('SIZE_STOP', 'DECLARED_SIZE', None))


if __name__ == '__main__':
    unittest.main()
