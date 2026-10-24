"""Read-only inspect / verify / signing-bytes interface. No human signing or execution command."""
import argparse
import json
from hashlib import sha256
from pathlib import Path
from .gate import inspect
from .approval import signing_bytes, verify


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    check = sub.add_parser('inspect')
    check.add_argument('packet', type=Path)
    check = sub.add_parser('verify')
    check.add_argument('packet', type=Path)
    check.add_argument('approval', type=Path)
    check.add_argument('signature', type=Path)
    check = sub.add_parser('signing-bytes', help='write the exact bytes to sign; never signs or reads keys')
    check.add_argument('approval', type=Path)
    check.add_argument('out', type=Path)
    args = parser.parse_args(argv)
    if args.command == 'signing-bytes':
        try:
            raw = signing_bytes(args.approval)
            with args.out.open('xb') as handle:  # a file, not stdout: shells may re-encode redirected output
                handle.write(raw)
        except (ValueError, KeyError, TypeError, OSError) as error:
            print(json.dumps({'status': 'BLOCKED', 'blocker': str(error)}, indent=2))
            return 2
        print(json.dumps({'written': str(args.out), 'bytes': len(raw), 'sha256': sha256(raw).hexdigest()}, indent=2))
        return 0
    result = inspect(args.packet) if args.command == 'inspect' else verify(args.packet, args.approval, args.signature)
    print(json.dumps(result, indent=2))
    return 0 if result.get('ready') else 2


if __name__ == '__main__':
    raise SystemExit(main())
