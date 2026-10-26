"""Attach already completed source attempts; report Anvil gates. No source run/continue command."""
import argparse
import json

from src.research.campaign_v1 import records as R
from src.research.operator.runs import DEFAULT_BASE
from src.research.operator.guard import offline
from src.research.source_v1 import store as S
from .continuity import Companion


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', default=str(DEFAULT_BASE))
    sub = p.add_subparsers(dest='command', required=True)
    c = sub.add_parser('create'); c.add_argument('campaign')
    c = sub.add_parser('attach-source'); c.add_argument('campaign'); c.add_argument('branch'); c.add_argument('activity')
    c.add_argument('--source-base', required=True); c.add_argument('--attempt', required=True)
    c = sub.add_parser('check-source'); c.add_argument('campaign'); c.add_argument('branch')
    c.add_argument('--source-base', required=True); c.add_argument('--attempt', required=True)
    c = sub.add_parser('checkpoint'); c.add_argument('campaign'); c.add_argument('--out')
    c = sub.add_parser('rehearse'); c.add_argument('--out', required=True)
    a = p.parse_args(argv)
    try:
        if a.command == 'rehearse':
            from .rehearsal import rehearse
            value = rehearse(a.out)
        else:
            obj = Companion(R.locate(a.base, a.campaign))
            if a.command == 'create':
                obj.create(); value = {'created': str(obj.root), 'authorises': []}
            elif a.command == 'attach-source':
                value = {'appended': obj.attach(a.branch, a.activity, a.source_base, a.attempt), 'authorises': []}
            elif a.command == 'check-source':
                value = obj.check_source(a.branch, a.source_base, a.attempt)
            else:
                value = obj.checkpoint()
                if a.out:
                    target = R.path(a.out)
                    R.need(target.parent == obj.root and target.name.startswith('checkpoint-') and target.suffix == '.json',
                           'use a new checkpoint-*.json directly in the companion directory')
                    with offline([obj.root]):
                        S.write_new(target, value)
        print(json.dumps(value, indent=2, allow_nan=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps({'status': 'REFUSED', 'reason': str(error), 'authorises': []}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
