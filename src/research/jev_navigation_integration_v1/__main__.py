"""Prepare/report provider records and holdout diagnostics. No CLI activation command."""
import argparse
import json
from . import workspace as W, evaluation as V


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    c = sub.add_parser('prepare'); c.add_argument('navigation_workspace'); c.add_argument('--model', required=True)
    c.add_argument('--quarry-export'); c.add_argument('--out', required=True)
    c = sub.add_parser('report'); c.add_argument('workspace')
    c = sub.add_parser('compose-quarry'); c.add_argument('exports', nargs='+'); c.add_argument('--out', required=True)
    c = sub.add_parser('freeze-evaluation'); c.add_argument('workspace'); c.add_argument('registration')
    c = sub.add_parser('compare'); c.add_argument('workspace'); c.add_argument('labels'); c.add_argument('independence_record')
    c = sub.add_parser('demo'); c.add_argument('--out', required=True)
    a = p.parse_args(argv)
    try:
        if a.command == 'prepare':
            result = W.prepare(a.navigation_workspace, a.out, model=a.model, quarry_export=a.quarry_export)
        elif a.command == 'report':
            result = W.report(a.workspace)
        elif a.command == 'compose-quarry':
            from .quarry import compose
            value = compose(a.exports, a.out)
            result = {'input': str(value['input']), 'records': len(value['bundle']['request']['records']), 'authorises': []}
        elif a.command == 'freeze-evaluation':
            result = V.freeze(a.workspace, a.registration)
        elif a.command == 'compare':
            result = V.compare(a.workspace, a.labels, a.independence_record)
        else:
            from .demo import run
            result = run(a.out)
    except (ValueError, TypeError, KeyError, OSError) as error:
        print(json.dumps({'status': 'BLOCKED', 'reason': str(error), 'authorises': []}))
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
