"""Connected synthetic rehearsal and read-only lineage checkpoint verification. Stop at Anvil."""
import argparse
import json

from src.research.campaign_v1 import records as R
from . import lineage as L


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('rehearse'); p.add_argument('--out', required=True)
    p = sub.add_parser('verify'); p.add_argument('checkpoint_directory')
    p = sub.add_parser('seal'); p.add_argument('selection'); p.add_argument('--out', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'rehearse':
            from .rehearsal import rehearse
            value = rehearse(args.out)
        elif args.command == 'verify':
            value = L.verify(args.checkpoint_directory)
        else:
            value = L.seal(R.loads(R.read(args.selection)), args.out)
        print(json.dumps(value, indent=2, allow_nan=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError, StopIteration) as error:
        print(json.dumps({'status': 'REFUSED', 'reason': str(error), 'authorises': []}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
