"""Offline campaign continuity. 'continue' only reconciles existing references; it executes no native work."""
import argparse
import json
from src.research.operator.runs import DEFAULT_BASE
from . import campaign as C, records as R


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', default=str(DEFAULT_BASE))
    sub = p.add_subparsers(dest='command', required=True)
    c = sub.add_parser('create'); c.add_argument('campaign'); c.add_argument('--api-allocation-micro-usd', type=int)
    c = sub.add_parser('add-branch'); c.add_argument('campaign'); c.add_argument('branch'); c.add_argument('--archive', required=True)
    c.add_argument('--idea', required=True); c.add_argument('--version', required=True, type=int); c.add_argument('--card-sha256', required=True)
    c = sub.add_parser('attach'); c.add_argument('campaign'); c.add_argument('branch'); c.add_argument('activity'); c.add_argument('--run', required=True)
    for command in ('reconcile', 'continue', 'status', 'final'):
        c = sub.add_parser(command); c.add_argument('campaign')
        if command in ('reconcile', 'continue'):
            c.add_argument('--branch')
        else:
            c.add_argument('--json', action='store_true')
    a = p.parse_args(argv)
    try:
        obj = C.create(a.base, a.campaign, a.api_allocation_micro_usd) if a.command == 'create' else C.Campaign(R.locate(a.base, a.campaign))
        if a.command == 'add-branch':
            result = {'appended': obj.add_branch(a.branch, a.archive, a.idea, a.version, a.card_sha256)}
        elif a.command == 'attach':
            result = {'appended': obj.attach(a.branch, a.activity, a.run)}
        elif a.command in ('reconcile', 'continue'):
            result = {'activities': obj.reconcile(a.branch), 'native_operations_started': 0}
        else:
            result = obj.status()
        if a.command in ('status', 'final') and not a.json:
            print(C.markdown(result))
        else:
            print(json.dumps(result, indent=2, allow_nan=False))
        return 2 if a.command in ('reconcile', 'continue') and any(
            x.startswith('RECONCILIATION_REQUIRED') for x in result['activities'].values()) else 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps({'status': 'REFUSED', 'reason': str(error), 'authorises': []}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
