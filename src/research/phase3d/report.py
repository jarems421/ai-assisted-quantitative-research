"""Public Phase 3D report generation from small canonical artifacts; offline."""
import json
from pathlib import Path
import tempfile
from decimal import Decimal
from .proof import ROOT, compile_manifest, replay, file_hash
from .fixtures import cases, proof_fixture, tiny
from .execution import LocalReferenceAdapter,NexusAdapter,reconcile_outputs
from src.research.spec import digest

DOCS=ROOT/'docs/acceleration'


def self_check():
    ledgers={}
    expected={'ordinary':['1000','1100','1050'],'dividend':['1000','1150','1100'],
              'split':['1000','1000','1000'],'rename':['1000','1100','1050'],'cash_acquisition':['1000','1250','1250']}
    for name,fixture in cases().items():
        out=LocalReferenceAdapter().execute(fixture)
        if [Decimal(r['nav']) for r in out['nav']]!=list(map(Decimal,expected[name])):
            raise ValueError('Independent hand-accounting mismatch')
        reconcile_outputs(out,LocalReferenceAdapter().execute(fixture))
        ledgers[name]={'input_sha256':out['input_sha256'],'receipt_sha256':out['receipt_sha256'],
                       'nav':out['nav'],'action_count':len(out['action_ledger'])}
    bad=cases()['cash_acquisition']; bad['events']=[]
    unresolved=cases()['cash_acquisition']; unresolved['events'][0]['status']='UNRESOLVED'
    failures={}
    for name,adapter,fixture in [('disappearance',LocalReferenceAdapter(),bad),
                                 ('unresolved_terminal',LocalReferenceAdapter(),unresolved),
                                 ('disabled_nexus',NexusAdapter(),tiny())]:
        try: adapter.execute(fixture)
        except ValueError as error: failures[name]={'input_sha256':digest(fixture),'status':'EXPECTED_REJECTION','reason':str(error)}
        else: raise ValueError('Unsafe fixture accepted: '+name)
    with tempfile.TemporaryDirectory() as tmp:
        spec,authority=proof_fixture(tmp)
        manifest,path=compile_manifest(spec,tmp,Path(tmp)/'manifests',authority=authority)
        verified=replay(path,tmp,authority=authority)
    return {'version':'phase3d_synthetic_spine_receipt_v001','ledgers':ledgers,
            'proof_replay':verified,'manifest_code_commit':manifest['code_commit'],
            'manifest_code_hashes':manifest['code_hashes'],'environment_sha256':digest(manifest['environment']),
            'expected_failure_receipts':failures,
            'exact_output_reproducibility':'Fixture arithmetic only; not a real source or remote-engine certificate',
            'nexus_adapter':'DISABLED_NO_TRANSPORT','temporary_EXP999_only':True}


