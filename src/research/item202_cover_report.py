"""Final bounded EXP006 source-feasibility disposition; no remote operations."""
from collections import Counter
import argparse,hashlib,json
from src.research.spec import ROOT,digest
from src.research.phase3c.sources import put
from src.research.sec_pilot.acquisition import Archive
from src.research.item202_cover_run import RAW,DOCS,SAMPLE,review

CERT=DOCS/'exp006_cover_identity_certificate_v002.json'
REPORT=DOCS/'exp006_cover_identity_report.md'


def certify():
    s=json.loads(SAMPLE.read_bytes());r=json.loads((RAW/'cover_review_v004.json').read_bytes())
    if digest(r['records'])!=r['records_sha256'] or digest(s)!=r['sample_sha256']:raise ValueError('Source review hash differs')
    n=len(r['records']);upper=r['single_common_count']
    if upper/n>=.95:raise ValueError('Source upper bound does not prove failure; downstream identity/path testing required')
    cohorts={}
    for label,selector in [('year',lambda x:x['filing_date'][:4]),('quarter',lambda x:x['filing_date'][:4]+'Q'+str(x['quarter'])),
                           ('frequency',lambda x:'single_event_issuer' if x['source_unique_issuer_events']==1 else 'repeat_issuer'),
                           ('source_exchange',lambda x:x['selected_common_row']['exchange'] if x['selected_common_row'] else 'UNRESOLVED_OR_NO_SINGLE_COMMON')]:
        groups={}
        for group in sorted({selector(x) for x in r['records']}):
            part=[x for x in r['records'] if selector(x)==group];single=sum(x['single_common_cover'] for x in part)
            groups[group]={'sample_candidates':len(part),'complete_cover_tuple':sum(x['complete_cover_tuple'] for x in part),
                'single_common':single,'multiple_common':sum(x['common_count']>1 for x in part),'SEC_identity_candidates':sum(x['SEC_identity_candidate'] for x in part),
                'fully_resolved_certificates':0,'source_only_fully_resolved_ceiling_percent':100*single/len(part)}
        cohorts[label]=groups
    baseline=json.loads((ROOT/'.research/item202_cover_v002/baseline.json').read_bytes())
    protected={p:h for p,h in baseline.items() if p.startswith(('experiments/','data/processed/')) or p.startswith('docs/acceleration/') and p!='docs/acceleration/master_plan.md'}
    for p,h in protected.items():
        if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h:raise ValueError('Earlier artifact changed: '+p)
    requests={};statuses=Counter()
    for group in ('SEC','rule_documentation'):
        folder=RAW/group
        files=list((folder/'receipts').glob('*.json')) if group=='SEC' else list((folder/'attempts/SEC').glob('*.json'))
        requests[group]=len(files)
        for p in files:
            rr=json.loads(p.read_bytes());Archive(folder).read(rr['body']);statuses[str(rr['status'])]+=1
    c={'version':'EXP006_event_date_identity_final_certificate_v002','status':'ABANDON_EXP006_SOURCE_FEASIBILITY',
       'starting_head':s['starting_head'],'sample_sha256':digest(s),'review_sha256':digest(r),'review_records_sha256':r['records_sha256'],
       'sample_candidates':n,'sample_unique_legal_filer_CIKs':len({x['CIK'] for x in r['records']}),
       'cover_identity_success':r['cover_tuple_count'],'single_common_class':upper,'multiple_common_classes':r['multiple_common_count'],
       'single_common_rate_percent':100*upper/n,'SEC_identity_candidates':r['SEC_identity_candidate_count'],
       'fully_resolved_certificates':0,'fully_resolved_rate_percent':0,'maximum_possible_fully_resolved_percent':100*upper/n,
       'provider_mapping_rate':None,'path_certification_rate':None,
       'provider_mapping_path_not_run_reason':'Mandatory cover/common-class ceiling is below95% even assuming perfect downstream mapping and paths',
       'coverage':cohorts,'source_failure_reasons':r['source_failure_counts'],
       'population':{'source_states':s['revision_source_counts'],'known_original_pairs':s['confirmed_legal_filer_accession_pairs'],
            'candidate_legal_filer_CIKs':s['candidate_legal_filer_CIKs'],'unknown_accessions':s['unknown_accessions'],'unknown_years':s['unknown_by_year'],
            'control_identity_certificates':0,'unknown_controls_or_events':0,'source_claim_unchanged':True},
       'requests':requests,'SEC_starts_total':sum(requests.values()),'verified_primary_cache_hits':sum(x['cache_hit'] for x in r['records']),
       'HTTP_statuses':dict(statuses),'OpenFIGI_starts':0,'Tiingo_starts':0,'FMP_starts':0,'Nexus_starts':0,
       'price_field_or_session_inspections':0,'performance_evaluations':0,'confirmation_accesses':0,
       'account_wide_debit':'UNKNOWN','purchase_or_upgrade':False,'scale_run':False,'experiment_registered':False,'freeze_commit':None,
       'inference_methods_evaluated':0,'synthetic_power_not_run':True,'hypothesis_status':'UNTESTED_SOURCE_FEASIBILITY_FAILURE',
       'parser_review_is_source_informed_not_independent_holdout':True,'earlier_parser_receipts':{
          str(i):hashlib.sha256((RAW/f'cover_review_v{i:03d}.json').read_bytes()).hexdigest() for i in (1,2,3)},
       'parser_code_sha256':hashlib.sha256((ROOT/'src/research/item202_cover.py').read_bytes()).hexdigest(),
       'source_taxonomy_review':'V002 retains original taxonomy and accepts exact standalone Common title as ordinary common equity; no arbitrary class selection',
       'protected_artifact_hashes':protected,'further_repair_authorized':False,'EXP004_paused':True,'EXP005_abandoned_absent':True}
    put(CERT,c);return c


