"""Canonical public report/private replay for the scoped historical-population stop."""
from collections import Counter
import argparse
import hashlib
import json

from src.research.spec import ROOT,digest
from src.research.item202_population_acquire import RAW,DOCS,manifest
from src.research.item202_population import parse_daily,reconcile,KEY_FIELDS
from src.research.sec_pilot.acquisition import Archive
from src.research.item202_availability import parse_header

GROUPS=('directories','daily_masters','unresolved_headers','unresolved_headers_continued',
        'unresolved_header_representations','cofiler_headers')


def certificate():return json.loads((DOCS/'exp006_historical_population_certificate_v003.json').read_bytes())


def audit():
    manifest();cert=certificate();counts={};statuses=Counter()
    for group in GROUPS:
        base=RAW/group;reserved={p.stem for p in (base/'reservations').glob('*.json')}
        receipts={p.stem:p for p in (base/'receipts').glob('*.json')};errors={p.stem:p for p in (base/'errors').glob('*.json')}
        if reserved!=receipts.keys()|errors.keys():raise ValueError('Unreconciled reservation IDs')
        counts[group]=len(reserved)
        for p in receipts.values():
            r=json.loads(p.read_bytes());Archive(base).read(r['body']);statuses[str(r['status'])]+=1
            if r['attempt']!=1 or r['request_headers']!='LOCALLY_IDENTIFIED_SEC_USER_AGENT_REDACTED':raise ValueError('Retry/identity provenance changed')
    if counts['daily_masters']>1650 or sum(counts[g] for g in GROUPS[2:])>1000:raise ValueError('Source ceilings changed')
    dispatch=json.loads((DOCS/'exp006_daily_master_dispatch.json').read_bytes());daily=[]
    for planned in dispatch['records']:
        part=json.loads((RAW/'daily_parts'/(planned['day']+'.json')).read_bytes())
        body=Archive(ROOT/part['source_root']).read(part['receipt']['body'])
        replay=parse_daily(body,planned['day'],part['receipt']['body']['sha256'])
        if replay['rows']!=part['rows'] or replay['outside_Development_rows']!=part['outside_Development_rows']:raise ValueError('Daily parse replay changed')
        daily+=part['rows']
    quarterly=[]
    for p in sorted((ROOT/'data/raw/item202_remedy_v001/source_closure/census_parts').glob('*.json')):
        quarterly += [{k:r[k] for k in (*KEY_FIELDS,'source_line','source_index_sha256')} for r in json.loads(p.read_bytes())['rows']]
    union=reconcile(daily,quarterly)
    if digest(union['rows'])!=cert['union_sha256']:raise ValueError('Union full-key replay changed')
    actual=json.loads((RAW/'resolved_population_final.json').read_bytes())
    if digest(actual['rows'])!=actual['sha256'] or actual['sha256']!=cert['resolved_population_sha256']:raise ValueError('Final source states changed')
    if {tuple(r[k] for k in KEY_FIELDS) for r in actual['rows']}!={tuple(r[k] for k in KEY_FIELDS) for r in union['rows']}:
        raise ValueError('Source key substituted or omitted')
    cache={}
    for group in GROUPS[2:]:
        for p in (RAW/group/'receipts').glob('*.json'):
            r=json.loads(p.read_bytes());cache[r['url']]=(RAW/group,r)
    for row in actual['rows']:
        review=row.get('original_header_review')
        if not review:continue
        root,receipt=cache[review['source_url']];body=Archive(root).read(receipt['body'])
        if review['source_url'].endswith('.txt'):body=body.split(b'<DOCUMENT>',1)[0]
        header=parse_header(body,cik=row['CIK'],accession=row['accession'],form='8-K')
        if header['source_chronology_contradictory'] or ('2.02' in header['source_items'])!=row['source_Item202_present']:
            raise ValueError('Original membership replay differs')
    unknown=[r for r in actual['rows'] if r['form']=='8-K' and r['event_state']=='UNKNOWN']
    if len(unknown)!=cert['unresolved_original_Item_source_rows']:raise ValueError('Unknowns changed')
    if any(r['form']=='8-K/A' and r['event_state']!='AMENDMENT_VERSION_ONLY' for r in actual['rows']):raise ValueError('Amendment became signal')
    for name in ('EXP006','EXP006_SEC_ITEM202_PREDICTIVE'):
        if (ROOT/'experiments'/name).exists():raise ValueError('Blocked experiment created')
    return {'status':'PASS','counts':counts,'new_SEC_starts':sum(counts.values()),'HTTP_statuses':dict(statuses),
            'daily_files_replayed':len(dispatch['records']),'source_union_rows':len(actual['rows']),
            'unresolved_original_keys_retained':len(unknown),'confirmation_accesses':0}


