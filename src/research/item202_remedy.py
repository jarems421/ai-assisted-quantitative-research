"""Offline remedy/source-closure audit and report; no transport or performance."""
import argparse,hashlib,json
from pathlib import Path
from src.research.spec import ROOT,digest
from src.research.item202_availability import calendar_sessions,probe
DOCS=ROOT/'docs/acceleration';RAW=ROOT/'data/raw/item202_remedy_v001'

def audit():
    receipt=json.loads((DOCS/'exp006_remedy_continuation_receipt.json').read_bytes())
    policy=json.loads((DOCS/'exp006_availability_contract_v002.json').read_bytes())
    calendar=json.loads((DOCS/'exp006_calendar_certificate_v002.json').read_bytes())
    clock=json.loads((DOCS/'exp006_bulk_clock_validation.json').read_bytes())
    coverage=json.loads((DOCS/'exp006_source_coverage.json').read_bytes())
    if digest(policy)!=receipt['availability_contract_sha256'] or digest(calendar)!=policy['calendar_sha256'] or digest(coverage)!=receipt['source_coverage_sha256'] or digest(clock)!=receipt['bulk_clock_audit_sha256']:
        raise ValueError('Remedy/continuation contract changed')
    if hashlib.sha256((ROOT/'src/research/item202_availability.py').read_bytes()).hexdigest()!=policy['implementation_sha256']:
        raise ValueError('Policy code changed')
    from src.research.sec_pilot.acquisition import Archive
    total=0
    for group,ceiling in (('chronology_documentation',12),('chronology_headers',48),('calendar',6),('source_closure',72),('bulk_probe',1),('bulk_snapshot',1)):
        reservations=list((RAW/group/'reservations').glob('*.json'));receipts=list((RAW/group/'receipts').glob('*.json'))
        if len(reservations)!=len(receipts) or len(reservations)>ceiling:raise ValueError('Request ledger mismatch')
        total+=len(reservations)
        for p in receipts:
            r=json.loads(p.read_bytes());body=r['body'];target=(RAW/group/body['path']).resolve()
            if not target.is_relative_to((RAW/group).resolve()):raise ValueError('Archive escape')
            h=hashlib.sha256();length=0
            with target.open('rb') as f:
                while chunk:=f.read(1024*1024):h.update(chunk);length+=len(chunk)
            if h.hexdigest()!=body['sha256'] or length!=body['bytes']:raise ValueError('Original body changed')
    if total!=receipt['requests']['all_direct_source_starts']:raise ValueError('Source count changed')
    days=calendar_sessions(calendar)
    chronology=json.loads((DOCS/'exp006_chronology_validation_v002.json').read_bytes())
    for row in chronology['records']:
        observed=probe(row['raw_acceptance'],row['FILED_AS_OF_DATE'],days,evidence_sha256=policy['evidence'][0]['sha256'],contradictory=row['source_chronology_contradictory'])
        if observed['modeled_eligible_open_utc']!=row['modeled_eligible_open_utc'] or observed['status']!=row['status']:raise ValueError('Chronology replay differs')
    from src.research.item202_source import metadata_clock_conformance
    labels=json.loads((RAW/'source_closure/bulk_labels.json').read_bytes())
    if digest(labels['rows'])!=labels['stats']['rows_sha256']:raise ValueError('Bulk derivative changed')
    lookup={(x['CIK'],x['accession']):x for x in labels['rows']}
    headers={(x['CIK'],x['accession']):x for x in chronology['records']}
    matches=0
    for row in clock['records']:
        key=(row['CIK'],row['accession']);meta=lookup[key]['metadata'];header=headers[key]
        if meta['acceptance_representation']!=row['bulk_acceptanceDateTime'] or header['raw_acceptance']!=row['raw_ACCEPTANCE_DATETIME'] or header['source_sha256']!=row['original_header_sha256']:
            raise ValueError('Original/bulk clock linkage differs')
        match=metadata_clock_conformance(row['bulk_acceptanceDateTime'],row['source_UTC_candidates'])=='MATCH_SOURCE_CANDIDATE'
        if match!=row['literal_ISO_matches_retained_source_UTC']:raise ValueError('Clock comparison differs')
        matches+=match
    if matches!=clock['literal_ISO_matches_source_candidates']:raise ValueError('Clock aggregate differs')
    if (ROOT/'experiments/EXP006').exists():raise ValueError('Blocked EXP006 must remain absent')
    return {'availability':policy['status'],'continuation':receipt['status'],'source_starts':total,'original_hashes':'PASS','chronology_replay':48,'performance':0,'confirmation':0}