def audit():
    c=json.loads(CERT.read_bytes());s=json.loads(SAMPLE.read_bytes())
    if digest(s)!=c['sample_sha256']:raise ValueError('Frozen sample changed')
    replay=review(4)
    if digest(replay)!=c['review_sha256']:raise ValueError('Final parser replay changed')
    if certify()!=c:raise ValueError('Disposition changed')
    # The primary SEC rule is preserved as original PDF bytes.
    e=json.loads((DOCS/'exp006_cover_rule_evidence_v001.json').read_bytes())
    Archive(RAW/'rule_documentation').read(e['original_body'])
    if (ROOT/'experiments/EXP006').exists() or (ROOT/'experiments/EXP006_SEC_ITEM202_PREDICTIVE').exists():raise ValueError('Abandoned experiment registered')
    return {'status':'PASS','original_covers_replayed':len(replay['records']),'confirmation_accesses':0}


def report(check=False):
    c=json.loads(CERT.read_bytes());s=json.loads(SAMPLE.read_bytes());p=c['population'];e=json.loads((DOCS/'exp006_cover_rule_evidence_v001.json').read_bytes())
    vpath=DOCS/'exp006_cover_identity_validation.json';v=json.loads(vpath.read_bytes()) if vpath.exists() else {}
    table='\n'.join(f"| {name} | {g['sample_candidates']} | {g['complete_cover_tuple']} | {g['single_common']} | {g['source_only_fully_resolved_ceiling_percent']:.1f}% |" for name,g in c['coverage']['quarter'].items())
    text=f'''# EXP006 final identity redesign: source-feasibility abandonment

**ABANDON_EXP006_SOURCE_FEASIBILITY. The Item 2.02 economic hypothesis remains untested.** Starting HEAD `{c['starting_head']}`, as of 2026-10-13. [Owner instruction](owner_item202_cover_redesign_2026-10-13.md) authorized one final bounded pre-performance redesign and required abandonment if its unchanged 95% gate failed. EXP006 remains absent: no registration, freeze, Development or confirmation access.

## Regulatory basis and separate design

The [official SEC final rule](https://www.sec.gov/files/rules/final/2019/33-10618.pdf), Release33-10618, establishes May2,2019 effectiveness/compliance for the human-readable Form8-K Section12(b) class/title, symbol and exchange fields. Inline cover tagging follows a phased category/first-applicable-10-Q schedule, with fiscal-period dates June15,2019/2020/2021. Absence of Inline tags does not establish absence of human disclosure. The requirement concerns Section12(b) securities; not every8-K registrant necessarily has such securities. Blank/None fields are not automatically illegal noncompliance. [Evidence receipt](exp006_cover_rule_evidence_v001.json), original PDF SHA256 `{e['original_body']['sha256']}`; original bytes are ignored and immutable.

[Design v002](exp006_design_candidate_v002.json) separately records Development2019-05-02–2020-12-31 and unchanged historical confirmation2021-01-01–2026-09-30. It replaces the multi-year-span requirement with an event-date class/provider certificate plus an economically resolvable entry-to-20-session-exit path. Existing availabilityv003,20-session horizon,10bps/side costs,20bps/side/+1-session robustness,0.50percentage-point materiality, positive95% lower endpoint and12-evaluation ceiling remain. Earlier designv001 and all prior reports/contracts keep their original bytes; inception was revised solely for source feasibility before any returns, and never moved again.

## Revised source population

| Revised-period source state | Keys |
| --- | ---: |
| Known original Item2.02 | {p['source_states']['ITEM202_CONFIRMED']:,} |
| Confirmed non-Item originals; controls require the same identity/path certificate | {p['source_states']['NON_ITEM202_CONFIRMED']:,} |
| Amendment version-only | {p['source_states']['AMENDMENT_VERSION_ONLY']:,} |
| Unknown Item status; neither events nor controls | {p['source_states']['UNKNOWN_ITEM_STATUS']} |

There are {p['known_original_pairs']:,} distinct known legal-filer/accession pairs and {p['candidate_legal_filer_CIKs']:,} candidate legal filers in this period. The64 unknown keys cover61 accessions:2019=2,2020=62. All113 keys/107 accessions remain in the earlier full-period missingness contract; no recovery resumed. These are reconciled daily/quarterly SEC observation keys, not certified independent trading events, every legal obligation, perfect contemporaneous ingestion or untouched-vintage proof. Non-Item source membership alone never admits a control; certified control identities remain0.

## Fixed sample, parser review and gate

The [sample](exp006_cover_identity_sample_v002.json) froze {c['sample_candidates']} candidates from {c['sample_unique_legal_filer_CIKs']} legal filers before new bodies were retrieved. Forty records per available year/quarter reserve earliest observed dates, single/repeat issuers and cofilers. Four May2,2019 filings remain; one has unresolved cover/class/domestic evidence, with no inception replacement. No price, fame, survival or provider convenience selected the sample. {c['verified_primary_cache_hits']} previously archived originals were verified cache hits; the remaining originals were acquired through exact frozen URLs.

The parser reads actual human tables/formatted text, keeps class/symbol/exchange rows and original character locators, and uses no issuer-specific patch. Source-informed generic reviews added labels below values, quoted symbols, header synonyms, explicit prose and exact standalone Common titles. Original extraction/prototype receipts and parser code are retained privately; they are not independent classifier holdouts. Missing/unparseable values remain unavailable, never inferred from company names. Preferred/depositary/warrant/right/unit/debt/fund-like classes do not become common equity; two multiple-common cases receive no discretionary class choice. No multi-year listing-span requirement was reinstated.

| Sample stage | Count / rate |
| --- | --- |
| Complete human-readable cover identity tuple | {c['cover_identity_success']}/{c['sample_candidates']} ({100*c['cover_identity_success']/c['sample_candidates']:.1f}%) |
| Single common-class candidate | {c['single_common_class']}/{c['sample_candidates']} ({c['single_common_rate_percent']:.1f}%) |
| Multiple common classes | {c['multiple_common_classes']} |
| SEC identity candidates after domestic/cofiler checks | {c['SEC_identity_candidates']}/{c['sample_candidates']} |
| Completed fully resolved certificates | 0; mapping/path stages not run |
| Maximum possible fully resolved rate with perfect downstream mapping/paths | **{c['maximum_possible_fully_resolved_percent']:.1f}%** |
| Mandatory threshold | **95%** |

| Quarter | Candidates | Complete tuple | Single common | Fully resolved ceiling |
| --- | ---: | ---: | ---: | ---: |
{table}

The [canonical certificate](exp006_cover_identity_certificate_v002.json) also reports year, source exchange and single/repeat-issuer breakdowns and overlapping failure reasons. Missing tuples38; no eligible common-class parse51; multiple classes2; domestic incorporation unresolved69; cofiler/security-issuer link unresolved10; symbol representation unresolved1. These are extraction/certification findings, not proof every missing record lacks a tradable security. Sparse or absent disclosure, None/N/A presentations, excluded instrument types and unresolved presentation/issuer evidence remain distinct from economic outcomes.

Even granting successful mapping and a valid20-session path to **every** single-class candidate, only227/280 could complete the certificate. Thus the unchanged fixed-sample denominator fails95% before any provider/path query. The zero completed-certificate inventory is **not a measured0% vendor success rate**. OpenFIGI/provider mapping rates, real path rates, renamed/ended/terminal denominators and complete control coverage are NOT_MEASURED. No current-ticker projection, first-match selection or survivor filter was used. No scalable mapping campaign or market-data certification followed this proven upper-bound failure.

## Verification and final stop

New starts: SEC {c['SEC_starts_total']} ({c['requests']['rule_documentation']} rule documentation plus {c['requests']['SEC']} primary bodies); verified cache hits {c['verified_primary_cache_hits']}; HTTP{json.dumps(c['HTTP_statuses'],sort_keys=True)}. OpenFIGI/Tiingo/FMP/Nexus/Aurora calls0; price-field/session inspections0; no purchase/upgrade; account-wide debit UNKNOWN. Browser official-rule discovery/review is separate (two calls; underlying fetch count unknown). The locally configured SEC identity was verified without disclosure; request contacts remain redacted. Original/vendor/private bodies, prototypes and credentials are not committed.

Validation: {v.get('local_tests_passed','pending')} local tests, {v.get('public_tests_passed','pending')} public tests, {v.get('tests_skipped','pending')} skipped. [Receipt](exp006_cover_identity_validation.json). Offline audit verifies cached/new source hashes, sample keys, parser replay, rule PDF and protected history. Public reproduction requires only tracked receipts; private audit needs ignored originals.

```sh
python -m src.research.item202_cover_report --check
python -m src.research.item202_cover_report --audit --check
python -m src.research.public_checks
python -m unittest discover -s tests -v
python -m src.presentation.exp001 --check
```

**Final stop under owner sections13/26.** Identity scaling, provider price certification, matching, real inference/calibration, synthetic power, Proof, freeze and Development were NOT_RUN. No spec/freeze commit, real effect, interval or p-value exists. Performance evaluations and confirmation accesses remain **0**. EXP004 stays paused; EXP005 abandoned/absent; EXP006 abandoned as a source-feasibility candidate and remains unregistered. The scientific closure is not evidence that Item2.02 has no alpha. No further identity search/provider/inception rescue, Phase4B, optimizer or paper/live action is authorized.
'''
    # Human-facing spacing only; identifiers and fixed canonical paths preserved.
    import re
    text=re.sub(r'\b(Form|Item|Release|Development|confirmation|design|May|June|Section|period|fields|classes|tuples|unresolved|coverage|controls|calls|inspections|Phase)(?=\d)',r'\1 ',text)
    for old,new in [('every8-K','every 8-K'),('availabilityv003','availability v003'),('designv001','design v001'),
                    ('and12-','and 12-'),('positive95%','positive 95%'),('The64','The 64'),('cover61','cover 61'),
                    ('All113','All 113'),('2020=62','2020 = 62'),('2019=2','2019 = 2'),
                    ('valid20-','valid 20-'),('only227/280','only 227/280'),('fails95%','fails 95%'),('method95%','method 95%'),
                    ('measured0%','measured 0%'),('PDF SHA256','PDF SHA-256'),('no eligible common-class parse51','no eligible common-class parse 51')]:
        text=text.replace(old,new)
    text=re.sub(r'(?<=\d),(?=\d{4}\b)',', ',text)
    text=re.sub(r',(?!\s)(?=\d+(?:\.\d+)?(?:-session|bps|percentage|-evaluation))',', ',text)
    text=re.sub(r'(?<=\d)(?=bps|percentage)', ' ',text)
    if check:
        if REPORT.read_bytes()!=text.encode():raise ValueError('Final cover report differs')
    else:REPORT.write_bytes(text.encode())
    return {'status':c['status'],'source_class_upper_bound_percent':c['maximum_possible_fully_resolved_percent'],'confirmation_accesses':0}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--certify',action='store_true');p.add_argument('--audit',action='store_true');p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.certify:print(certify()['status'])
    if a.audit:print(audit())
    print(report(a.check))
