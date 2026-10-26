"""Pure, bounded helpers; values here are internal Python types, not native records."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import ipaddress
import json
import math
import re
from urllib.parse import parse_qsl, urlsplit, urlunsplit

MAX_BYTES = 1024 * 1024
MAX_ITEMS = 4096
TOKEN = re.compile(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}\Z')


class Invalid(ValueError):
    """Only fixed diagnostic codes, never untrusted exception text."""


def need(ok, code):
    if not ok:
        raise Invalid(code)


def text(value, maximum=2048, *, multiline=False):
    need(isinstance(value, str) and 0 < len(value) <= maximum
         and not any((ord(c) < 32 and not (multiline and c in '\n\r\t'))
                     or ord(c) == 127 or 0xD800 <= ord(c) <= 0xDFFF for c in value), 'INVALID_TEXT')
    return value


def token(value):
    need(isinstance(value, str) and TOKEN.fullmatch(value) is not None, 'INVALID_IDENTIFIER')
    return value


def pairs(items):
    result = {}
    for key, value in items:
        need(key not in result, 'DUPLICATE_JSON_KEY')
        result[key] = value
    return result


def number(value):
    result = float(value)
    need(math.isfinite(result), 'NONFINITE_JSON_NUMBER')
    return result


def loads(raw):
    need(isinstance(raw, bytes) and len(raw) <= MAX_BYTES, 'CAPTURE_SIZE')
    try:
        return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_float=number,
                          parse_constant=lambda _: need(False, 'NONFINITE_JSON_NUMBER'))
    except (UnicodeError, json.JSONDecodeError, RecursionError, OverflowError, ValueError) as exc:
        if isinstance(exc, Invalid):
            raise
        raise Invalid('MALFORMED_JSON') from None


def array(value, maximum=MAX_ITEMS):
    need(isinstance(value, list) and len(value) <= maximum, 'INVALID_ARRAY')
    return value


def obj(value):
    need(isinstance(value, dict), 'INVALID_OBJECT')
    return value


def public_url(value):
    """Syntax only; no DNS, existence, publisher, access or authority verification."""
    text(value)
    need(value.isascii() and not any(c.isspace() for c in value) and '\\' not in value, 'INVALID_URL')
    need(not re.search(r'%(?![0-9a-fA-F]{2})|%(?:0[0-9a-fA-F]|1[0-9a-fA-F]|7[fF])', value), 'INVALID_URL')
    try:
        p = urlsplit(value)
        host = p.hostname or ''
        need(p.scheme == 'https' and p.port in (None, 443) and not p.username and not p.password, 'INVALID_URL')
        need(len(host) <= 253 and '.' in host and not host.endswith(('.local', '.localhost', '.internal')),
             'INVALID_URL_HOST')
        need(not host.split('.')[-1].isdigit(), 'INVALID_URL_HOST')
        need(all(re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', s) for s in host.split('.')),
             'INVALID_URL_HOST')
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            raise Invalid('IP_LITERAL_URL')
        sensitive = {'key', 'api_key', 'apikey', 'token', 'access_token', 'signature', 'password', 'secret'}
        need(not any(k.lower() in sensitive for k, _ in parse_qsl(p.query)), 'CREDENTIAL_LIKE_URL')
        return host, urlunsplit(('https', host, p.path or '/', p.query, p.fragment))
    except (ValueError, UnicodeError) as exc:
        if isinstance(exc, Invalid):
            raise
        raise Invalid('INVALID_URL') from None


@dataclass(frozen=True)
class Artifacts:
    """Exact bytes retained in memory. Caller owns private, immutable persistence."""
    input: bytes = field(repr=False)
    output: bytes = field(repr=False)
    events: bytes = field(repr=False)

    @property
    def hashes(self):
        return tuple((key, hashlib.sha256(getattr(self, key)).hexdigest())
                     for key in ('input', 'output', 'events'))
