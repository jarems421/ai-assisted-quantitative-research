"""Reconcile completed integration receipts and generate reports offline; no acquisition."""
import argparse,hashlib,json
from pathlib import Path
from src.research.sec_pilot.acquisition import ROOT,Archive
from src.research.spec import digest
from src.research.source_first_v2 import select
from src.research.surfaces.congressional import CongressionalDisclosuresAdapter,TABLES
from src.research.integrations.registry import validate_registry
DOCS=ROOT/'docs/acceleration';RAW=ROOT/'data/raw/integration_v002'

def audit():
    registry=validate_registry(json.loads((ROOT/'docs/architecture/external_integrations.json').read_bytes()))
    comparison=json.loads((DOCS/'phase4a_researchability_v2.json').read_bytes())
    if select(comparison['rows'])['winner']!=comparison['winner']:raise ValueError('Frozen winner changed')
    pin=json.loads((RAW/'comparison/snapshot_pin.json').read_bytes());snapshot=json.loads((RAW/'comparison/snapshot_manifest.json').read_bytes())
    a=CongressionalDisclosuresAdapter(snapshot,RAW/'comparison/snapshot_files',revision=pin['revision'],retrieved_at='2026-10-13T00:00:00Z')
    for table in TABLES:
        for f in a.files(table,2020):a.verify(f)
    sample=json.loads((RAW/'comparison/congress_neutral_sample.json').read_bytes())
    if digest(sample['sample'])!=sample['sample_hash'] or len(sample['sample'])!=12:raise ValueError('Neutral sample changed')
    for group,ceiling in (('comparison',24),('sec_prototype',32)):
        reservations=list((RAW/group).glob('*/reservations/*.json'));receipts=list((RAW/group).glob('*/receipts/*.json'))
        if len(reservations)>ceiling or len(reservations)!=len(receipts):raise ValueError('Unreconciled budget/response ledger')
        for path in receipts:
            r=json.loads(path.read_bytes());Archive(path.parent.parent).read(r['body'])
    prototype=json.loads((RAW/'sec_prototype/source_contract_corrected.json').read_bytes())
    summary=json.loads((DOCS/'phase4a_source_contract_prototype.json').read_bytes())
    if digest(prototype)!=summary['full_private_receipt_sha256']:raise ValueError('Prototype changed')
    design=json.loads((DOCS/'next_experiment_design_candidate.json').read_bytes());compiled=json.loads((RAW/'sec_prototype/design_dry_compile_completed.json').read_bytes())
    if digest(compiled)!=design['proof_dry_compile']['sha256']:raise ValueError('Proof receipt changed')
    for name,h in compiled['code_fingerprints'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=h:raise ValueError('Design code fingerprint changed: '+name)
    return {'comparison_starts':len(list((RAW/'comparison').glob('*/reservations/*.json'))),'prototype_starts':len(list((RAW/'sec_prototype').glob('*/reservations/*.json'))),'all_bodies_and_snapshot_hashes':'PASS','v2_design_only':True}

def report(check=False):
    p=json.loads((DOCS/'phase4a_source_contract_prototype.json').read_bytes());c=json.loads((DOCS/'phase4a_researchability_v2.json').read_bytes());d=json.loads((DOCS/'next_experiment_design_candidate.json').read_bytes())
    vpath=DOCS/'phase4a_integration_validation.json';v=json.loads(vpath.read_bytes()) if vpath.exists() else {};g=p['geometry']
    matrix='| Surface | Access | Denominator | PIT | Depth | Reproducibility | Derived dependencies |\n| --- | --- | --- | --- | --- | --- | ---: |\n'+'\n'.join('| '+r['id']+' | '+' | '.join(r['gates'][k] for k in ('SOURCE_ACCESS','DENOMINATOR','POINT_IN_TIME','HISTORICAL_DEPTH','REPRODUCIBILITY'))+' | '+str(r['derived_dependencies'])+' |' for r in c['rows'])
    comparison=f'''# Researchability v2: SEC versus Congressional Disclosures

**Frozen rule selects SEC.** This is a source-contract continuation, not a fourth family pilot. V001 map/code/outputs remain unchanged.

{matrix}

Both candidates have three PROVEN/PASS and two PARTIAL gates. The first difference is fewer non-primary derived-evidence dependencies: SEC0, Congress1. Identity/frequency/tie-break levels do not decide the result; frequency remains unknown, not a fabricated independent N. [Selection receipt](phase4a_researchability_v2.json) preserves the exact rule hash and comparison-time statuses without upgrading them from later prototype results.

Congress snapshot commit `{c['snapshot']['revision']}`, generated `{c['snapshot']['generatedAt']}`, schema2, was pinned before downloading2020 files. Published byte counts/SHA-256 verified for all three tables:914 filings,18614 trades,18299 event versions. Q1 first-availability neutral frame contains4124 versions; twelve mechanically ordered sample rows map to one House filing. Its original PDF returned200 and matches upstream rawSha256. That proves source-byte linkage only, not every extracted field or first-public instant. Snapshot remains AUDITED_EXTERNAL_DERIVED; no owner contract accepting it as canonical primary evidence was supplied.

Upstream availability is modeled New York filing-date EOD. FirstAvailableAt is event origin; each amended version also needs its own availableAt gate and exclusive supersededAt endpoint. Python adapter enforces both, retains source URLs and unresolved rows, joins source trade printed/resolved tickers separately, and labels upstream conflated ticker as provenance rather than a canonical ticker. Event consolidation filters identified members; filings/trades retain unresolved/non-member records. Repeated contributors/identity overrides and cross-year version coverage require separate audits before real certification. No transaction date substitutes for disclosure time.

Comparison10 starts including ordinary publisher redirects; one direct official House source start (maximum18) is inside the24 ceiling. Exact dispatches, original redirects and signed targets remain private; targets were explicitly hash-reviewed/frozen before following, never silently substituted. No403/429 denial was overridden. Only2020 Parquet shards were downloaded, not the full all-year corpus. Software/license audit GitHub operations are engineering, not these research-source counts. SEC comparison reused independently verified v001 originals with zero new comparison calls. Federal Register/ClinicalTrials v001 dispositions remain conditional/blocked and were not rerun.

The owner-authorized automatic continuation now completed one SEC prototype; see [source contract](phase4a_source_contract_prototype.md). No prices, performance or new experiment.
'''
    prototype=f'''# SEC source-contract prototype v002

**SOURCE_CONTRACT_READY_FOR_DESIGN for the declared Q1 2020 filing-index scope.** It certifies what was enumerated, not every legally required filing, an original contemporaneous index vintage, a tradable equity population or exact public availability.

| Evidence | Result |
| --- | --- |
| Current official Q1 master index |18124 entries:17631 original8-K and4938-K/A |
| Filing identifiers |17660 unique accessions;18124 distinct CIK/accession/path keys; shared-accession cofilers retained |
| Filer/calendar geometry |5519 CIKs,62 filing dates,3 calendar months; not independent N or equity identities |
| Neutral body sample |First4 original source-order entries per month,12 bodies/4 CIKs, all200 |
| Original body states |12 AVAILABLE;18112 UNTESTED; no unsampled source absence manufactured |
| Daily versus quarterly key checks |2020-01-31,2020-02-06,2020-03-05 all reconcile; no broader PAC/deletion certificate |
| Item2.02 semantic test |3 present,9 not declared in complete source header; all12 corroborated by original primary document |
| Timing / identity |Raw acceptance observed; PUBLIC_TIMESTAMP_UNKNOWN; filer CIK, no security/class certificate |
| Requests |16, including quarter index,12 bodies and3 daily indexes; below32 |

The denominator froze before bodies and before Item selection. No issuer/ticker/outcome/current-survivor filter. Shared accession does not imply one legal issuer; master rows have different CIK/path keys. 8-K/A relationships and PAC/removal states remain UNKNOWN unless evidenced. Archive bodies, exact timestamps/hashes, source lines, original filed names and unresolved states remain private; [public receipt](phase4a_source_contract_prototype.json) contains bounded aggregates and sample metadata.

Daily indexes use compact YYYYMMDD while the quarterly index uses ISO dates. An initial derived comparison incorrectly treated those representations as different keys. A corrected version normalizes dates, retains original bytes and the earlier comparison receipt, and records its hash; no false deletion/correction diagnosis follows. The three checks cover only those current index views, not all62 dates or historical deleted originals.

The first fixed mechanism direction, Item2.02, passed source semantics, so Item5.02 and financing alternatives were not selected or compared. Source declarations and primary headings establish disclosure-category presence, not analyst surprise, earnings persistence, numeric forecasts or zero underlying activity. No time policy was activated; v002/v003 remain their original inactive scopes. [Concrete predictive design candidate](next_experiment_design_candidate.md) is separate from registration/freezing/performance.

Q1 alone is not a confirmatory experiment: three monthly sign groups have minimum one-sided p.125 at alpha.05, and the body sample is dominated by four CIKs. Larger declared source-year coverage and dependence/calibration/power work remain prerequisites. 18124 rows never become independent N. No source-only geometry certifies real returns/inference.
'''
    design=f'''# Next predictive design candidate: source-declared Item2.02

**READY_FOR_EXPERIMENT_FREEZE_REVIEW structurally; executable freeze remains BLOCKED.** One pre-performance proposal, no EXP006 registration/freeze and no performance authorization. [Exact versioned candidate](next_experiment_design_candidate.json).

| Contract | Proposal / requirement |
| --- | --- |
| Estimand |PREDICTIVE positive net paired mean; no causal assertion that disclosure caused a return |
| Source population |Declared original8-K filing census with8-K/A/version/cofiler/missingness retained; only Q1 prototype observed |
| Feature |Source-declared Item2.02 confirmed in original primary HTML; issuer/class/day aggregation only after dated identity reconciliation |
| Missingness |Missing/ambiguous documents, identities or matches stay UNKNOWN/UNAVAILABLE, never zero activity |
| Information time |Raw acceptance and observed filing date separate from UNKNOWN public accessibility; new8-K policy must be independently approved |
| Benchmark |Frozen contemporaneous filing/issuer baseline with dated industry/size/momentum matching; SPY descriptive comparator; one formal discovery |
| Execution concept |Next eligible open after approved availability; one proposed20-session horizon, no horizon search; ended class paths must be valued |
| Cost / robustness |Proposed10bps per side, double-cost40bps roundtrip and+1-session delay; not certified liquidity or account fees |
| Development proposal |2015–2020; full source coverage not acquired/certified |
| Historical confirmation proposal |2021-01-01–2026-09-30, workflow-held-out; modern AI may know history, not genuinely forward unseen |
| Inference |Issuer/calendar/industry/common-factor dependence and overlapping horizons; calibrated method, power and effective counts required |
| Trial proposal |12 total: stage candidate/benchmark6, confirmation robustness2, failure reserves4; one feature/horizon/discovery |
| Materiality proposal |Estimated net20-session paired mean>=0.50percentage point and positive two-sided95% lower endpoint againstzero; prospective owner-review choice |

Economic premise: operating-results disclosures may convey gradually incorporated information; a bare event label does not establish positive surprise, direction or alpha. Negative/bidirectional news, anticipation, concurrent filings, matching failures and confounding may defeat the hypothesis. These are falsifiable limitations, not profitability predictions. This source pass classifies only12 original submissions and computes no numeric forecast, market outcome or strategy.

Proof v2 dry compile: **{d['proof_dry_compile']['status']}**. File/source/denominator/feature/trial hashes, source adapter/upstream version, timing status, identity requirements, code and installed environment fingerprints are retained. It explicitly records performance_executed=false, performance_authorized=false, experiment_registered=false and scientifically_certified=false. Compiler has no Store/stage/engine/return loader; historical synthetic Proof v1 is unchanged.

The prototype demonstrates source feasibility, not full proposed-calendar coverage. Three-month pilot geometry cannot establish significance; proposed69 confirmation monthly groups are not an effective-sample certificate. Persistent common factors, unequal-calendar/partial-year support, selection/missingness and overlapping event horizons require frozen synthetic calibration and real-design justification before any inference claim. No method is selected merely for convenience or to repair earlier Phase3 failed methods.

Remaining executable-freeze blockers: wider source-year/version census, new availability/calendar approval, historical equity/class/terminal and matched-baseline certification, population-preserving real execution (Nexus blocked; local engine synthetic only), inference calibration/power, and owner adoption of horizon/cost/materiality/trial proposals. **Owner review of this concrete candidate can precede those bounded certificates; it does not authorize Development execution until gates close.** No further broad architecture phase is proposed.
'''
    integration=f'''# Phase 4A-I: implemented integrations and source-contract continuation

**READY_FOR_EXPERIMENT_FREEZE_REVIEW at structural/design-review level. Actual executable freeze: BLOCKED.** As of2026-10-13. The owner-authorized implementation and one winning source-contract prototype are complete. No market prices, returns, performance, experiment registration or remote Nexus operation occurred.

## Implemented capabilities

Nine upstream repositories were audited at pinned default-branch HEADs, with implementation/test/license file hashes in the [validated registry](../architecture/external_integrations.md). No cloned repo, copied indicator catalog or upstream code was committed. Congressional adapter consumes pinned schema1/2 manifests and verified Parquet using existing PyArrow/DuckDB; events use version-aware half-open as-of semantics, modeled availability labels and distinct printed/resolved tickers. Evidence tiers prevent an audited external snapshot or OpenBB provider result from satisfying PRIMARY_ORIGINAL merely through an official URL.

Temporal primitives are clean-room Python UTC observations, explicit buckets, same-bucket replacement, elapsed expiry, value-ago/ROC/SMA, batch/stream parity, reset/state continuation and bounded-memory rejection. Unlike upstream adaptive thinning, no data are silently discarded to satisfy capacity. Independent vectors were tested; bit-for-bit chrono-ta parity is not claimed and no Rust runtime was added.

Installed Nexus1.42.0 prepare_web_pages is used offline on literal archived bytes as an optional secondary projection. Original hashes, input/output hashes and helper version remain attached; hidden/script removal never certifies absence. There is no client, host-fetch, agent, Lake, Aurora, portfolio/backtest/paper/live route in the wrapper. Upstream1.55.0 was audited, not installed. OpenBB provider/query/result boundaries informed metadata-preserving adapters without the OpenBB runtime; audited current license is Apache2.0. FinRL/FinRL-X is DEFERRED_PHASE5 with no train/test/price/environment runtime imported. Pandas/sklearn are not new direct dependencies.

NumPy2.2.6, already directly used and fingerprinted, is now explicitly pinned in research requirements; installed environment did not change. DuckDB1.3.2, PyArrow20.0.0 and nexustrade1.42.0 remain pinned. Matplotlib3.11.2 remains presentation-only. A new isolated interpreter using existing system site packages imported the integrations and exercised offline projection; this is an import smoke test, not a new independently locked dependency resolution. Dependency licenses remain their own terms; [notices](../architecture/third_party_notices.md) credit audited sources.

## Source evidence and concrete result

[Researchability v2](phase4a_researchability_v2_report.md) mechanically selected SEC at the third lexicographic criterion. Congressional snapshot integrity passed but remains AUDITED_EXTERNAL_DERIVED. No owner acceptance of derived data as canonical primary was inferred. The neutral12-event sample maps to one original House PDF and does not prove broad extraction/member/security/timing correctness. Comparisons used10 starts (including one direct official original) inside24; the automatic SEC continuation used16 inside32. Total26 new scientific request starts, zero retries, no purchase/upgrade; account-wide usage/debit unknown. Engineering Git/blob audit and delivery Git/CI are separately classified. Ordinary publisher-declared redirects were archived and explicitly reviewed, with signed query targets kept private; no denial override or host evasion.

[SEC prototype](phase4a_source_contract_prototype.md):18124 preserved index entries,12 neutral originals, three daily-key checks,12 header/primary semantic agreements. Source contract ready for design within its declared current-index scope. One Item2.02 [predictive candidate](next_experiment_design_candidate.md), no Item/horizon/grid search. Source-only sample/dependence geometry flags Q1 confirmation impossibility rather than treating rows as independent evidence. Design-only Proof v2 passes structurally, retains six scientific blocker categories and never advances Store state.

## Validation, history and stop

Validation: {v.get('local_tests_passed','pending')} local tests, {v.get('public_tests_passed','pending')} public tests, zero skipped. [Validation receipt](phase4a_integration_validation.json). Replay completed evidence offline: `python -m src.research.integration_review --audit --check`. Public report regeneration/check needs only tracked summaries: `python -m src.research.integration_review --check`. No routine reproduction command makes a source request. Public CI uses fake transports and small synthetic manifests; full local Arrow/SDK tests require the existing research environment, not live data.

Source-first v001, procurement/FDA/merger, old Proof/Decimal execution, canonical metrics/results and frozen experiment artifacts remain byte-preserved. The initial compact-date comparison and earlier dry-compile versions remain privately retained, with corrected interpretation/current code fingerprints separately recorded. No old failed calibration or policy was rewritten. EXP004 remains paused; EXP005 abandoned and absent; no EXP006, held-out opening, new market observations, Orbis/Nexus/Aurora, graph, causal lab, optimization or paper/live action.

**Stop for review of the concrete Item2.02 candidate and exact bounded closure of its remaining scientific gates.** This is not another open-ended integration audit. No owner-only Test/paper confirmation is supplied. Owner approval to freeze/run Development must await full source/date/identity/execution/inference/cost certification; structural review readiness alone grants none of those permissions.
'''
    outputs={'phase4a_researchability_v2_report.md':comparison,'phase4a_source_contract_prototype.md':prototype,'next_experiment_design_candidate.md':design,'phase4a_integration_report.md':integration}
    for name,text in outputs.items():
        p=DOCS/name
        if check:
            if not p.exists() or p.read_text(encoding='utf-8')!=text:raise ValueError('Integration report mismatch: '+name)
        else:p.write_text(text,encoding='utf-8',newline='\n')
    return {'overall':'READY_FOR_EXPERIMENT_FREEZE_REVIEW','executable_freeze':'BLOCKED','preferred':'SEC','candidate':'Item2.02','scientific_requests':26}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--audit',action='store_true');a=p.parse_args()
    if a.audit:print(audit())
    print(report(a.check))
