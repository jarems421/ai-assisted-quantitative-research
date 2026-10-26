"""HTTPS GET for one exact URL, connected to an address the caller has already validated and pinned.

No redirects are followed (http.client never follows them), no retries, no proxy, no cookies or ambient
credentials, identity encoding only. It has never contacted a real host: the restricted offline tests inject a
fake transport, and tests/test_source_retrieval_transport_v1.py runs it against a loopback-only TLS server.
"""
from __future__ import annotations

import http.client
import socket
import ssl
from urllib.parse import urlsplit

ROBOTS_AGENT = 'ResearchOS-SourceRetrieval'
USER_AGENT = ROBOTS_AGENT + '/1'


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    """Certificate and SNI use the URL host; the TCP connection goes only to the pinned address."""

    def __init__(self, host, address, timeout, context, port=443):
        super().__init__(host, port, timeout=timeout, context=context)
        self.pinned = address

    def connect(self):
        sock = socket.create_connection((self.pinned, self.port), self.timeout)
        try:
            if sock.getpeername()[0] != self.pinned:
                raise ConnectionError('connected address differs from the pinned address')
            self.sock = self._context.wrap_socket(sock, server_hostname=self.host)
        except BaseException:
            sock.close()
            raise


class Response:
    def __init__(self, connection, response):
        self._connection, self._response = connection, response
        self.status = response.status
        self.headers = [(str(k), str(v)) for k, v in response.getheaders()]

    def read(self, size):
        return self._response.read(size)

    def close(self):
        try:
            self._response.close()
        finally:
            self._connection.close()


class HttpsTransport:
    """port exists only for the loopback transport tests; exact URLs never carry a port, so runs always use 443."""

    def __init__(self, context=None, port=443):
        self.context = context or ssl.create_default_context()
        self.context.minimum_version = ssl.TLSVersion.TLSv1_2
        self.port = port

    def resolve(self, host):
        addresses = []
        for info in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP):
            if info[4][0] not in addresses:
                addresses.append(info[4][0])
        return addresses

    def open(self, url, host, address, timeout):
        p = urlsplit(url)
        connection = PinnedHTTPSConnection(host, address, timeout, self.context, self.port)
        try:
            connection.putrequest('GET', (p.path or '/') + ('?' + p.query if p.query else ''), skip_host=True, skip_accept_encoding=True)
            for name, value in (('Host', host), ('User-Agent', USER_AGENT), ('Accept-Encoding', 'identity'), ('Connection', 'close')):
                connection.putheader(name, value)
            connection.endheaders()
            return Response(connection, connection.getresponse())
        except BaseException:
            connection.close()
            raise