def report(check=False):
    r=json.loads((DOCS/'exp006_remedy_continuation_receipt.json').read_bytes());s=json.loads((DOCS/'exp006_source_coverage.json').read_bytes());c=json.loads((DOCS/'exp006_bulk_clock_validation.json').read_bytes())
    sensitivity=json.loads((DOCS/'exp006_bulk_bound_sensitivity.json').read_bytes())
    vpath=DOCS/'exp006_remedy_validation.json';v=json.loads(vpath.read_bytes()) if vpath.exists() else {}
    text=f'''# Item 2.02 acceptance remedy and source-closure stop

**Availability v002 passes the scoped raw-header policy audit. Continuation: SCALABLE_ACCEPTANCE_PROVENANCE_BLOCKED. EXP006 remains absent; no freeze or Development.** Starting HEAD `3c867089fffc16710d23f322f18c330fb5da495b`, as of 2026-10-13. [Owner instruction](owner_item202_remedy_2026-10-13.md) required automatic continuation after the remedy; it occurred. This is a concrete source-clock conformance failure, not another planning phase or an unknown-first-public-time stop.

## Acceptance-aware remedy

The [v002 contract](exp006_availability_contract_v002.json) retains seasonal Eastern and literal EST interpretations of original raw ACCEPTANCE-DATETIME. Eligibility is 09:30 New York on the second regular NYSE session strictly after the later of filed date and each candidate civil date; independent opens must agree and follow every candidate. Earlier adjusted filing dates cannot defeat the acceptance anchor. Missing/conflicting/non-invariant/calendar states stay unavailable. Exact public availability remains **UNKNOWN**; this is an owner-approved modeled buffer, not an observed or guaranteed website timestamp.

Archived SEC [2013 PDS specification](https://www.sec.gov/files/info/edgar/pdsdissemspec072213.pdf), sections 1.0/2.1, establishes pre-Development acceptance/dissemination and header-time semantics. Current filing-status guidance corroborates acceptance; the webmaster FAQ supplies no exact website posting time or guaranteed lag. Both timezone candidates remain plausible; timestamp uncertainty is preserved rather than declared solved.

The frozen source-order sample covers 2015–2020, all four quarters, 24 original 8-Ks and 24 amendments: **48 invariant / 0 timing unavailable / 0 acceptance missing**, across 22 CIKs. It includes 12 pre-market, 19 regular and 17 after-market raw-clock observations and eight Fridays. No actual adjusted-date example was independently certified; synthetic earlier-filed, holiday, DST and midnight/non-invariance cases test that policy explicitly. The [calendar certificate](exp006_calendar_certificate_v002.json) reconciles 1,511 opening sessions from official exchange holiday notices and the 2018 mourning closure. Per-class interruptions/execution remain later requirements. [Chronology receipt](exp006_chronology_validation_v002.json).

## Automatic full-source continuation

All 24 current quarterly indexes were acquired or hash-verified cache hits **before Item filtering**. [Source coverage](exp006_source_coverage.json): **{s['source_rows']:,} rows**, **{s['original8K']:,} 8-K**, **{s['amendment8KA']:,} 8-K/A**, **{s['unique_CIKs']:,} CIKs**, **{s['unique_accessions']:,} accessions**. Shared-accession/cofiler rows and all source paths/forms/dates remain retained; no ticker, survivor or price-availability join defined the census.

The official SEC submissions ZIP was downloaded once as **1,568,623,665 unchanged bytes**, SHA-256 `496e3b23b6014cad33783959c313d3fa9fc75e0acaafa155836907499fddef05`. It includes 993,915 members. Scope gates examined only exact census-bound Development records before Items/acceptance/primary-document fields. Current company/ticker fields and outside-stage feature/clock values were not used. The full raw ZIP includes later metadata and remains quarantined; no market outcomes or confirmation study were opened.

Every census key has a current structured metadata label; no CIK member or historical part was missing. One equivalent duplicate metadata row was retained, not treated as another filing. Current metadata declares Item 2.02 on **{s['bulk_original8K_Item202_rows']:,} originals plus {s['bulk_amendment8KA_Item202_rows']:,} amendments**; these are provisional source labels, not certified qualifying events or trades. Complete original-primary semantic validation was not reached. All 48 sample Item sets agree with original headers, but this is not a primary-body precision certificate. Certified full-population event/timing counts remain unavailable.

## The specific failed scaling gate

[Clock validation](exp006_bulk_clock_validation.json) compares the same 48 original SGML timestamps with the official bulk `acceptanceDateTime` values interpreted according to their literal ISO representation. **{c['literal_ISO_matches_source_candidates']}/48 match a retained original-source UTC candidate; {c['literal_ISO_conflicts_source_candidates']}/48 do not.** Sixteen bulk lexical clocks equal the raw wall clock; other records exhibit conversion, and eight have an additional four/five-hour offset relative to seasonal-source UTC. A single documented serialization interpretation does not reproduce the observed originals.

A separate [calendar-only sensitivity](exp006_bulk_bound_sensitivity.json) gives **{sensitivity['different_second_session_opens']}/48 different eligible opens** when the bulk value is taken literally. Thus this sample does not demonstrate 24 failed date bounds, nor that the modeled buffer fails. Its dates happen to agree; that agreement does not recover original raw timestamps or establish the undocumented representation mode for every census record. The stop concerns the source bridge required by the declared raw-acceptance contract.

Sampled accession `0001001250-20-000042` has raw `20200518160143` while bulk says `2020-05-18T20:01:43.000Z`, a normal seasonal conversion. Accession `0000950157-20-000567` has raw `20200504061131` and bulk `2020-05-04T14:11:31.000Z`, four hours beyond its seasonal-source UTC candidate. The receipt retains all examples, including unconverted clocks, with original source hashes. These are source clock observations, not return results. Neither per-CIK offset guessing nor a broadened adapter clock model was adopted to repair this after discovery.

The raw-header model still passes. The failed gate is certifying its **scalable source input**: an ISO string with mixed provenance cannot silently become original raw ACCEPTANCE-DATETIME. The existing official SEC access guide describes Feed/Oldloads as full public submission archives with headers. They remain a potential raw source, not proved inaccessible. The prior instruction requires bulk-first acquisition, prohibits downloading tens of thousands of bodies and cautions against thousands of individual document requests when a bulk surface exists. No validated header-only bulk source was established in these audited routes, and no full-submission corpus or extensive individual-header fallback was run. A separately bounded source/provenance method is needed; this finding does not prove every possible scalable original-header route impossible.

## Disposition, verification and stop

| Remaining requirement | Disposition |
| --- | --- |
| Original-primary classification and complete PAC/version/missingness reconciliation | DEFERRED_SOURCE_CLOCK_STOP; all {s['source_rows']:,} version states unresolved; unavailable-original count unknown |
| Dated equity/class mapping, ended classes and terminal paths | NOT_TESTED; mapped/unresolved/ended/terminal counts unknown |
| Market provider/API/corporate actions | NOT_CERTIFIED; zero market requests |
| Exact benchmark matching / match rate | NOT_FROZEN / NOT_MEASURED |
| Inference methods/calibration/power/effective N | NOT_RUN; zero methods selected/evaluated |
| Scientific Proof / EXP006 spec hash / freeze commit / Development result | NOT_RUN / NONE / NONE / NONE |
| Performance trials / confirmation outcome accesses | 0 / 0; 12-evaluation ceiling unchanged |

Direct starts: **80 SEC + 5 exchange-calendar = 85**, zero retries. SEC comprises remedy documentation/indexes 7, chronology headers 48, remaining quarterly indexes 17, six API schema probes, and bulk HEAD/GET 2. Browser official-documentation discovery/PDS review is separately logged (three tool calls; underlying fetch count unknown), as are Git/push/hosted-CI delivery operations. No purchase or upgrade; account-wide debit unknown. Original and failed setup receipts remain immutable/private; no contacts or vendor payloads are committed.

**Verification: {v.get('local_tests_passed','pending')} local tests, {v.get('public_tests_passed','pending')} public tests, zero skipped.** [Receipt](exp006_remedy_validation.json). Public report regeneration needs only tracked summaries; private audit verifies every source body including the ZIP by streaming its hash:

```sh
python -m src.research.item202_remedy --check
python -m src.research.item202_remedy --audit --check
python -m src.research.public_checks
python -m unittest discover -s tests -v
```

The [failed v001 report](exp006_freeze_review_v001.md), failed contract/receipt and old global policies retain their original bytes and verdicts. Previous candidate/integration/source/experiment artifacts, metrics, pins and pause/state remain unchanged. EXP004 stays paused and EXP005 abandoned/absent. No new hypothesis, architecture phase, Nexus/Aurora, price/return, registration/freeze, held-out outcome, optimizer or paper/live action occurred. Owner-approved feature/dates/horizon/costs/materiality/trials are unchanged.

**Stopped at the specific source-clock provenance gate.** Next owner decision: authorize or decline a separately bounded original-header/provenance repair for this same candidate. The second-session rule needs no renewed approval merely because its scalable source bridge failed. No downstream continuation runs automatically from this result.
'''
    # Preserve the historical report byte-for-byte before updating its current path.
    old=DOCS/'exp006_freeze_review.md';archive=DOCS/'exp006_freeze_review_v001.md'
    if not archive.exists():
        if check:raise ValueError('Historical v001 report archive missing')
        archive.write_bytes(old.read_bytes())
    target=DOCS/'exp006_freeze_review.md';body=text.encode('utf-8')
    if check:
        if target.read_bytes()!=body:raise ValueError('Current freeze review differs from canonical evidence')
    else:target.write_bytes(body)
    return {'availability':r['availability_status'],'continuation':r['status'],'EXP006_created':False,'Development_run':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--audit',action='store_true');a=p.parse_args()
    if a.audit:print(audit())
    print(report(a.check))
if __name__=='__main__':main()
