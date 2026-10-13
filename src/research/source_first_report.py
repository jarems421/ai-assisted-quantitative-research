"""Public source-first reports; optional private hash audit, never acquire sources."""
import argparse
import hashlib
import json
from src.research.source_first import DOCS,RAW,DIMENSIONS,HARD_GATES,ProbeHTTP,frozen,assess,mechanism_allowed
from src.research.spec import digest


def audit():
    m=frozen();review=json.loads((DOCS/'phase4a_researchability_map.json').read_bytes())
    if review['acquisition_sha256']!=hashlib.sha256((RAW/'acquisition.json').read_bytes()).hexdigest():raise ValueError('Acquisition provenance changed')
    saved=RAW/'reviews'/(digest(review)+'.json')
    if not saved.exists() or json.loads(saved.read_bytes())!=review:raise ValueError('Independent archived review changed')
    registry=json.loads((DOCS/'phase4a_source_registry.json').read_bytes())
    receipts=[json.loads(p.read_bytes()) for p in RAW.glob('*/receipts/*.json')]
    starts=list(RAW.glob('*/reservations/*.json'))
    if len(starts)!=registry['starts'] or len(receipts)!=len(starts) or len(starts)>36:raise ValueError('Request ledger/ceiling mismatch')
    for surface in m['surfaces']:
        http=ProbeHTTP(m,surface)
        for path in (http.root/'receipts').glob('*.json'):
            r=json.loads(path.read_bytes());http.archive.read(r['body'])
            expected=[x for x in registry['response_receipts'] if x['surface']==surface['id'] and x['request_started_at_utc']==r['request_started_at_utc']]
            if len(expected)!=1 or any(expected[0].get(k)!=v for k,v in r.items()):raise ValueError('Receipt substitution')
    return len(starts)


