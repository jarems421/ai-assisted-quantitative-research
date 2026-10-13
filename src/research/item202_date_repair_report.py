"""Offline canonical report and private source replay; never acquire or trade."""
import argparse
from collections import Counter
import hashlib
import json

from src.research.item202_date_repair import DOCS, RAW, verify_freeze, load_inputs
from src.research.item202_date_bound import compare, confusion
from src.research.item202_availability import parse_header, calendar_sessions
from src.research.item202_primary_review import inspect
from src.research.sec_pilot.acquisition import Archive
from src.research.spec import ROOT, digest


def data():
    return {name:json.loads((DOCS/filename).read_bytes()) for name,filename in (
        ('timing','exp006_date_validation_v003.json'),('primary','exp006_primary_title_review_v003.json'),
        ('first_primary','exp006_primary_validation_v003.json'),('archive','exp006_archive_feasibility_v003.json'),
        ('population','exp006_population_identity_review_v003.json'))}


def audit():
    manifest,sample,policy=verify_freeze()
    d=data();calendar=json.loads((DOCS/'exp006_calendar_certificate_v002.json').read_bytes())
    sessions=calendar_sessions(calendar)
    evidence=json.loads((DOCS/'exp006_availability_contract_v002.json').read_bytes())['evidence'][0]['sha256']
    for row in d['timing']['records']:
        body=Archive(RAW/'headers').read(row['receipt']['body'])
        header=parse_header(body,cik=row['CIK'],accession=row['accession'],form=row['form'])
        if header != row['original_header']: raise ValueError('Original header replay changed')
        replay=compare(row['bulk_acceptanceDateTime'],row['filed_date'],header['acceptance_raw'],
                       header['FILED_AS_OF_DATE'],sessions,evidence_sha256=evidence,
                       contradictory=header['source_chronology_contradictory'])
        if any(row.get(k)!=v for k,v in replay.items()): raise ValueError('Date dominance replay changed')
    first=d['first_primary'];primary=d['primary']
    if digest(first)!=primary['first_parser_evidence_sha256']: raise ValueError('First-parser receipt changed')
    if hashlib.sha256((ROOT/'src/research/item202_primary_review.py').read_bytes()).hexdigest()!=primary['implementation_sha256']:
        raise ValueError('Versioned title parser changed')
    for row in primary['records']:
        body=Archive(RAW/'primary').read(row['receipt']['body'])
        if inspect(body)!=row['primary_observation']: raise ValueError('Primary source replay changed')
    if any(primary[k]!=v for k,v in confusion(primary['records']).items()): raise ValueError('Confusion aggregate changed')
    groups={'headers':240,'primary':96,'archive_discovery':14,'archive_days':12,
            'archive_feed_discovery':14,'archive_feed_days':12}
    counts={};complete=0;prefixes=0
    for group,ceiling in groups.items():
        base=RAW/group
        starts=list((base/'reservations').glob('*.json'))
        receipts=list((base/'receipts').glob('*.json'));errors=list((base/'errors').glob('*.json'))
        if len(starts)!=len(receipts)+len(errors) or len(starts)>ceiling: raise ValueError('Unreconciled request ledger')
        counts[group]=len(starts)
        for p in receipts+errors:
            r=json.loads(p.read_bytes())
            if r['attempt']!=1: raise ValueError('Unexpected retry')
            record=r.get('body') or r.get('partial_body')
            if record:
                path=(base/record['path']).resolve()
                if not path.is_relative_to(base.resolve()): raise ValueError('Archive path escape')
                h=hashlib.sha256();size=0
                with path.open('rb') as f:
                    while part:=f.read(1024*1024):h.update(part);size+=len(part)
                if h.hexdigest()!=record['sha256'] or size!=record['bytes']: raise ValueError('Source body changed')
            complete+=bool(r.get('body'));prefixes+=bool(r.get('partial_body'))
    if counts['archive_days']+counts['archive_feed_days']>12 or counts['archive_discovery']+counts['archive_feed_discovery']>14:
        raise ValueError('Combined archive ceilings exceeded')
    bindings=json.loads((RAW/'identity_source_keys.json').read_bytes())
    if digest(bindings['source_keys'])!=bindings['sha256'] or bindings['sha256']!=d['population']['identity']['source_key_bindings_sha256']:
        raise ValueError('Source-key identity reconciliation changed')
    source_keys={(r['CIK'],r['accession'],r['form'],r['filing_date']) for r in load_inputs() if r['state']=='PRESENT_METADATA'}
    if {(r['CIK'],r['accession'],r['form'],r['filing_date']) for r in bindings['source_keys']}!=source_keys:
        raise ValueError('Identity source-key population changed')
    if len(bindings['source_keys'])!=d['population']['provisional_Item202_source_keys']:
        raise ValueError('Source-key count changed')
    if (ROOT/'experiments/EXP006').exists() or (ROOT/'experiments/EXP006_SEC_ITEM202_PREDICTIVE').exists():
        raise ValueError('Blocked experiment unexpectedly created')
    return {'status':'PASS','starts':sum(counts.values()),'by_group':counts,'complete_bodies':complete,
            'retained_incomplete_prefixes':prefixes,'header_replay':240,'primary_replay':96,
            'source_key_identity_reconciliation':len(bindings['source_keys']),'confirmation_accesses':0}


