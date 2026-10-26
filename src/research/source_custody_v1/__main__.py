"""Source custody V001: preflight, import, status. Offline; no network, retrieval, extraction or interpretation."""
import argparse
import json
import sys
from . import custody as X


def main(argv=None):
    parser = argparse.ArgumentParser(prog='python -m src.research.source_custody_v1', description=__doc__)
    parser.add_argument('--base', help='records directory holding source-v1/ (default: the ignored .research/)')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('preflight', help='read-only: is this target receipt custody-eligible?')
    p.add_argument('attempt_id'); p.add_argument('url')
    p = sub.add_parser('import', help='one verified receipt into a new Quarry package')
    p.add_argument('attempt_id'); p.add_argument('url'); p.add_argument('--claims', required=True); p.add_argument('--out', required=True)
    p = sub.add_parser('status', help='read-only custody claim and package state'); p.add_argument('receipt_sha256')
    a = parser.parse_args(argv)
    try:
        if a.command == 'preflight':
            ctx = X.preflight(a.base, a.attempt_id, a.url)
            out = {'eligible': True, 'receipt_sha256': ctx['receipt_sha256'], 'route_id': ctx['route']['id'],
                   'route_version': ctx['route']['version'], 'transfer_coverage': ctx['receipt']['coverage'],
                   'body_sha256': ctx['receipt']['body_sha256'], 'body_bytes': ctx['receipt']['bytes_received'], 'authorises': []}
        elif a.command == 'import':
            out = X.import_receipt(a.base, a.attempt_id, a.url, a.claims, a.out)
        else:
            out = X.status(a.base, a.receipt_sha256)
    except (ValueError, OSError) as error:
        print(json.dumps({'error': type(error).__name__, 'message': str(error), 'authorises': []}, indent=2))
        return 1
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
