"""Item 2.02 availability preflight and offline stop report; no execution path."""
import argparse
import hashlib
import json
from datetime import date, datetime, time, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from src.research.spec import ROOT, digest

DOCS = ROOT / 'docs/acceleration'
RULE = 'First regular NYSE session OPEN strictly AFTER SEC date filed calendar date; never execute on filing date'


def illustrative_open(filed_date, sessions, *, synthetic=False):
    """Calendar-only synthetic probe, never an activated real eligibility view."""
    if synthetic is not True:
        raise ValueError('Synthetic fixture only; real availability remains blocked')
    filed = date.fromisoformat(filed_date)
    days = [date.fromisoformat(d) for d in sessions]
    if not days or days != sorted(set(days)):
        raise ValueError('Ordered unique synthetic calendar required')
    later = next((d for d in days if d > filed), None)
    if later is None:
        raise ValueError('Insufficient calendar coverage')
    return datetime.combine(later, time(9, 30), ZoneInfo('America/New_York')).astimezone(timezone.utc).isoformat()


def availability_gate(contract):
    if contract.get('rule') != RULE:
        raise ValueError('Owner rule changed; no automatic replacement policy')
    semantics = contract.get('source_semantics', {})
    # An owner approval alone cannot establish the source-field chronology.
    supported = (semantics.get('filed_date_no_earlier_than_acceptance_certified') is True
                 and semantics.get('earlier_date_adjustment_documented') is False)
    return {'status': 'AVAILABILITY_SUPPORTED' if supported else 'AVAILABILITY_BLOCKED',
            'policy_activated': False, 'observed_public_available_at_utc': None,
            'owner_approval_replaces_source_evidence': False}


def require_availability(contract):
    result = availability_gate(contract)
    if result['status'] != 'AVAILABILITY_SUPPORTED':
        raise ValueError('AVAILABILITY_BLOCKED: filing date alone is not a safe acceptance/public-date bound')
    return result


def audit():
    from src.research.sec_pilot.acquisition import Archive
    r = json.loads((DOCS / 'exp006_closure_receipt.json').read_bytes())
    c = json.loads((DOCS / 'exp006_availability_contract.json').read_bytes())
    if digest(c) != r['availability_contract_sha256']:
        raise ValueError('Availability contract changed')
    if availability_gate(c)['status'] != r['status']:
        raise ValueError('Disposition changed')
    raw = ROOT / 'data/raw/item202_closure_v001/documentation'
    original = json.loads((raw / 'result.json').read_bytes())
    if len(list((raw / 'reservations').glob('*.json'))) != r['requests']['SEC_source_certification']:
        raise ValueError('Request count changed')
    if len(list((raw / 'receipts').glob('*.json'))) != original['starts']:
        raise ValueError('Unreconciled response ledger')
    for public, private in zip(c['evidence'], original['documents'], strict=True):
        body = Archive(raw).read(private['body'])
        if (hashlib.sha256(body).hexdigest(), len(body), private['url']) != (
                public['source_sha256'], public['bytes'], public['url']):
            raise ValueError('Source evidence changed')
    if (ROOT / 'experiments/EXP006').exists():
        raise ValueError('Blocked experiment must remain absent')
    return {'status': r['status'], 'source_hashes': 'PASS', 'requests': original['starts'],
            'performance_evaluations': 0, 'held_out_confirmation_accesses': 0}