def report(check=False):
    m=json.loads((DOCS/'phase4a_researchability_map.json').read_bytes());registry=json.loads((DOCS/'phase4a_source_registry.json').read_bytes())
    if m['manifest_sha256']!=registry['manifest_sha256']:raise ValueError('Map/registry mismatch')
    preferred=[r['id'] for r in m['surfaces'] if assess(r)]
    if preferred!=m['preferred_surfaces']:raise ValueError('Preferred surface hard-gate mismatch')
    validation=DOCS/'phase4a_source_first_validation.json';v=json.loads(validation.read_bytes()) if validation.exists() else {}
    dimensions='| Dimension | '+ ' | '.join(r['id'] for r in m['surfaces'])+' |\n| --- | '+' | '.join('---' for r in m['surfaces'])+' |\n'
    dimensions+='\n'.join('| '+k.replace('_',' ')+' | '+' | '.join(r['dimensions'][k]['status'] for r in m['surfaces'])+' |' for k in DIMENSIONS)
    routes='| Surface / probe | Exact tested URL | HTTP | Bytes |\n| --- | --- | ---: | ---: |\n'+'\n'.join('| '+r['surface']+'/'+r['purpose']+' | '+r['url']+' | '+str(r['status'])+' | '+str(r['body']['bytes'])+' |' for r in registry['response_receipts'])
    md=f'''# Phase 4A-R: source-first researchability map

**{m['recommendation']}; SEC is the preferred surface for a subsequent bounded design review.** As of 2026-10-13. This is planning-level source-route plausibility, not a complete historical population, observed public-timing, identity, execution or inference certificate. Three fixed surfaces were reviewed after exact access probes; no fourth family pilot or hypothesis was selected. NEXT_EXPERIMENT NONE_SELECTED; PERFORMANCE_AUTHORIZED FALSE.

## Actual access and samples

{routes}

Six starts, zero retries, of the36-start maximum; no search/discovery request, source purchase or account upgrade. Existing15 original Phase2 documents were hash/length verified without network and its archive/parser evidence reused. The current SEC fixture index matches its previous original bytes. All three primary routes returned usable200 responses. Federal Register documentation302 was archived without following; its source stop remains. ClinicalTrials documentation200 is a JavaScript shell, not substantive parsed API/history guidance. No blocked family route was retried. Git/CI metadata are separate delivery operations; account-wide debit remains unknown.

Federal Register's fixed2019-01-02 first page returned2 notices; the source advertises12 documents for that day. Ten unsampled records are not absent. Both sampled rows carry document number, publication date, agency IDs and official PDF links; those PDFs were not fetched and legal-original/correction lineage is not certified. ClinicalTrials' neutral first page returned2 studies and source count606601. Both happened to be COMPLETED; outcome was not a query filter. This current count is not a count of eligible corporate events or independent observations. Their first-post fields date to2000, last-update fields to2005, and the posting structs say ESTIMATED. They do not establish historical first-public time, prior content or complete historical registry coverage.

## Researchability matrix

{dimensions}

Status meanings and hard gates: [SourceResearchabilityContract](phase4a_researchability_contract.md). [Canonical map](phase4a_researchability_map.json) gives every status a reason and source-hash/document provenance; [registry](phase4a_source_registry.json) records exact samples, request clocks and original-body hashes. No score totals or imagined alpha probabilities were used.

**SEC passes the planning-level hard-gate plausibility screen**: current access, documented form/CIK/date/path public-filing indexes, original accession/header archive/replay, historical index coverage, and plausible repeated observations. Denominator, PIT and record variation remain PARTIAL with explicitly recorded plausibility reasons. No source passes executable trading-certification gates. The preferred population is filings defined by type/date, not all historically tradable US stocks or all filings a company should have made. A complete obligation-based missing-filing panel cannot be manufactured from filed records.

Federal Register remains a conditional frontier, not a preferred surface: historical publication-date access works, but original-publication/PIT/correction evidence and company linkage are unresolved. ClinicalTrials is not ready for historical discovery through this probed route: current-version date/status/sponsor fields cannot reconstruct prior versions. Another official historical route was not tested and is not declared impossible. The small candidate set was not expanded to force success; only one of three surfaces currently meets evidenced planning plausibility.

## SEC-native surface limits

The official SEC guide documents public filing indexes from1994Q3, including company name, form type, CIK, date filed and source filename. It also documents post-acceptance corrections/deletions, nightly index changes and rebuilt quarterly/full indexes. Daily/feed/oldload indexes can retain references after later removals; that creates a plausible missingness-preserving census route, not recovery of unavailable original bytes. A current quarterly index is not an untouched historical vintage. Preserve daily enumeration, original accession versions, amendments, PAC/deletion relationships and unresolved missing documents in a versioned source denominator receipt before selecting a feature.

Acceptance, dissemination, filing date, public website accessibility and present-day download remain separate. Existing winter timestamp evidence and October uncertainty remain unchanged. No v002/v003 activation or extension to other forms occurs. New form/window/channel timing needs explicit review; possible conservative bounds are not observed public times. CIK identifies a filer, not a security/class; accession prefix can be an agent. Today's ticker/entity associations do not certify historical listed membership. Deleted/ended issuers cannot disappear from the denominator.

8-K, periodic, ownership and transaction form classes are conceptually enumerable from this filing universe, subject to source-contract review. No insider/institutional experiment is reopened: EXP002/EXP003 historical membership, identity, omission-to-zero and complete event-version failures remain. The review retrieves no Form4/13D/13G event corpus and supplies no absence certificate. Phase3 accounting/EPS/triple and terminal/execution/inference failures are likewise preserved, not solved by SEC access.

## Mechanisms and architecture decision

Only after the completed map, three SEC-native [mechanism directions](phase4a_mechanism_directions.md) are offered as PREDICTIVE ideas. No mechanism is chosen, scored on returns or registered. Federal Register/ClinicalTrials receive no new mechanism proposals while hard gates remain unresolved. Predictive work still needs PIT population, honest identity, matched benchmark, dependence-aware inference, costs, trial control and survivor-safe execution; causal identification is an additional requirement only for causal claims.

**KEEP_PHASE4B_LATER.** Actual blockers remain upstream source versions/denominators/public timing. SEC already supplies useful filer IDs; Federal Register lacks issuer IDs and ClinicalTrials sponsor relationships would require later dated bridges, but those limited probes do not establish entity resolution as the dominant recurring bottleneck. Standardize accession-filer-version, agency-document, study-sponsor/collaborator and eventual class spans only when a chosen source contract needs them. No graph, entity-spine campaign or causal lab is built.

The justified minimal gap is a **versioned filing-denominator receipt**, reusing archives/Store rather than another warehouse: declare date/form population; reconcile neutral daily-index entries to original accession bytes and missing/PAC/amendment states; keep as-of availability and class identity separate. This is a recommended bounded prototype, not an authorized implementation or full census. [Architecture decision](phase4a_architecture_decision.md) records the owner-approved change in sequencing and the remaining decision.

## Verification and stop

Validation: {v.get('local_tests_passed','pending')} local tests, {v.get('public_tests_passed','pending')} public tests, zero skipped. [Receipt](phase4a_source_first_validation.json). Public regeneration: `python -m src.research.source_first_report --check`. Private original-body/ledger audit: `python -m src.research.source_first_report --audit --check`; neither command acquires sources. `python -m src.research.source_first acquire --execute` is a separate bounded mutation and not reproduction; cached acquisition prevents blind resubmission. Old SEC offline replay/audit and historical pilot reports remain independently checked.

The mechanism-first family screen remains COMPLETE_THREE_FAMILIES_EXHAUSTED. Historical procurement/FDA/merger reports, raw errors/stops, all prior phase evidence, experiment artifacts, EXP004 pause, EXP005 abandonment/absence and inactive policy approvals are unchanged. No price/return/performance, strategy, new experiment, optimization, held-out opening, Orbis/Nexus/Aurora, Phase4B/4C, graph, causal lab or paper/live action occurred.

**Stop for owner review.** The exact proposed next decision is whether to commission one bounded SEC filing-denominator/PAC/availability contract prototype and then choose one of these predictive directions for a separate design review. The owner must specify the form/date/sample ceiling before any new source work. No future experiment or timing policy is approved by SOURCE_FIRST_DIRECTION_READY.
'''
    mechanisms='''# Source-first mechanism directions: SEC only

**Ideas after completed researchability review; none selected or executable.** All three are ESTIMAND_TYPE **PREDICTIVE**, with no causal claim. Listed by qualitative source-contract testability and learning value, not imagined profitability. Maximum three directions per qualified source; only SEC currently meets planning-level plausibility. No fourth family pilot, market-data request or experiment is authorized.

| Direction / exact proposed record | Economic reasoning and natural population | Dependence / prior failure / cheapest falsification |
| --- | --- | --- |
| Operating-results disclosure: accession-specific8-K Item2.02 presence/type | Disclosure may update expectations about operating persistence/uncertainty. Population: all eligible8-K filings in a separately frozen date/form census, with item classification and amendments retained; no future good/bad-result filter. A future benchmark would assess predictive value, not an analyst-surprise claim. | Repeated issuer, reporting season, multi-item filings and amendments. Avoid Phase3 EPS comparability and unsupported expectations/surprise. First test neutral item extraction and amendment/missingness coverage against archived originals; do not compute forecasts or returns. |
| Governance transition disclosure: accession-specific8-K Item5.02 event category | Changes in leadership can alter execution risk and expected continuity. Population: the same declared8-K filing universe, with appointment/departure and unresolved event categories retained without selecting successful transitions. | Repeated issuer, concurrent results/restructuring, delayed disclosure and event-type ambiguity. Prior omission-to-zero/identity failures could recur. First certify the category/announcement/filing distinction in a tiny neutral sample and keep ambiguous categories unavailable. |
| Financing/obligation disclosure: accession-specific8-K Items1.01/2.03/3.02, under a reviewed transaction definition | New agreements, direct obligations or unregistered equity issuance may describe financing constraints/capital decisions. Population: source-defined filings, not deals later known to succeed or survive; multiple items are distinct records. | Industry/credit/calendar shocks, overlapping items, subsidiary/party rights and repeated issuer. Prior merger identity/terminal and missing-population risks could recur. First test whether source locators can distinguish operating agreements from financing and original changes from amendments; reject ambiguous economic definitions before performance. |

These categories are proposed labels, not certified event contracts or trading features. Public form/item definitions and original examples need separate bounded verification before adoption; this pass did not fetch or classify an8-K corpus. No numerical signal, return, holding period, cost grid or threshold is chosen. Do not infer absence of an item or activity from missing/uncertified documents. Form4/13D/13G capability ideas are not proposed as revived EXP002/EXP003 designs.

Any future predictive design still needs a non-hindsight population, approved availability, dated class identity, dependence-aware calibration/power, predeclared benchmark/cost/trial rules and certified execution. CAUSAL_CANDIDATE would additionally require identification/counterfactual evidence; none is declared here. No first mechanism wins automatically.
'''
    architecture=f'''# Phase 4A-R: architecture decision and recommendation

**Owner decision: source-first discovery replaces mechanism-first selection.** [Verbatim instruction](owner_source_first_2026-10-13.md), 2026-10-13. The historical three-family screen is complete/exhausted, NEXT_EXPERIMENT NONE_SELECTED, performance false. This extends Research OS; it does not restart the project or reopen any rejected family/experiment.

The adopted order is exact source/access proof, denominator, PIT/timing, historical depth, identifiers/relationships, observation/dependence geometry, then economically motivated mechanism directions. No scientific score precedes primary access evidence. [Frozen candidates/probes](phase4a_source_probe_manifest.json) bounded this pass to three surfaces and36 starts including retries. Six starts were used, with two tiny samples and existing SEC archive reuse. No broad corpus was necessary.

Recommendation: **{m['recommendation']}**, SEC preferred for planning; Federal Register conditional; ClinicalTrials current-version route not ready. Hard gates have planning-level plausible evidence for SEC only, not execution certificates. No mechanism or future hypothesis has been selected. A positive source direction does not approve source scale-up, full acquisition, new policy, real inference, EXP006, prices or performance.

Phase4B verdict: **KEEP_PHASE4B_LATER**. Identity/relationship fields could be standardized later (accession-filer-version; agency-document; study-sponsor/collaborator; issuer-security/class spans). Source/version/denominator/public-timing gaps precede a graph; these probes do not justify ADVANCE_PHASE4B_PILOT or BUILD_MINIMAL_ENTITY_SPINE_FIRST. Phase4C remains dedicated to causal claims. Predictive studies can instead evaluate conditional forecasting against a predeclared benchmark, while preserving PIT, population, identity, dependence, cost/trial and execution gates.

Minimum evidenced reusable gap: versioned source-level filing-denominator receipts. SEC documentation explicitly warns of PAC/deletion and rebuilt index differences; ClinicalTrials current modules cannot replay prior versions; Federal Register's original/correction lineage is unproved. Reuse existing archives, hash/receipt registries, source contracts, Store/stage controls and proof compiler concepts. Do not build a generalized platform or weaken frozen proofs.

**Exact next owner decision:** authorize or decline one bounded SEC filing-denominator/PAC/availability prototype, with explicit form/date/sample/request ceilings and no prices/performance, followed by separate review of one predictive mechanism direction. Design approval, source scope, timing assumptions, experiment registration/freeze and performance remain distinct decisions. No further acquisition is authorized by this recommendation.
'''
    if 'SEC' in preferred:mechanism_allowed(next(r for r in m['surfaces'] if r['id']=='SEC'),'PREDICTIVE')
    else:mechanisms='# Mechanism directions deferred\n\nNo source passes plausible hard gates; no mechanism direction is proposed.\n'
    for name,text in {'phase4a_researchability_report.md':md,'phase4a_mechanism_directions.md':mechanisms,'phase4a_architecture_decision.md':architecture}.items():
        p=DOCS/name
        if check:
            if not p.exists() or p.read_text(encoding='utf-8')!=text:raise ValueError('Source-first report mismatch: '+name)
        else:p.write_text(text,encoding='utf-8',newline='\n')
    return m['recommendation']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--audit',action='store_true');a=p.parse_args()
    if a.audit:print('Archived starts/body audit:',audit())
    print('Source-first report:',report(a.check))