def evidence():
    prior=json.loads((DOCS/'phase3c_evidence.json').read_bytes())
    census=json.loads((DOCS/'phase3d_source_census.json').read_bytes())
    calibration=json.loads((DOCS/'phase3d_inference_calibration.json').read_bytes())
    gates={'REVENUE_CANONICALIZATION':'PARTIAL','ACCOUNTING_PERIMETER_CERTIFICATION':'BLOCKED',
           'HISTORICAL_SECURITY_IDENTITY':'PARTIAL','CORPORATE_ACTION_LIFECYCLE':'PARTIAL','TERMINAL_VALUE_EVIDENCE':'BLOCKED',
           'PUBLIC_ELIGIBILITY_POLICY':'READY_FOR_OWNER_REVIEW','INFERENCE_IMPLEMENTATION':'BLOCKED',
           'HISTORICAL_UNIVERSE_FEASIBILITY':'BLOCKED','PROOF_COMPILER':'PASS_SYNTHETIC_ONLY',
           'MANIFEST_REPLAY':'PASS_EXACT_INPUT_BYTES_SYNTHETIC','LOCAL_EXECUTION_ROUTE':'PARTIAL_SYNTHETIC_VERIFIED',
           'NEXUS_ADAPTER_INTERFACE':'DEFINED_DISABLED','NEXUS_EXECUTION':'BLOCKED','EXP005_FREEZE_READINESS':'NOT_READY'}
    inputs={p:file_hash(DOCS/p) for p in ('phase3c_evidence.json','phase3d_revenue_contract.json',
             'phase3d_identity_contract.json','phase3d_inference_protocol.json','phase3d_inference_calibration.json',
             'phase3d_source_census.json','phase3d_execution_contract.json','phase3d_experiment.schema.json','phase3d_spine_receipt.json')}
    return {'version':'phase3d_evidence_v001','as_of':'2026-10-12','baseline_git_sha':'da35f25',
            'input_hashes':inputs,'gates':gates,'source_cases':prior['cases'],'originals':census['original_denominator'],
            'three_original_denominator':prior['revenue_metrics']['three_originals'],
            'canonical_candidate_presence_upper_bound':census['concept_presence_upper_bound_triples'],
            'certified_triples':census['fully_certified_triples'],'real_identity_spans':prior['identity_metrics']['sufficient_span_count'],
            'real_terminal_certificates':prior['identity_metrics']['terminal_certified_count'],
            'timing_invariant':sum(r['status']=='INVARIANT' for r in prior['timing']),
            'availability_policy_sha256':prior['policy_sha256'],'owner_decision':'PENDING_NOT_APPROVED',
            'exact_public_availability':'UNKNOWN','inference_selected_method':calibration['selected_method'],
            'synthetic_replicates_per_world':400,'new_source_requests':{k:0 for k in ('SEC','OpenFIGI','Tiingo','FMP','Orbis','Nexus')},
            'documentation_browser':{'tool_calls':1,'search_queries':2,'source_dataset_requests':0},
            'prior_phase3c_request_counts':prior['request_counts'],'real_acceleration_or_performance_computed':False,
            'EXP004':'OPERATIONALLY_PAUSED','EXP005':'ABSENT_NOT_REGISTERED_NOT_FROZEN','stopped_before':'PHASE4A',
            'limitations':['Synthetic proofs are not real scientific certificates','No source/calendar/execution universe certificate',
                          'No full backfill or independent remote-engine reconciliation','Existing stage ledger real EXP005 adapter still required']}


def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join('---' for _ in headers)+' |',
                       *['| '+' | '.join(str(v) for v in row)+' |' for row in rows]])


