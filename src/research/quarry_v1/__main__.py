"""Offline evidence import, status, export and acquisition planning. No acquisition command."""
import argparse
import json
from . import evidence as E, io
from .acquisition import plan


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('import-file')
    p.add_argument('registry'); p.add_argument('supply'); p.add_argument('--file'); p.add_argument('--out', required=True)
    p = sub.add_parser('status'); p.add_argument('package')
    p = sub.add_parser('export')
    p.add_argument('package'); p.add_argument('inspection'); p.add_argument('subject')
    p.add_argument('--extracted-file'); p.add_argument('--out', required=True)
    p = sub.add_parser('validate-export'); p.add_argument('package')
    p = sub.add_parser('plan-acquisition'); p.add_argument('registry'); p.add_argument('scope')
    p = sub.add_parser('demo'); p.add_argument('--out', required=True)
    a = parser.parse_args(argv)
    try:
        if a.command == 'import-file':
            result = E.import_file(a.registry, a.supply, a.file, a.out)
        elif a.command == 'status':
            result = E.status(a.package)
        elif a.command == 'export':
            result = E.export(a.package, a.inspection, a.subject, a.out, extracted_path=a.extracted_file)
        elif a.command == 'validate-export':
            value = E.validate_export(a.package)
            result = {'status': 'VALID_INSPECTION_PACKAGE', 'files': value['manifest']['files'], 'authorises': []}
        elif a.command == 'plan-acquisition':
            result = plan(a.registry, a.scope)
        else:
            from .demo import run
            result = run(a.out)
    except (ValueError, TypeError, KeyError, OSError, StopIteration) as error:
        print(json.dumps({'status': 'BLOCKED', 'fault_type': type(error).__name__, 'reason': str(error), 'authorises': []}))
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
