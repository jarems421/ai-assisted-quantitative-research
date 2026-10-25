"""python -m src.research.opportunity_scout.scan_v001 configure|scan

  configure --owner NAME --from-plan ARCHIVE --prices-valid-until YYYY-MM-DD   one-time local settings (no secrets)
  scan [--count N] [--budget USD]          plan a new scan, check it, ask for confirmation, run once
  scan --archive ARCHIVE                   use an existing unclaimed plan (for example Pilot 002) instead
  scan ... --plan-only                     stop after the checks and the confirmation summary
  scan ... --confirm PLAN_SHA256           non-interactive confirmation of that exact plan (owner-given hash only)
"""
import argparse
import json
import sys

from .. import schema as S
from . import scan as N


def parser():
    p = argparse.ArgumentParser(prog='python -m src.research.opportunity_scout.scan_v001', description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--config', default=str(N.CONFIG)); sub = p.add_subparsers(dest='command', required=True)
    x = sub.add_parser('configure', help='write the one-time local scan configuration from a reviewed plan')
    x.add_argument('--owner', required=True); x.add_argument('--from-plan', required=True); x.add_argument('--prices-valid-until', required=True)
    x.add_argument('--default-count', type=int, default=2); x.add_argument('--default-budget', type=float, default=1.0)
    x.add_argument('--allowed-subscription', action='append', choices=list(N.X.SUBSCRIPTIONS))
    x.add_argument('--pin-account-fingerprint', default='NOT_PINNED'); x.add_argument('--quiet-seconds', type=int, default=20)
    x.add_argument('--replace', action='store_true')
    x = sub.add_parser('scan', help='plan (or load), check, confirm and run one Opportunity Scout scan')
    x.add_argument('--count', type=int); x.add_argument('--budget', type=float, help='Gemini reservation cap in USD')
    x.add_argument('--archive', help='existing unclaimed plan to use instead of planning a new one')
    x.add_argument('--plan-only', action='store_true'); x.add_argument('--confirm'); x.add_argument('--json', action='store_true')
    return p


def render(result):
    s, out = result['summary'], []
    if s:
        g, c = s['generator'], s['critics']
        out += [f"Plan        {s['plan_sha256']}", f"Archive     {s['archive']}  (batch {s['batch']})",
                f"Prompt      {s['prompt']['version']} {s['prompt']['lane']}, {g['cards']} cards, seeds {s['prompt']['seeds']}, memory {s['prompt']['memory']}",
                f"Generator   {g['model']} effort {g['effort']}, CLI {g.get('cli_version', 'UNCHECKED')}, binary {g['binary_sha256'][:12]}, "
                f"account {json.dumps(g.get('account', 'UNCHECKED'))}"]
        for name, r in c.items():
            extra = (f"effort {r['effort']}, identity {r['identity']}, {r.get('cli_version', 'UNCHECKED')}, {r.get('auth', 'login UNCHECKED')}"
                     if 'effort' in r else f"thinking {r['thinking_level']}, output cap {r['max_output_tokens']}, "
                     f"${r['prices']['input_usd_per_million']}/${r['prices']['output_usd_per_million']} per 1M to {r['prices_valid_until']}, "
                     f"key {r['key_variable']} {'present' if r['key_present'] else 'ABSENT'}")
            out.append(f"{name:<11} {r['provider']} {r['model']}: {extra}")
        q, sp = s['requests'], s['spend']
        out += [f"Requests    1 generation process; up to {q['critic_requests_maximum']} critic requests ({q['gemini_requests_maximum']} Gemini), "
                f"{q['attempts_per_request']} attempt each, adversarial {q['adversarial']}",
                f"Spend       Gemini reservation cap USD {sp['gemini_reservation_cap_usd']:.2f}: {sp['note']}",
                f"Disclosure  {s['disclosure']}", f"One shot    {s['one_shot']}"]
    out += [f'WARNING     {w}' for w in result['warnings']] + [f'BLOCKED     {b}' for b in result['blockers']]
    return '\n'.join(out)


def ask(plan_sha256, read=input):
    """Interactive owner confirmation of this exact plan; anything else stops."""
    typed = read('\nBy confirming, you (the configured owner) approve sending this exact plan to the providers above, accept the '
                 'requested-only Codex identity where shown and the one-shot risk, and attest that Gemini prepaid auto-reload is '
                 f'disabled and the balance covers the cap.\nType "RUN {plan_sha256[:12]}" to start it once, or anything else to stop: ').strip()
    return plan_sha256 if typed == f'RUN {plan_sha256[:12]}' else None


def main(argv=None, *, read=input, interactive=None):
    a = parser().parse_args(argv)
    try:
        if a.command == 'configure':
            c = N.configure(a.config, owner=a.owner, from_plan=a.from_plan, prices_valid_until=a.prices_valid_until,
                            default_count=a.default_count, default_spend_cap_usd=a.default_budget,
                            allowed_subscription_types=a.allowed_subscription or ['pro'], account_fingerprint_sha256=a.pin_account_fingerprint,
                            quiet_seconds=a.quiet_seconds, replace=a.replace)
            print(json.dumps(c, indent=2)); return 0
        cfg = N.load_config(a.config)
        if a.archive and (a.count is not None or a.budget is not None):raise S.ScoutError('an existing plan is immutable; --count/--budget apply only to a new plan')
        store = a.archive or N.prepare(cfg, count=a.count, spend_cap_usd=a.budget)
        result = N.check(store, cfg)
        print(json.dumps(result, indent=2) if a.json else render(result))
        if result['blockers']:print('\nNOT STARTED: resolve the blockers above. Nothing was claimed or sent.'); return 2
        plan = result['summary']['plan_sha256']
        if a.plan_only:
            print(f'\nPlan only: nothing started. To run it once after the owner confirms this exact hash:\n'
                  f'  python -m src.research.opportunity_scout.scan_v001 scan --archive "{store}" --confirm {plan}'); return 0
        if a.confirm:confirm, channel = a.confirm.strip(), 'COMMAND_ARGUMENT'
        elif (sys.stdin.isatty() if interactive is None else interactive):confirm, channel = ask(plan, read), 'INTERACTIVE_TERMINAL'
        else:print('\nNOT STARTED: no confirmation. Re-run with --confirm <plan hash> once the owner has confirmed it.'); return 2
        if confirm is None:print('NOT STARTED: not confirmed. Nothing was claimed or sent.'); return 2
        print('\nRunning once. This can take several minutes; do not start or close Claude Code sessions meanwhile.')
        out = N.run(store, cfg, confirm, channel=channel)
        print(json.dumps(out, indent=2))
        print(f'\nStatus: python -m src.research.opportunity_scout.automation_v001 status "{store}"  (never re-run a claimed plan)')
        return 0 if out['outcome'] == 'COMPLETE' and not out['error'] else 3
    except (S.ScoutError, ValueError, OSError, KeyError, TypeError) as error:
        print(f'Opportunity Scout scan: {error}', file=sys.stderr); return 2


if __name__ == '__main__':
    sys.exit(main())