def render(e):
    gates=table(['Gate','Verdict'],e['gates'].items())
    validation=DOCS/'phase3d_validation.json'
    checks=json.loads(validation.read_bytes()) if validation.exists() else {}
    test_text=f"{checks['tests_passed']} tests passed; {checks['tests_skipped']} skipped." if 'tests_passed' in checks else 'Final validation pending; no unexecuted check claimed.'
    calibration=json.loads((DOCS/'phase3d_inference_calibration.json').read_bytes())
    caltable=table(['World','Annual raw rejection / location coverage','Funded-window raw rejection / location coverage'],
        [(name,*[f"{r['raw_rejection']:.1%} / {r['location_coverage']:.1%}" for r in calibration['rows'] if r['world']==name])
         for name in dict.fromkeys(r['world'] for r in calibration['rows'])])
    documents={
    'phase3d_report.md':f'''# Phase 3D: certification closure and independent research spine

**Infrastructure verified on synthetic fixtures; EXP005 remains NOT_READY.** As of {e['as_of']}. The [governing roadmap](master_plan.md) is now active. Earlier phase reports, freezes, negative results and original archives remain historical evidence. No real revenue acceleration, momentum, strategy returns or new experiment was computed.

The bounded offline census examined all {e['originals']} existing original annual filings across the fixed 30 revenue candidates. {e['canonical_candidate_presence_upper_bound']}/{e['three_original_denominator']} discovered three-original candidates have one or more permitted revenue-line candidates throughout. This is an upper bound on tag presence, **not** {e['canonical_candidate_presence_upper_bound']} comparable chains: statement location, tax treatment, recognition basis and consolidation perimeter still require evidence-linked review. Fully certified triples remain {e['certified_triples']}. [Revenue contract](phase3d_revenue_contract.md) preserves the original single-concept failure and permits only separately reviewed mappings.

The minimal compiler validates hash-linked contracts, separately supplied synthetic authority, mandatory gates, source bounds and stage restrictions; it emits immutable manifests and verifies exact input replay. The local Decimal ledger reconciles hand-accounted buy/hold/sell, dividend entitlement/payment, split, rename and acquisition fixtures. Missing population identities, price rows and terminal terms fail closed. These are scoped software results; real scientific certificates and the real stage/selection adapter remain incomplete. [Execution details](phase3d_execution_reference.md) distinguish the implemented spine from production certification. Nexus has a disabled interface and no transport.

Both frozen inference candidates were evaluated on known synthetic worlds. Neither can satisfy the four-effect Holm power gate with six annual or two funded-window clusters; no replacement was selected. Calibration also exposes dependence/coverage limitations. The original Phase 3C failure is preserved. [Inference revision](phase3d_inference_revision.md) records the exact protocol, all results and finite-sample limit.

{gates}

Exact public availability stays UNKNOWN. The 89-filing clock-invariance result remains evidence of calendar mechanics, not resolution of SEC summer timestamps. The [availability decision](phase3d_availability_decision.md) is pending explicit owner approval, rejection or amendment. Approval alone cannot certify identity, universe, terminal values or execution.

New source requests: SEC 0, OpenFIGI 0, Tiingo 0, FMP 0, Orbis 0, Nexus 0. Two browser queries in one documentation-tool call reviewed primary accounting/randomization references; no filing or market dataset was acquired. Prior Phase 3C request totals remain separately recorded. Original Intel failure and prefix-retention gap remain intact. Reading utilities were installed only under ignored `.research/pdf-reader`; research dependency pins are unchanged.

Validation: **{test_text}** [Validation receipt](phase3d_validation.json) records executed checks and preservation. [Canonical evidence](phase3d_evidence.json), [source census](phase3d_source_census.json), [synthetic ledgers](phase3d_spine_receipt.json) and [gate review](phase3d_gate_review.md) provide deeper detail. Report generation needs public artifacts only; source census verification requires private archived instances.

```sh
python -m src.research.phase3d check
python -m src.research.phase3d review --check
python -m src.research.phase3d report --check
python -m unittest discover -s tests -v
```

EXP004 remains paused; EXP005 is absent. No Validation/Test opening, Nexus/Aurora/support operation, purchase, Orbis scraping, optimization, paper/live action, full backfill, graph or causal platform occurred. **Stopped at the Phase 3D owner decision and unresolved scientific gates; Phase 4A requires separate authorization.** Certification closure remains incomplete even though this bounded implementation checkpoint is delivered. Commit/push receipts are in Git history and the delivery message.
''',
    'phase3d_gate_review.md':f'''# Phase 3D gate review

{gates}

Software fixture passes do not make real population certification pass. Mandatory accounting/perimeter, historical listing spans, terminal consideration, complete universe/calendar, approved modeled eligibility, usable inference and population-preserving execution remain missing. No EXP005 freeze or performance authorization is inferred.

Next decisions: review the [availability packet](phase3d_availability_decision.md); decide separately whether to commission bounded primary accounting/listing/terminal review or an independently audited source with sufficient coverage. Inference needs another reviewed pre-performance design because this two-method family cannot reach the existing confirmation gate. Do not extend sample windows, relax Holm, change thresholds or choose a new method automatically. Full-market acquisition and Phase 4A remain unauthorized.

The [report](phase3d_report.md) states exact scope, checks and zero new dataset requests. Historical records and failures are preserved.
''',
    'phase3d_revenue_contract.md':f'''# Phase 3D canonical revenue candidate

[RevenueContract_v002](phase3d_revenue_contract.json) is a versioned source-only candidate, committed before real signal computation (none occurs). The prior exact-element contract and its 0/29 certified result remain unchanged. V002 permits three named mapping candidates: RevenueFromContractWithCustomerExcludingAssessedTax, SalesRevenueNet and Revenues. Each needs an exact observation hash plus original/primary source hashes, element and statement locators, explicit review identity/reason/time/version, accounting basis and perimeter. No concept is automatically preferred or equivalent; financial/nonoperating components, assessed-tax changes and revenue recognition transitions can invalidate mapping.

The [FASB revenue implementation guide](https://xbrl.fasb.org/impguidance/Rev2_TIG/Revenue.htm) distinguishes revenue from customer contracts and other revenue categories. Its examples motivate caution; current guidance is not a historic taxonomy-vintage certificate. Deterministic mapping and explicit reviewed exceptions replace informal judgment. Synthetic tests reject segments, instant/stub periods, extensions, scale/statement failures, recasts, changed observations and incompatible perimeters. Comparatives have a separate period role and remain later-accession evidence, never substitute earlier originals.

The source census is a narrow inspection of already archived XBRL bytes, not a new financial parser. It verifies archive hashes, annual current-period nondimensional USD contexts and exact allowed concept names. It does not select a line, reconcile a new line through EdgarTools/Inline statements or certify accounting scope. All 89 originals and all 30 candidates remain in the denominator; {e['canonical_candidate_presence_upper_bound']}/29 have candidate presence throughout, zero certified chains. The 60-case frame remains selected feasibility evidence, not a representative US universe. Missing reviews and source gaps are explicitly unresolved. No acceleration series, ranking, new date window or expanded economic family exists.
''',
    'phase3d_identity_certification.md':f'''# Phase 3D historical identity certification

[Identity contract](phase3d_identity_contract.json) requires issuer → class → venue/ticker → stable ID with half-open effective intervals and independently trusted start/end evidence. Multiple classes and ticker reuse remain distinct. Tests reject overlaps and untrusted endpoints; boundary instants select the next interval without rewriting prior state.

The existing 60-case [identity matrix](phase3c_identity_lifecycle.md) remains the source evidence. Current OpenFIGI candidates and filing cover points cannot establish full listing intervals. Real complete listing-span certificates remain {e['real_identity_spans']}/60; no ambiguous case was removed or replaced. Existing 8-A/25 and merger documents contain useful partial evidence, but some refer to unrelated preferred classes or a surviving issuer. No new requests or owner Orbis login occurred. A separately bounded primary-document/independent listing endpoint review is still necessary; this model is not itself an authoritative identity database.
''',
    'phase3d_terminal_value.md':f'''# Phase 3D lifecycle and terminal value

Canonical event receipts carry class/security ID, effective time, original source hash/locator, reviewer/time and independently trusted decision. Cash consideration needs currency/payment timing; stock conversion needs ratio and dated successor binding; spinoff needs distribution terms; cancellation needs explicit recovery evidence. Mere delisting, bankruptcy or a final price cannot establish zero. OTC continuation, elections/proration, cash-in-lieu, contingent recoveries and deferred distributions stay unresolved until modeled and evidenced.

Synthetic ledgers prove no silent disappearance for held and unheld identities, cash merger accounting, stock conversion, explicit evidenced cancellation, dividends and splits. The engine refuses unresolved transitions and missing prices. Review supports a spinoff receipt model, but the v001 engine deliberately rejects spinoff execution and other unsupported events. Corporate-action evidence and mechanical execution are separate gates.

Existing ten merger-document sets remain PARTIAL. Real terminal class/position certificates remain {e['real_terminal_certificates']}; no guessed amounts, terminal NAV, assumed cash election or immortal last-price marks were introduced. See [source evidence](phase3c_identity_lifecycle.md) and [execution contract](phase3d_execution_contract.json). Terminal-value evidence for a real universe stays BLOCKED.
''',
    'phase3d_availability_decision.md':f'''# Phase 3D availability decision packet

**PENDING OWNER DECISION; NOT APPROVED.** Proposed pilot policy is unchanged: `phase3c_ambiguity_buffer_v002`, hash `{e['availability_policy_sha256']}`, scope 2015-01-01–2021-12-31. Its canonical object is `policy` in [Phase 3C evidence](phase3c_evidence.json); [the original packet](phase3c_availability_review.md) remains immutable.

At 09:30 America/New_York on the second exchange session strictly after the later of official filing date and acceptance civil date under each plausible UTC interpretation, allow modeled eligibility only if all candidate opens equal the raw-rule open and occur after every candidate instant. Fail closed on missing/contradictory timing, non-invariance, unsupported calendars or contrary public evidence. Contributor, semantic and class gates remain independent.

All {e['timing_invariant']}/89 existing annual originals pass the pinned calendar-mechanics probe. Summer literal EST vs seasonal ET acceptance remains PARTIAL; exact first-public time remains UNKNOWN. The calendar is not independently exchange-certified for a full population. This rule expresses a conservative modeling assumption, not guaranteed dissemination or an observed timestamp. It does not authorize 2022+ data or implement the conditional 2021–2032 experiment design.

| Owner choice | Tradeoff |
| --- | --- |
| Approve this exact pilot modeling policy/hash/scope | Permits a later separately certified modeled view; accepts residual dissemination uncertainty; does not approve EXP005 or execution |
| Reject; require observed channel-specific availability | Stronger observational standard, but current sources cannot supply exact first-public times |
| Amend or defer | Specify a different buffer/channel/scope; preserve this version and independently test any replacement before use |

An approval must explicitly reference the policy hash and pilot scope, accept modeled timing with observed public time UNKNOWN, and be archived as owner evidence with a new versioned decision receipt. No approval writer or real eligibility activation runs here. Under the owner plan §§A5/16, “The owner must explicitly approve, reject or amend the policy.” We stop at this decision rather than decide on the owner's behalf.
''',
    'phase3d_inference_revision.md':f'''# Phase 3D inference revision: no replacement selected

**BLOCKED for the proposed confirmation design.** [Protocol](phase3d_inference_protocol.json) was committed at `8067219`; implementation `5824c96` and a private hashed freeze receipt preceded evaluation. Two exact cluster-sign candidates, fixed seed3003002, 400 replications/world, ten worlds and three four-effect dependence structures were predeclared. No real return series entered. All candidates/results remain in [calibration evidence](phase3d_inference_calibration.json); the Phase 3C bootstrap failure stays unchanged.

{caltable}

Raw size, Wilson Monte Carlo intervals, four-effect family size/power and common-location inversion coverage are reported separately. Independent, fully correlated and mixed common-shock family structures all have zero Holm rejections for both candidates, including the positive effect world. This reflects discreteness and weak power, not universal robustness: six annual clusters have minimum one-sided p=1/64, above Holm's first threshold0.0125; two funded-window clusters have minimum p=1/4. A four-effect positive-world lower power bound>=0.50 is impossible. There is no selected method.

Exact randomization requires group invariance, not merely zero expected mean. See [Berkeley's paired randomization notes](https://www.stat.berkeley.edu/~stark/Teach/S240/Notes/ch6.htm). Observational strategy/control labels are not randomized; cluster symmetry and independence require scientific justification. Persistent, overlapping, heterogeneous-shift and skewed worlds challenge those assumptions. Confidence sets invert a common additive location test; they do not certify an arbitrary heterogeneous paired-mean estimand. Funded-window two-sided sets are unbounded at95%; no invented finite interval is reported. Exhaustive sign tests additionally verify nominal size over a fixed symmetric six-cluster orbit.

No constants were tuned after calibration; no calendar or Holm family was relaxed. The 45-performance ceiling, original economic hypothesis and conditional windows remain planning history. Another method or longer confirmation design requires a separately frozen pre-performance revision and owner review; this outcome authorizes none automatically.
''',
    'phase3d_execution_reference.md':'''# Phase 3D proof compiler and local reference execution

[Experiment schema](phase3d_experiment.schema.json) and [execution contract](phase3d_execution_contract.json) describe the minimal engine-independent spine. `proof.py` reuses canonical hashes and immutable JSON storage; `execution.py` reuses exact population reconciliation and UTC parsing. The compiler does not create a new warehouse, DSL, experiment registry or stage journal.

The schema can describe a future research ID with hypothesis, population, source snapshots, signal, identity, eligibility, execution, costs, inference and trial family. This implementation accepts only synthetic EXP999/DRAFT with separately supplied synthetic authority; real compilation remains denied pending the existing Store/selection/stage adapter and real scientific certificates. Unapproved policy, unresolved gate/terminal state, missing contract, changed hash, future source or illegal stage fails. Manifest code file hashes and package/environment fingerprints distinguish a dirty code state from its parent Git SHA. No performance is executed; execution/statistical receipt slots are null.

Replay verifies the immutable manifest, referenced input bytes, authority, contracts/gates, current code hashes and environment. A relaxed environment check reports incompatibility; it cannot claim exact outputs. Historical input verification is distinct from bit-for-bit numeric outputs and from cross-engine semantic reconciliation. Local owner control of files remains outside this application-level trust boundary.

The local engine uses Decimal34, exact strings, fractional long-only shares and immediate synthetic settlement. It processes explicitly ordered lifecycle events, dividend entitlement/receivables/payment, exhaustive decision observations, descending ranking with stable-ID ties, sales then buys, actual traded-notional fees, cash and complete close NAV. Insufficient cash fails rather than silently rescaling. Missing/unheld population identities fail as well as missing held prices. The event model supports split, dividend, cash/stock merger and evidenced cancellation; unsupported spinoff/OTC/deferred-recovery mechanics fail explicitly.

Hand-verifiable fixtures start at USD1000: a50-share buy at10, hold at12 and sale at11 yields NAV1000/1100/1050 without fees; USD1 dividend entitlement adds50 before later payment; a2:1 split and price5 preserves NAV1000; rename preserves stable identity; cash acquisition at15 yields1250. Separate tests cover stock conversion, fees, no-cash scaling, unavailable events, overlaps, future signals and equal-count substitutions. [Synthetic receipts](phase3d_spine_receipt.json) are accounting fixtures, not strategy performance.

`ExecutionAdapter` exposes `execute(input)->output`. The disabled `NexusAdapter` always raises and has no client/transport. Reconciliation compares every population, observation, order/fill, cash/action, position and NAV field exactly, including warnings/errors/input hash; engine metadata may differ. No tolerance or omitted field is silently accepted. No independent real/Nexus comparison has run.

This spine is implemented; real LOCAL_EXECUTION_ROUTE remains PARTIAL. Calendar/source completeness, lifecycle coverage, market microstructure/cost feasibility, proof-result binding and stage-safe real selection need further certification. It cannot resume EXP004 or run EXP005.
'''}
    return documents


def generate(*,check=False):
    e=evidence(); summary={k:v for k,v in e.items() if k not in ('input_hashes','prior_phase3c_request_counts')}
    outputs={'phase3d_evidence.json':json.dumps(e,sort_keys=True,indent=2)+'\n',
             'phase3d_summary.json':json.dumps(summary,sort_keys=True,indent=2)+'\n',**render(e)}
    for name,content in outputs.items():
        path=DOCS/name
        if check:
            if not path.exists() or path.read_text(encoding='utf-8')!=content: raise ValueError('Report stale: '+name)
        else: path.write_text(content,encoding='utf-8',newline='\n')
    return len(outputs)
