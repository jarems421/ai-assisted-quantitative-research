"""Read-only inspect / verify interface. No human signing or execution command."""
import argparse
import json
from pathlib import Path
from .gate import inspect
from .approval import verify


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    check = sub.add_parser('inspect')
    check.add_argument('packet', type=Path)
    check = sub.add_parser('verify')
    check.add_argument('packet', type=Path)
    check.add_argument('approval', type=Path)
    check.add_argument('signature', type=Path)
    args = parser.parse_args(argv)
    result = inspect(args.packet) if args.command == 'inspect' else verify(args.packet, args.approval, args.signature)
    print(json.dumps(result, indent=2))
    return 0 if result.get('ready') else 2


if __name__ == '__main__':
    raise SystemExit(main())