def report(check=False):
    r = json.loads((DOCS / 'exp006_closure_receipt.json').read_bytes())
    c = json.loads((DOCS / 'exp006_availability_contract.json').read_bytes())
    if digest(c) != r['availability_contract_sha256'] or availability_gate(c)['status'] != r['status']:
        raise ValueError('Receipt/contract mismatch')
    validation = DOCS / 'exp006_closure_validation.json'
    v = json.loads(validation.read_bytes()) if validation.exists() else {}
    text = f'''# Item 2.02 freeze closure: availability stop

**AVAILABILITY_BLOCKED. EXP006 was not created or frozen; Development did not run.** As of 2026-10-13, starting from `8e8ad0c7f676d916832bfaae4e0fb1ff17adf492`. The [owner instruction](owner_item202_closure_2026-10-13.md), sections 3 and 24, requires stopping when the filing-date-only availability semantic cannot be supported. This is a scientific timing stop, not economic falsification or a new architecture phase.

The owner approved one Item 2.02 predictive feature, Development 2015-01-01–2020-12-31, unopened historical confirmation 2021-01-01–2026-09-30, a 20-session horizon, 10 bps per side, future doubled-cost/+1-session robustness, a 12-evaluation ceiling, estimated paired net mean at least 0.50 percentage point and a positive two-sided 95% lower endpoint against zero. These approvals are retained in the [closure receipt](exp006_closure_receipt.json). They were not rescinded or tuned; performance authorization remains conditional on a scientifically certified freeze.

## The exact rule and documented exception

Owner-approved conditional rule: **first regular NYSE open strictly after the SEC filing-date calendar date; never execute on that date**. It is modeled conservative eligibility, not observed first-public time. [Availability contract](exp006_availability_contract.json): OWNER_APPROVED_CONDITIONAL; NOT_ACTIVATED; source-semantic gate FAILED.

The SEC's [filing-date adjustment guidance](https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/request-filing-date-adjustment) permits moving the official date back to an earlier attempted transmission while leaving acceptance time unchanged. The [2006 regulatory overview](https://www.sec.gov/info/edgar/regoverview.htm), section B.5 and Common Filing Concerns, already describes Rule 13 adjustments for technical delays and Exchange Act reports. The newer guidance is not assumed to be a contemporaneous Development receipt; the earlier document establishes that this exception mechanism predates Development. Both current response bodies were archived unchanged with hashes, retrieval times and source locators. No observed adjusted 8-K count is claimed.

Consequently, the required universal chronology implication is unsupported: an adjusted official filing date may precede successful acceptance. A next open calculated from that date alone can then precede acceptance. The documentation does not quantify how often this occurs in the proposed census or establish any accession's exact first-public time.

Synthetic counterexample only: filing date Monday 2015-01-05; delayed acceptance Wednesday 2015-01-07 at 16:00 UTC; the date-only rule gives Tuesday 2015-01-06 at 14:30 UTC. The proposed execution would precede acceptance. This illustrates the permitted mechanism; it is not a fabricated real filing. Calendar tests also cover weekends, holidays, DST, strict date exclusion and insufficient coverage. No production eligibility view exists.

No replacement rule, acceptance maximum, extra waiting period or adjusted-filing exclusion was silently adopted. Old v002/v003 approvals, scopes and inactive states remain unchanged. Economic event date, filing date, acceptance, modeled eligibility and retrieval remain distinct; observed public availability is UNKNOWN. A separately reviewed source-chronology remedy would be needed to change this failed contract.

## Scope retained at the upstream stop

| Required output | Disposition |
| --- | --- |
| Full 2015–2020 census; 8-K / 8-K/A / CIK / Item 2.02 / unknown counts | NOT_ACQUIRED; counts unavailable, not zero |
| Existing Q1 2020 prototype | Unchanged: 17,631 8-K; 493 8-K/A; 5,519 filer CIKs; twelve sampled originals, three Item 2.02 declarations; no full-population label count |
| Identity mapped/unresolved/ended classes and terminal resolution | DEFERRED_AVAILABILITY_STOP; counts unknown, no survivor filtering or terminal exclusion |
| Market provider/API, coverage and corporate-action certificate | NOT_TESTED; no provider or price request; previous bounded QA is not promoted |
| Benchmark matching rule/rate | NOT_FROZEN_NOT_MEASURED; industry/size/momentum/calendar concepts retained |
| Inference methods/calibration/power/effective geometry | NOT_RUN; no method selected and no synthetic success claimed |
| Scientific Proof v2 / canonical EXP006 specification / freeze commit | NOT_RUN / ABSENT / NONE; old design-only compilation remains historical |
| Performance trials / historical confirmation accesses | 0 / 0; ceiling remains 12 |

Two new SEC documentation starts, two HTTP 200 responses, zero retries; no new filing source, identity or market requests. One browser discovery call containing two documentation queries is separately recorded; its underlying fetch count is unavailable. Git/push/hosted-CI operations are engineering delivery, not scientific source calls. No purchase or upgrade occurred; account-wide debit remains unknown. Original response bytes and contact-redacted receipts stay ignored. Local import-path/configuration and editing failures occurred before any request reservation, are retained in the setup log, and consumed no source starts or performance trials.

## Reproduction, preservation and stop

Validation: {v.get('local_tests_passed', 'pending')} local tests; {v.get('public_tests_passed', 'pending')} public tests; zero skipped. [Validation receipt](exp006_closure_validation.json). Public regeneration/check reads tracked receipts only; private audit verifies the two archived bodies without requests:

```sh
python -m src.research.item202_closure --check
python -m src.research.item202_closure --audit --check
python -m src.research.public_checks
python -m unittest discover -s tests -v
```

Prior source/controller/Proof/execution code, integration reports/candidate, original archives, dependency pins, frozen experiments, processed metrics and pause state remain unchanged. Public tests use synthetic fixtures with private reads and external network blocked. Unrelated local files remain untouched. EXP004 stays paused; EXP005 abandoned/absent. No EXP006 directory/state/job/trial, post-event return, confirmation opening, Nexus/Aurora, graph, optimizer or paper/live action occurred.

**Stopped under owner sections 3 and 24.** The next substantive decision is whether to commission a separately bounded review of an acceptance/public-availability-aware source chronology contract for this same candidate. Nothing downstream runs automatically, and the already adopted feature/horizon/cost/materiality parameters do not need renewed approval merely because this gate failed.
'''
    p = DOCS / 'exp006_freeze_review.md'
    body = text.encode('utf-8')
    if check:
        if not p.exists() or p.read_bytes() != body:
            raise ValueError('Closure report differs from canonical receipts')
    else:
        p.write_bytes(body)
    return {'status': r['status'], 'EXP006_created': False, 'Development_run': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check', action='store_true')
    p.add_argument('--audit', action='store_true')
    args = p.parse_args()
    if args.audit:
        print(audit())
    print(report(args.check))


if __name__ == '__main__':
    main()
