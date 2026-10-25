"""Critic reply credential screen V002 (prospective; Forge Pilot 001 correction).

V001 critic adapters reused ``claude_subscription.safe_output``, whose ``Bearer\\s+\\S+`` alternative fires on any word
after "bearer". The frozen economic rubric asks for an "economic bearer", so ordinary critique prose such as "the cost
bearer remains the contractor" was rejected as a credential (Forge Pilot 001, CRQ-952b880443c8b5c3). That record keeps
its V001 fault; this screen applies only to replies reviewed after it, and every review records its version.

The screen returns category labels only, never a matched value. It runs over the raw bytes and over every string
inside them that parses as JSON (whole body or JSON lines), so a JSON-escaped value is screened as decoded text too.

* ``ANTHROPIC_KEY_PREFIX``: ``sk-ant-`` anywhere, any case (unchanged from V001).
* ``OPENAI_STYLE_KEY`` / ``GOOGLE_API_KEY``: the key shapes of the providers this pipeline holds keys for.
* ``CREDENTIAL_JSON_KEY``: a quoted credential field name followed by a colon (V001's set plus id_token, apikey,
  client_secret and x-goog-api-key).
* ``BEARER_TOKEN`` / ``AUTHORIZATION_HEADER``: "bearer" (any case) or an ``Authorization:`` header, then a value in the
  RFC 6750 token alphabet, optionally quoted. The value is a credential unless it is a short ordinary word: it is
  flagged at 20 characters or more whatever its letters, and at 6 or more unless it is a plain word, a hyphenated
  compound or an all-capitals label. Digits are not required, so ``Bearer abcDEFghiJKL`` is flagged. Accepted gap: a
  real token of 6-19 characters that is spelt like an ordinary word is not detected.

Anything these rules do not recognise is not detected; raw bytes stay private and unredacted as before."""
from __future__ import annotations

import json
import re

VERSION = 'SCOUT_CRITIC_CREDENTIAL_SCREEN_V002'
LEGACY = 'CLAUDE_SUBSCRIPTION_SAFE_OUTPUT_V001'  # the screen V001 adapters applied (Forge Pilot 001)
LONG, SHORT = 20, 6
VALUE = r'''["'`]?([A-Za-z0-9._~+/-]+=*)'''  # RFC 6750 b64token, optionally opened by a quote or backtick
WORD = re.compile(r"[A-Za-z][a-z]*(?:[-'][A-Za-z][a-z]*)*|[A-Z]+(?:_[A-Z]+)*")
FIXED = {
    'ANTHROPIC_KEY_PREFIX': re.compile(r'sk-ant-', re.I),
    'OPENAI_STYLE_KEY': re.compile(r'\bsk-(?:proj-|svcacct-|admin-)?[A-Za-z0-9_-]{20,}'),
    'GOOGLE_API_KEY': re.compile(r'\bAIza[0-9A-Za-z_-]{35}(?![0-9A-Za-z_-])'),
    'CREDENTIAL_JSON_KEY': re.compile(r'"(?:access_token|refresh_token|id_token|api_key|apikey|client_secret|authorization|x-goog-api-key)"\s*:', re.I),
}
VALUED = {
    'BEARER_TOKEN': re.compile(r'\bbearer[ \t\r\n]+' + VALUE, re.I),
    'AUTHORIZATION_HEADER': re.compile(r'\b(?:proxy-)?authorization[ \t]*:[ \t]*(?:[A-Za-z][A-Za-z0-9-]*[ \t]+)?' + VALUE, re.I),
}


def secret_shaped(value):
    core = value.rstrip('.')
    return len(core) >= LONG or (len(core) >= SHORT and not WORD.fullmatch(core))


def categories(text):
    found = {name for name, rule in FIXED.items() if rule.search(text)}
    found |= {name for name, rule in VALUED.items() if any(secret_shaped(m.group(1)) for m in rule.finditer(text))}
    return found


def strings(value):
    """Every key and string value, walked iteratively so nesting depth never matters."""
    stack, out = [value], []
    while stack:
        v = stack.pop()
        if isinstance(v, str):out.append(v)
        elif isinstance(v, dict):out += list(v); stack += list(v.values())
        elif isinstance(v, list):stack += v
    return out


def parsed(chunk):
    try:return [json.loads(chunk)]
    except (ValueError, RecursionError):return []


def decoded(text):
    """The strings inside the text when it is one JSON value, else inside each line that is one."""
    values = parsed(text) or [v for line in text.splitlines() for v in parsed(line)]
    return [s for v in values for s in strings(v)]


def screen(*blobs):
    """Sorted category labels found in the raw blobs or their decoded JSON strings; empty means none recognised."""
    found = set()
    for blob in blobs:
        text = blob.decode('utf-8', errors='replace') if isinstance(blob, bytes) else blob
        found |= categories(text)
        for s in decoded(text):found |= categories(s)
    return sorted(found)