def report(check=False):
    m=json.loads((DOCS/'exp006_historical_population_manifest.json').read_bytes());c=certificate()
    validation_path=DOCS/'exp006_historical_population_validation.json'
    v=json.loads(validation_path.read_bytes()) if validation_path.exists() else {}
    states=c['population_states'];events=c['event_states']
    text=f'''# EXP006 historical filing population: unresolved Item membership

**Daily population reconstruction completed; HISTORICAL_ITEM_STATUS_BLOCKED. EXP006 remains absent and unfrozen.** Starting HEAD `{m['starting_head']}`, as of 2026-10-13. [Exact owner instruction](owner_item202_population_identity_2026-10-13.md). No timing redesign, market outcomes or confirmation access occurred.

The full declared daily-index acquisition and the bounded unresolved-original audit were executed. The remaining blocker is concrete: **{c['unresolved_original_Item_source_rows']} original source keys across {c['unresolved_original_Item_accessions']} accessions still lack authoritative Item membership** under the tested official representations. They are UNKNOWN, never non-Item-2.02 controls or zero activity. Identity feasibility did not launch after this upstream source gate failed.

## What population was reconstructed

The archived SEC access guide was rechecked by original hash before dispatch. It states that later removals are not reflected in previous daily/feed/oldload indexes, while full/quarterly views rebuild weekly. Official directory metadata enumerated exactly {c['daily_index_files']:,} Development daily masters in 24 quarters; these exact routes were pushed in `39d8009` before daily acquisition. Only enumerated 2015–2020 files were requested, with three verified cache hits. Empty indexes remain observations, not imputed missing filings.

| Historical population measure | Result |
| --- | ---: |
| Daily files / new daily starts / cache hits | {c['daily_index_files']:,} / {c['daily_request_starts']:,} / {c['daily_cache_hits']} |
| Raw daily observations / distinct daily full keys | {c['daily_observation_rows']:,} / {c['daily_union_rows']:,} |
| Equivalent repeated daily observations | {c['duplicate_equivalent_daily_rows']} |
| Current quarterly rows | {c['quarterly_rows']:,} |
| PRESENT_BOTH | {states['PRESENT_BOTH']:,} |
| HISTORICAL_DAILY_ONLY | {states['HISTORICAL_DAILY_ONLY']} |
| CURRENT_QUARTERLY_ONLY | {states['CURRENT_QUARTERLY_ONLY']} |
| Reconciled union full keys | {c['reconciled_union_rows']:,} |
| Daily union original 8-K / 8-K/A | {c['daily_union_original8K']:,} / {c['daily_union_amendment8KA']:,} |
| Daily union accessions / CIKs | {c['daily_union_unique_accessions']:,} / {c['daily_union_unique_CIKs']:,} |
| Full union accessions / CIKs | {c['union_unique_accessions']:,} / {c['union_unique_CIKs']:,} |
| Additional legal-filer keys per shared accession | {c['shared_accession_cofiler_extra_legal_filer_keys']:,} |
| Same-filer/accession date/form/path variants | {c['same_filer_accession_date_form_path_variant_extra_keys']} |
| Equivalent quarterly duplicate keys | {c['duplicate_equivalent_quarterly_rows']} |

Keys retain CIK, accession, form, source filed-date representation and path. Every difference and every source observation/locator is retained in ignored `population_differences.json`, with its full hash in [reconciliation](exp006_historical_population_reconciliation.json). Neither daily-only nor quarterly-only means deleted, invalid or eligible automatically. Repeated index observations and date variants are distinct from cofilers and independent trades.

The defensible claim is **the union of archived SEC daily master-index observations over Development, reconciled against the present rebuilt quarterly census, with quarterly-only observations separately retained**. These bytes were acquired today: they do not establish contemporaneous ingestion, every legally required filing, or an untouched vintage for every filing document. Known PAC/removal explanations remain UNKNOWN; numerical index differences alone are not such explanations.

## Original Item membership and version evidence

Current, previously audited bulk labels were reused only for exact Development keys. Missing historical keys were checked against the existing quarantined ZIP with date/accession gates before Items/clock/primary fields; no current ticker/company fields or future feature values were used. This left 625 original accessions (1,173 source keys) requiring original-source checks, below the predeclared 1,000-start ceiling. The 625-accession dispatch was pushed in `1ad6a12` before header requests.

The first HTML-header pass stopped after ten HTTP200 responses and one `404 NoSuchKey`. Its [initial certificate](exp006_historical_population_certificate.json), body, error and persisted stop remain unchanged. The [reviewed continuation](exp006_historical_header_review_v002.json) permitted only unvisited records and documented exact `.hdr.sgml` / source-index `.txt` representations on non-denial404. No failed HTML URL was retried; no403/429, redirect, mirror or host rotation was bypassed.

All 625 accessions were examined: 518 original HTML headers were recovered and 107 accessions returned404 on all three first-filer representations. Those alternatives recovered zero originals. Five shared-accession cases had another filer path explicitly evidenced by the indexes; all 15 additionally frozen requests also returned404. This avoids concluding accession-wide absence merely from one filer path. [Final certificate](exp006_historical_population_certificate_v003.json) preserves every result and key. Missing originals under these tested routes are not proof of legal removal or universal archive unavailability.

| Source feature / unresolved state | Result |
| --- | ---: |
| Known original Item 2.02 source keys | {c['candidate_original_Item202_rows']:,} |
| Unique known original legal-filer/accession pairs | {c['candidate_original_unique_filer_accession_count']:,} |
| Known candidate accessions / legal-filer CIKs | {c['candidate_original_unique_accessions']:,} / {c['candidate_original_unique_CIKs']:,} |
| Non-Item-2.02 source keys | {events.get('NON_ITEM202',0):,} |
| Amendments retained as version-only keys | {events.get('AMENDMENT_VERSION_ONLY',0):,} |
| Original Item states still UNKNOWN | {c['unresolved_original_Item_source_rows']} keys / {c['unresolved_original_Item_accessions']} accessions |
| Original header/representation starts | {c['historical_Item_header_starts']} / 1,000 ceiling |

These are source candidates, not certified trading events. All 8-K/A rows remain version-only and never produce separate signals or retrospectively replace an original. Amendment-parent links and version relationships remain unresolved; no arbitrary parent was selected. Current primary-title concordance remains the earlier 96-source sample certificate, not full-population historical primary validation.

Source index dates and raw header FILED AS OF DATE were recorded separately. Original Item membership requires verified filer/form/accession; a date-label difference is not Item absence. Raw keys were not rewritten to match the current header. Source-key counts exceed unique legal-filer/accession counts because retained date variants are additional observations. Final security/class/day aggregation must wait for dated identity reconciliation.

Unresolved original keys by source filed year: {', '.join(y+': '+str(n) for y,n in sorted(c['unresolved_original_Item_years'].items()))}. Most are in 2020; this is source missingness, not evidence of poor returns or ended classes. Issuer-level identity, rename/end and terminal clustering were not measured. All unresolved originals remain in the denominator; none becomes a matched non-Item control. The remaining 146 request credits do not supply a demonstrated original source. A huge Feed/Oldloads recovery was not launched: daily population acquisition succeeded, previous whole-day transfers exceeded their bounds, and their original stops remain intact.

## Gate disposition and stop

| Gate | Disposition |
| --- | --- |
| Daily-index enumeration/archive/reconciliation | COMPLETE_FOR_DECLARED_SOURCE_OBSERVATIONS |
| Historical legal-filing or untouched-vintage exhaustiveness | NOT_CLAIMED |
| Original Item population / PAC-version certificate | HISTORICAL_ITEM_STATUS_BLOCKED;107 accessions unresolved |
| Availability v003 / earlier sampled classification | PRESERVED_UNCHANGED; no new timing study or activation |
| Identity sample, three routes and coverage by year/issuer | NOT_RUN_UPSTREAM_ITEM_SOURCE_STOP;95% standard retained |
| Fully mapped/ambiguous identities, classes, renames, endings and terminal paths | NOT_MEASURED_IN_THIS_PASS; no new identity certificate |
| Provider, deterministic matching, execution certification | NOT_RUN_UPSTREAM_SOURCE_STOP |
| Inference candidates/calibration/synthetic power | NOT_RUN; zero methods evaluated |
| EXP006 spec/freeze/Development | ABSENT / NONE / NOT_RUN |
| Performance evaluations / confirmation accesses | 0 / 0;12-evaluation ceiling unchanged |

This is a source-input failure, not an economic test of Item2.02 or an identity-route failure inferred without an audit. Reading local EXP002 diagnostics established their discovery-only role; clipped spans, missing venue/type evidence and previous underfilled populations were not promoted to canonical identity. No current ticker, future surviving-security or price-availability join defined this population. No Development date/horizon/cost/materiality/trial choice changed.

## Verification and reproduction

New direct starts: **2,375 SEC**:24 directory indexes,1,497 daily masters and854 original-header/representation checks. Network responses:2,039 HTTP200 and336 HTTP404; zero retries. Three daily cache hits are separately verified, not new starts. Documentation was reused offline; new browser/documentation, OpenFIGI, Tiingo, FMP, Orbis, Nexus and Aurora calls were zero. No purchase/upgrade; account-wide debit is unknown. Local SEC identity and configured-provider presence were checked without exposing values. Request identity is correctly labelled redacted in new receipts; no contact or source payload is committed.

**Validation:** {v.get('local_tests_passed','pending')} local tests, {v.get('public_tests_passed','pending')} public tests, zero skipped. [Receipt](exp006_historical_population_validation.json). Earlier reports, passed v003 timing, failed clock/remedy receipts, policies, raw archives, experiment definitions, processed baselines, metric code and dependency pins remain unchanged. EXP004 is paused, EXP005 abandoned/absent, EXP006 absent. No performance, held-out outcomes, optimization, paper/live activity or next phase occurred.

```sh
python -m src.research.item202_historical_report --check
python -m src.research.item202_historical_report --audit --check
python -m src.research.public_checks
python -m unittest discover -s tests -v
python -m src.presentation.exp001 --check
```

Public report regeneration reads tracked canonical receipts only. Private audit needs ignored originals/derivatives and verifies full keys, hashes, repeated observations, source memberships and preserved unknowns without network. Acquisition commands require explicit `--execute`; caches, budgets and old stops persist. **Stopped under owner section25 at unrecovered historical-original Item membership, before identity scaling or freeze.** No next source campaign or architecture phase is launched automatically. Delivery records the final Git SHA and hosted CI separately.
'''
    p=DOCS/'exp006_historical_population_report.md'
    if check:
        if p.read_bytes()!=text.encode():raise ValueError('Historical population report differs')
    else:p.write_bytes(text.encode())
    return {'status':c['status'],'daily_files':c['daily_index_files'],'unresolved_original_Item_keys':c['unresolved_original_Item_source_rows'],'confirmation_accesses':0}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--audit',action='store_true');a=p.parse_args()
    if a.audit:print(audit())
    print(report(a.check))


if __name__=='__main__':main()
