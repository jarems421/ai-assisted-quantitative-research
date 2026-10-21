"""One manual, receipted GET for the Discovery Lab + Graph v1 pilot. Not a crawler.

Reproduces the receipt practice of the SH09 and Measurement Gate M source checks: a reservation is
written before dispatch; exactly one request is made, with no retries, no redirect following and no
authentication; the body is read up to a byte cap and stored privately by SHA-256; a receipt records
URL, UTC start and finish, status, headers, bytes, digest, completeness and any size stop. Before
dispatch it refuses a request that the archive's start or byte ceiling cannot accommodate.

Usage (from a repository checkout):
  python docs/strategy/graph_pilot/fetch_one.py ARCHIVE_DIR URL --purpose TEXT --max-starts N --max-bytes B
      [--cap 4194304] [--sec-identity-env PATH_TO_.env]

For www.sec.gov the declared User-Agent is the locally configured EDGAR_IDENTITY, read from the
given .env file; it is never printed or stored (the receipt records a redacted marker).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

USER_AGENT = 'ResearchOS-GraphPilot/1.0 (manual receipted request)'
SIZE_STOP = 4 * 2 ** 20


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def now():
    return datetime.now(timezone.utc).isoformat()


def sec_identity(path):
    for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
        if line.startswith('EDGAR_IDENTITY='):
            value = line.split('=', 1)[1].strip().strip('"').strip("'")
            if '@' in value and '\n' not in value:
                return value
    raise SystemExit('refused: no usable EDGAR_IDENTITY in the identity file (value never printed)')


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('archive'); p.add_argument('url'); p.add_argument('--purpose', required=True)
    p.add_argument('--max-starts', type=int, required=True); p.add_argument('--max-bytes', type=int, required=True)
    p.add_argument('--cap', type=int, default=SIZE_STOP); p.add_argument('--sec-identity-env')
    a = p.parse_args(argv)
    root = Path(a.archive); receipts = root / 'receipts'; bodies = root / 'bodies'; reservations = root / 'reservations'
    for d in (receipts, bodies, reservations):d.mkdir(parents=True, exist_ok=True)
    if (root / 'final_stop.json').exists():raise SystemExit('refused: final_stop.json exists; no further dispatch')
    done = [json.loads(f.read_text(encoding='utf-8')) for f in sorted(receipts.glob('*.json'))]
    reserved = sorted(reservations.glob('*.json'))
    if len(reserved) != len(done):raise SystemExit('refused: a reservation has no receipt; reconcile before any new request')
    used = sum(r['body_bytes'] for r in done)
    if len(done) >= a.max_starts:raise SystemExit(f'refused: start ceiling {a.max_starts} reached')
    remaining = a.max_bytes - used
    if remaining <= 0:raise SystemExit(f'refused: byte ceiling {a.max_bytes} reached')
    host = urlsplit(a.url).hostname or ''
    if urlsplit(a.url).scheme != 'https':raise SystemExit('refused: https only')
    headers = {'User-Agent': USER_AGENT, 'Accept-Encoding': 'identity'}
    redacted = None
    if host == 'www.sec.gov':
        if not a.sec_identity_env:raise SystemExit('refused: SEC requests declare the configured identity (--sec-identity-env)')
        headers['User-Agent'] = sec_identity(a.sec_identity_env); redacted = 'LOCALLY_IDENTIFIED_SEC_USER_AGENT_REDACTED'
    cap = min(a.cap, remaining)
    index = len(done) + 1
    reservation = {'index': index, 'url': a.url, 'purpose': a.purpose, 'method': 'GET', 'started_at_utc': now(), 'automatic_retries': 0,
                   'authenticated': False, 'redirects_followed': False, 'request_user_agent': redacted or USER_AGENT,
                   'body_cap_bytes': cap, 'size_stop_bytes': a.cap, 'archive_starts_before': len(done), 'archive_bytes_before': used}
    (reservations / f'{index:03d}.json').write_text(json.dumps(reservation, indent=2), encoding='utf-8')
    status, resp_headers, body, error, truncated = None, {}, b'', None, False
    try:
        r = build_opener(NoRedirect(), ProxyHandler({})).open(Request(a.url, headers=headers), timeout=60)
        status, resp_headers = r.status, dict(r.headers.items())
        body = r.read(cap + 1)
    except HTTPError as e:
        status, resp_headers = e.code, dict(e.headers.items()) if e.headers else {}
        body = e.read(cap + 1) if hasattr(e, 'read') else b''
    except (URLError, TimeoutError, OSError) as e:
        error = f'{type(e).__name__}: {e}'
    if len(body) > cap:body, truncated = body[:cap], True
    digest = hashlib.sha256(body).hexdigest()
    (bodies / digest).write_bytes(body)
    stop = None
    if truncated:stop = 'SIZE_STOP_PREFIX_ONLY' if cap == a.cap else 'BYTE_CEILING_PREFIX_ONLY'
    receipt = dict(reservation, finished_at_utc=now(), status=status, transport_error=error,
                   headers={k.lower(): v for k, v in resp_headers.items() if k.lower() in ('content-type', 'content-length', 'date', 'last-modified', 'location')},
                   body_bytes=len(body), body_sha256=digest, body_path=str((bodies / digest).as_posix()), complete=not truncated and error is None,
                   size_stop=stop)
    (receipts / f'{index:03d}.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps({k: receipt[k] for k in ('index', 'url', 'status', 'transport_error', 'body_bytes', 'body_sha256', 'complete', 'size_stop')}, indent=2))
    if error or status is None or status >= 300 or truncated:sys.exit(3)


if __name__ == '__main__':
    main()
