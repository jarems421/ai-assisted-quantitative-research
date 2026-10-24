"""Offline-only prepare, saved synthetic import, read-only report and demonstration."""
import argparse
import json
import sys
from . import contracts as K, workspace as W


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare'); p.add_argument('input'); p.add_argument('--out', required=True)
    p = sub.add_parser('import-response'); p.add_argument('workspace'); p.add_argument('response')
    p = sub.add_parser('report'); p.add_argument('workspace')
    p = sub.add_parser('schema'); p.add_argument('task', choices=K.TASKS)
    p = sub.add_parser('demo'); p.add_argument('--out', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'prepare':
            result = W.prepare(args.input, args.out)
        elif args.command == 'import-response':
            result = W.import_response(args.workspace, args.response)
        elif args.command == 'report':
            result = W.report(args.workspace)
        elif args.command == 'schema':
            result = {'schema': K.input_schema(args.task), 'authorises': []}
        else:
            from .demo import run
            result = run(args.out)
        print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))
        return 0
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(json.dumps({'status': 'REFUSED', 'error': str(error), 'authorises': []}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
