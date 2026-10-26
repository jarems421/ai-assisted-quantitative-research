"""Source Retrieval V001: check, stops-snapshot, run, status, result, finalise-interrupted, implementation.

run dispatches only under a valid owner scope, a complete attested stop snapshot and a component reservation.
No command searches, crawls, calls a model, retries, resumes or schedules another activity.
"""
import argparse
import json
import sys
from . import contracts as C, retrieve as R, stops as T, store as S


def main(argv=None):
    parser = argparse.ArgumentParser(prog='python -m src.research.source_v1', description=__doc__)
    parser.add_argument('--base', help='records directory (default: the ignored .research/ of this checkout)')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('implementation', help='print the implementation hash an owner scope must bind')
    p = sub.add_parser('check', help='read-only preflight: the refusal run would record, or none'); p.add_argument('request')
    p = sub.add_parser('stops-snapshot', help='reconcile stop records into an additive snapshot')
    p.add_argument('--input', action='append', default=[]); p.add_argument('--from-dir', action='append', default=[])
    p.add_argument('--attestation'); p.add_argument('--previous')
    p = sub.add_parser('run', help='one bounded retrieval attempt'); p.add_argument('request')
    p = sub.add_parser('status', help='read-only verification of one attempt'); p.add_argument('attempt_id')
    p = sub.add_parser('result', help='print a verified result'); p.add_argument('attempt_id')
    p = sub.add_parser('finalise-interrupted', help='record-only UNKNOWN result for an interrupted attempt')
    p.add_argument('attempt_id'); p.add_argument('--no-attempt-running', action='store_true', required=True)
    a = parser.parse_args(argv)
    try:
        if a.command == 'implementation':
            out = {'implementation_sha256': S.implementation(), 'authorises': []}
        elif a.command == 'check':
            out = R.check(a.request, a.base)
        elif a.command == 'stops-snapshot':
            out = T.build(a.input, a.base, attestation=a.attestation, previous=a.previous, from_dirs=a.from_dir)
        elif a.command == 'run':
            out = R.run(a.request, a.base)
        elif a.command == 'status':
            out = R.status(a.base, a.attempt_id)
        elif a.command == 'result':
            state, result, notes = R.verify(a.base, a.attempt_id)
            C.need(result is not None, 'no result: ' + state + '; ' + '; '.join(notes))
            out = result
        else:
            out = R.finalise_interrupted(a.base, a.attempt_id, no_attempt_running=a.no_attempt_running)
    except (ValueError, OSError) as error:
        print(json.dumps({'error': type(error).__name__, 'message': str(error), 'authorises': []}, indent=2))
        return 1
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