def report(check=False):
    manifest,sample,policy=verify_freeze();d=data()
    t,p,a,s=d['timing'],d['primary'],d['archive'],d['population']
    lexical_matches=sum(r['lexical_date']==max(r['raw_candidate_civil_dates']) for r in t['records'])
    literal_matches=sum(r['literal_New_York_date']==max(r['raw_candidate_civil_dates']) for r in t['records'])
    raw_date_agreement=sum(len(set(r['raw_candidate_civil_dates']))==1 for r in t['records'])
    vpath=DOCS/'exp006_date_repair_validation.json'
    validation=json.loads(vpath.read_bytes()) if vpath.exists() else {}
    text=f'''# Item 2.02: conservative date repair and population closure

**SCALABLE_ACCEPTANCE_DATE_BOUND_READY. Sampled Item 2.02 concordance passes. EXP006 freeze remains blocked at HISTORICAL_POPULATION_VERSION_IDENTITY_BLOCKED.** Starting HEAD `{manifest['starting_head']}`, as of 2026-10-13. The owner's expected checkpoint was followed by the README-only `cafb8e9` commit; research inputs were unchanged. [Exact owner instruction](owner_item202_date_repair_2026-10-13.md).

The narrower civil-date requirement was tested and passed; exact raw-clock reconstruction was not attempted or asserted. The [earlier freeze review](exp006_freeze_review.md), mixed-clock failure, calendar sensitivity and v002 policy keep their original bytes. This pass continued automatically into primary classification and population/identity review, then stopped at those remaining scientific gates. No prices or performance were accessed.

## Date provenance

The [frozen v003 transform](exp006_availability_contract_v003.json) takes the maximum of the ISO string's lexical date, its literal offset-aware instant converted to New York civil date, and the census filed date. Eligibility is the second regular NYSE session strictly after that envelope, at 09:30 New York. No CIK/year offsets or learned clock corrections are used. Conservative later execution is accepted by the owner. Exact public availability remains UNKNOWN; timing is modeled and the policy is not activated for a trading population.

The [new sample](exp006_date_validation_sample_v003.json) was pushed in `35f3fba` before its first header request. It excludes the original 48 records. Each of 48 year/quarter/form cells has five accessions: all six Development years, four quarters, originals and amendments. Hash-ordered clock-stress strata use only archived Development source metadata. Representation proxies are sampling labels, not inferred serialization modes.

| Expanded original-header audit | Count |
| --- | ---: |
| New original headers / HTTP 200 | {t['sample_size']} / {t['sample_size']} |
| Envelope earlier than any raw candidate civil date | {t['raw_date_dominance_failures']} |
| Bulk lexical / literal-New-York date exactly matches latest raw civil date | {lexical_matches} / {literal_matches} |
| Both retained raw interpretations have the same civil date | {raw_date_agreement} |
| Same-day / later-day envelope versus latest raw civil date | {t['same_day_envelope']} / {t['later_day_envelope']} |
| Same / later / earlier eligible open | {t['same_eligible_opens']} / {t['later_eligible_opens']} / {t['earlier_eligible_opens']} |
| Delay: 0 / 1 / 2+ sessions | {t['delay_distribution'].get('0',0)} / {t['delay_distribution'].get('1',0)} / 0 |
| Raw-v002 candidate-open non-invariance in sample | {t['prior_v002_non_invariant_count']} |

[Canonical validation](exp006_date_validation_v003.json) retains each source hash, candidate date and open, and the full cell/stress distributions: 40 records per year, 60 per quarter and 120 per form. It covers near lexical UTC midnight (57), near New York midnight (48), Friday (99), DST-window (38) and pre/regular/after-market **bulk-clock** strata (64/66/110). These overlapping strata are not raw-market-hour observations. Observed literal-bulk minus seasonal-source offsets include -5, -4, 0, +4 and +5 hours (39/49/55/76/21). The sample directly exercises the prior representation discrepancies without reconstructing unsampled raw seconds.

This is an expanded mechanical source audit, not proof that every unsampled metadata value is error-free. Full-population missing/conflicting/out-of-scope inputs remain unavailable. The passed bound permits subsequent source closure; it does not certify class-specific calendars, identity, execution or returns.

## Official archive feasibility

Both separately predeclared official channels were reached through their root, year and quarter JSON indexes (six HTTP 200 responses). The first frozen day, 2015-01-06, requested the evidenced Oldloads `.gz` and Feed `.nc.tar.gz` links. Each transfer crossed the declared 256 MiB ceiling and stopped; neither was retried. Twelve fixed days remain in [the archive frame](exp006_archive_feasibility_v003.json), with eleven unvisited days retained explicitly.

Oldloads retains a 269,484,032-byte prefix: its initial reader checked after a 1 MiB chunk and overshot the ceiling by that chunk. The corrected Feed reader retains 268,435,457 bytes (ceiling plus one detection byte). Original prefixes, errors and persisted stops are immutable. The inherited transport-error schema did not retain response status/headers, so those statuses remain UNKNOWN. Whole-file sizes/hashes, uncompressed totals, accession extraction and exact raw-header reconciliation were not certified. Successful directory access is not full archive scalability; bounded transfer failure does not prove the archives inaccessible. Synthetic gzip/tar tests verify extraction logic separately.

No enormous raw-header fallback was launched: the date envelope passed. Six-year PAC/deletion exhaustiveness is still unresolved; these partial day files cannot establish it.

## Primary classification and historical population

The 96-record source-only primary sample froze in `4c48a83` before body requests, with two records per year/quarter/form cell. Positive/negative balance was attempted where the fixed timing sample supplied both; actual labels are 27 positive and 69 negative. No missing stratum was replaced by an outcome-selected issuer.

The first title parser returned TP22, TN69, FP0, FN0, UNKNOWN5. [Its original receipt](exp006_primary_validation_v003.json) is preserved. Source locators show a Disclosure-of prefix, singular Operation or Unicode dash in those five headings. A separately versioned general rule was applied to all 96 cached originals, with no accession-specific override or further download. [Reviewed concordance](exp006_primary_title_review_v003.json): **TP{p['TP']}, TN{p['TN']}, FP{p['FP']}, FN{p['FN']}, UNKNOWN{p['UNKNOWN']}; coverage {p['coverage']:.0%}.** Header, bulk declaration and primary title agree. This source-informed parser review is not an independent classifier holdout.

| Source population / certification boundary | Result |
| --- | --- |
| Current quarterly census | {s['source_rows']:,} rows: {s['original8K']:,} originals / {s['amendment8KA']:,} amendments |
| CIKs / unique accessions | {s['unique_CIKs']:,} / {s['unique_accessions']:,} |
| Provisional Item 2.02 labels | {s['provisional_Item202_original_rows']:,} original rows / {s['provisional_Item202_amendment_rows']:,} amendment rows |
| Candidate source keys / unique accessions / CIKs | {s['provisional_Item202_source_keys']:,} / {s['provisional_Item202_unique_accessions']:,} / {s['provisional_Item202_CIKs']:,} |
| Full-population certified Item 2.02 count | UNKNOWN; 96-source concordance is a sample certificate |
| Full-population classification/version states unresolved | {s['unknown_full_population_classification_rows']:,} |
| Dated class/provider-bound source keys | 0 certified / {s['identity']['unresolved_source_keys']:,} unresolved |
| Renamed / ended classes; complete terminal paths | Counts UNKNOWN; no complete terminal certificate |

[Population review](exp006_population_identity_review_v003.json) keeps current-index keys, amendments, shared accessions and cofilers. Candidate shared-accession excess is {s['shared_accession_extra_candidate_source_rows']:,} rows; they cannot become independent trades by deduplication on CIK or accession alone. SEC's [PAC documentation](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data) explains why rebuilt quarterly/full indexes do not prove the original daily/feed/oldload vintage. Historical deleted keys, unavailable-original counts and amendment-parent links remain unproved, never zero by assumption.

The minimum source-key binding table retains all {s['identity']['unresolved_source_keys']:,} provisional records with nullable class, security ID, venue, effective spans and provider ID. Prior identity receipts have 60 cases and zero complete spans; 57 candidate CIKs overlap that point-evidence frame. No point or current ticker was promoted into a historical span, and no row was dropped. Filer CIK is not a security class. This prevents a certified non-hindsight equity/event/control population and population-preserving valuation, including ended histories. That is the specific closure blocker after the timing and sampled classification passes.

## Stop, verification and reproduction

Market provider/API certification, exact matching, real execution, inference candidates/calibration and synthetic power were not run after the upstream population/identity stop. No spec hash, freeze commit, Development event/pair count, effect, interval or p-value exists. EXP006 remains absent; performance evaluations and confirmation accesses are **0**, with the 12-evaluation ceiling unchanged. EXP004 stays paused; EXP005 stays abandoned/absent. No Nexus, Aurora, purchases, optimizer, paper/live or new phase occurred.

New direct starts: **344 SEC** (240 headers, 96 primary documents, six archive directory probes, two incomplete archive GETs); zero retries, zero market/provider requests. One official-guide browser review is separate; its underlying fetch count is unknown. Git/GitHub delivery checks are also separate. No purchase/upgrade; account-wide debit is unknown. Identity loads locally without exposing its value. The inherited collector's generic User-Agent receipt label is inaccurate for these SEC calls: the wrapper actually supplies the locally configured identified SEC User-Agent. A separate redaction/provenance annotation records this without changing old receipts or publishing contacts.

**Validation:** {validation.get('local_tests_passed','pending')} local tests; {validation.get('public_tests_passed','pending')} public tests; zero skipped. [Validation receipt](exp006_date_repair_validation.json). Earlier reports, contracts, frozen experiment artifacts, source bodies, processed baselines and dependency pins are hash-checked. No historical report is regenerated or rewritten by this pass.

```sh
python -m src.research.item202_date_repair_report --check
python -m src.research.item202_date_repair_report --audit --check
python -m src.research.public_checks
python -m unittest discover -s tests -v
python -m src.presentation.exp001 --check
```

Report regeneration uses tracked summaries only; private audit needs ignored originals and source-key bindings and makes no network request. Remote acquisition commands require explicit `--execute`; completed receipts and persisted stops prevent blind retry. The earlier raw-clock failure remains historically true; the new date-bound certificate is distinct. **Stopped at historical population/version and class-identity certification, before freeze or performance.** Commit SHAs and hosted CI are recorded in the delivery message, without embedding a self-referential final SHA here.
'''
    target=DOCS/'exp006_date_repair_report.md'
    if check:
        if target.read_bytes()!=text.encode(): raise ValueError('Date repair report differs from canonical evidence')
    else: target.write_bytes(text.encode())
    return {'timing':t['status'],'primary':p['status'],'closure':s['status'],'confirmation_accesses':0}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true');parser.add_argument('--audit',action='store_true')
    a=parser.parse_args()
    if a.audit: print(audit())
    print(report(a.check))


if __name__=='__main__': main()
