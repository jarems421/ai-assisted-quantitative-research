"""Exploratory FORGE runner CLI. ``plan`` and ``status`` start no process. ``run`` makes CLI calls only under a
completed owner authorisation bound to the exact plan: four administrative commands and one model invocation."""
from __future__ import annotations

import argparse
import sys

from .. import schema as S
from ..cli import emit
from . import runner as X


def parser():
    p = argparse.ArgumentParser(prog='python -m src.research.opportunity_scout.exploratory_v001', description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    x = sub.add_parser('plan', help='new archive, one reserved FORGE attempt, plan and authorisation template (no process)')
    x.add_argument('store'); x.add_argument('--title', required=True); x.add_argument('--model', required=True, help='canonical claude-opus-* id')
    x.add_argument('--count', type=int, default=2); x.add_argument('--effort', choices=X.EFFORTS, default='low')
    x.add_argument('--max-output-tokens', type=int, default=16000, help='per-request CLI cap (thinking counts as output)')
    x.add_argument('--timeout', type=int, default=300); x.add_argument('--executable', required=True, help='absolute path of claude.exe')
    x = sub.add_parser('run', help='the one authorised generation; never retried'); x.add_argument('store'); x.add_argument('--authorisation', required=True)
    x = sub.add_parser('status', help='attempt, claim and receipt state (no process)'); x.add_argument('store')
    return p


def main(argv=None):
    a = parser().parse_args(argv)
    try:
        if a.command == 'plan':
            out = X.plan(a.store, title=a.title, model=a.model, count=a.count, effort=a.effort,
                         max_output_tokens_per_request=a.max_output_tokens, timeout_seconds=a.timeout, executable=a.executable)
        elif a.command == 'run':out = X.run(a.store, a.authorisation)
        else:out = X.status(a.store)
        emit(out)
    except (S.ScoutError, ValueError, OSError, KeyError, TypeError) as error:
        print(f'Opportunity Scout exploratory runner: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
