"""Research OS pipeline CLI. ``plan``, ``status`` and ``report`` never invoke a model or a CLI. ``run`` fails closed
without a completed owner authorisation bound to the exact plan, and is never resumed or re-run."""
from __future__ import annotations

import argparse
import sys

from .. import schema as S
from ..cli import emit
from ..storage import input_json
from . import pipeline as R


def parser():
    p = argparse.ArgumentParser(prog='python -m src.research.opportunity_scout.automation_v001', description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    x = sub.add_parser('plan', help='archive, reserved generation attempt, pipeline plan and authorisation template (no process)')
    x.add_argument('store'); x.add_argument('--title', required=True)
    x.add_argument('--model', required=True, help='canonical claude-opus-* generator id'); x.add_argument('--count', type=int, default=2)
    x.add_argument('--effort', default='low'); x.add_argument('--max-output-tokens', type=int, default=16000)
    x.add_argument('--timeout', type=int, default=300); x.add_argument('--executable', required=True, help='absolute path of claude.exe')
    x.add_argument('--scientific', required=True, help='JSON role file (provider, family, model, ...)')
    x.add_argument('--economic', required=True, help='JSON role file'); x.add_argument('--spend-cap-usd', type=float, required=True)
    x.add_argument('--codex-home', help='CODEX_HOME for a Codex role'); x.add_argument('--critic-timeout', type=int, default=600)
    x = sub.add_parser('run', help='the one authorised run'); x.add_argument('store'); x.add_argument('--authorisation', required=True)
    x = sub.add_parser('status', help='recorded state only'); x.add_argument('store')
    x = sub.add_parser('report', help='render the consolidated report from recorded files'); x.add_argument('store')
    x.add_argument('--json', action='store_true')
    return p


def main(argv=None):
    a = parser().parse_args(argv)
    try:
        if a.command == 'plan':
            out = R.plan(a.store, title=a.title, scientific=input_json(a.scientific), economic=input_json(a.economic),
                         spend_cap_usd=a.spend_cap_usd, codex_home=a.codex_home, critic_timeout_seconds=a.critic_timeout,
                         generator=dict(model=a.model, count=a.count, effort=a.effort, max_output_tokens_per_request=a.max_output_tokens,
                                        timeout_seconds=a.timeout, executable=a.executable))
        elif a.command == 'run':out = R.run(a.store, a.authorisation)
        elif a.command == 'status':out = R.status(a.store)
        else:
            rep = R.build(a.store)
            if not a.json:
                sys.stdout.write(R.markdown(rep)); return 0
            out = rep
        emit(out)
    except (S.ScoutError, ValueError, OSError, KeyError, TypeError) as error:
        print(f'Research OS pipeline: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
