"""Continuation reports from bounded source review and frozen synthetic evidence."""
from collections import Counter
from datetime import date
import json
from src.research.phase3d.proof import ROOT,file_hash
from src.research.phase3d.approval import approved_pilot
from src.research.inference_feasibility import inference_design_gate
from src.research.spec import digest
from .accounting import DOCS


def geometry():
    from src.nexus.process_exp001 import session_dates
    sessions=sorted(session_dates(date(2015,1,1),date(2021,12,31)))
    months=Counter(d.strftime('%Y-%m') for d in sessions)
    return {'scope':['2015-01-01','2021-12-31'],'sessions':len(sessions),'monthly_decisions':len(months),'years':7,
            'sessions_per_month':dict(months),'eligible_issuers_certified':0,
            'calendar_source_sha256':file_hash(ROOT/'src/nexus/process_exp001.py'),
            'confirmation_toy':{'funded_windows':2,'months_per_window':36,'monthly_units':72,'daily_units':1512},
            'status':'CALENDAR_GEOMETRY_ONLY_NOT_EFFECTIVE_SAMPLE_OR_EXCHANGE_CERTIFICATE',
            'conditional_phase3b_dates':'Unchanged/unactivated; no2022+ calendar or market observations inspected'}


def summary():
    a=json.loads((DOCS/'phase3d_accounting_review.json').read_bytes())
    i=json.loads((DOCS/'phase3d_identity_closure.json').read_bytes())
    t=json.loads((DOCS/'phase3d_terminal_closure.json').read_bytes())
    cal=json.loads((DOCS/'phase3d_inference_calibration_v002.json').read_bytes())
    approved_pilot(DOCS)
    gates={'REVENUE_CANONICALIZATION':'PARTIAL','ACCOUNTING_PERIMETER_CERTIFICATION':'BLOCKED',
           'HISTORICAL_SECURITY_IDENTITY':'PARTIAL','CORPORATE_ACTION_LIFECYCLE':'PARTIAL','TERMINAL_VALUE_EVIDENCE':'BLOCKED',
           'PUBLIC_ELIGIBILITY_POLICY':'OWNER_APPROVED_PILOT_NOT_ACTIVATED','INFERENCE_RESOLUTION_FEASIBILITY':'MATHEMATICALLY_FEASIBLE_NEW_METHODS',
           'INFERENCE_IMPLEMENTATION':'BLOCKED','HISTORICAL_UNIVERSE_FEASIBILITY':'BLOCKED','PROOF_COMPILER':'PASS_SYNTHETIC_ONLY_WITH_FEASIBILITY_GUARD',
           'MANIFEST_REPLAY':'PASS_SYNTHETIC_WITH_SEPARATE_GIT_AND_CODE_CHECKS','LOCAL_EXECUTION_ROUTE':'PARTIAL_SYNTHETIC_VERIFIED',
           'NEXUS_ADAPTER_INTERFACE':'DEFINED_DISABLED','NEXUS_EXECUTION':'BLOCKED','EXP005_FREEZE_READINESS':'NOT_READY'}
    hashes={n:file_hash(DOCS/n) for n in ('phase3d_accounting_review.json','phase3d_identity_closure.json','phase3d_terminal_closure.json',
             'phase3d_inference_protocol_v002.json','phase3d_inference_calibration_v002.json','availability_policy_v002_approved.json')}
    return {'version':'phase3d_closure_summary_v001','baseline':'7f89155','as_of':'2026-10-12','gates':gates,'inputs':hashes,
            'originals':89,'issuer_denominator':30,'three_original_candidates':29,'frame_cases':60,
            'revenue_observations':a['observations'],'current_revenue_observations':a['current_observations'],
            'primary_rendering_matches':a['primary_rendering_reconciled'],'scoped_tax_reviews':len(a['scoped_disclosure_reviews']),
            'certified_triples':a['full_certified_triples'],'identity_status_counts':i['status_counts'],'certified_full_spans':0,
            'disclosed_lifecycle_claims':t['reviewed_disclosed_claims'],'certified_terminal_position_cases':0,'nav_capable_paths':0,'incomplete_frame_paths':60,
            'outside_cutoff_documents_not_read':i['outside_cutoff_documents'],'selected_inference_method':cal['selected_method'],
            'source_requests':{k:0 for k in ('SEC','OpenFIGI','Tiingo','FMP','Orbis','Nexus')},
            'documentation_activity':'Two primary-method searches, primary-paper/docs browser reads, two public action-tag Git lookups; separate from source data ledgers',
            'availability':'Exact approved hash/scope retained; observed public time UNKNOWN; no real modeled view activated',
            'real_signals_or_performance_computed':False,'EXP004':'PAUSED','EXP005':'ABSENT_NOT_READY','next_phase_started':False,
            'ci_scope':'Public whitelist only; package installation allowed; source network/private reads denied; hosted status requires separate observation'}


def resolution(cal):
    base={'alpha':.05,'family_size':4,'sample_units':72,'minimum_units':24,'power_required':.5}
    old={name:inference_design_gate(dict(base,method='exact_sign',clusters=n,power_lower=0)) for name,n in [('annual_cluster_sign',6),('funding_window_sign',2)]}
    current={}
    for method in ('monthly_hac12','monthly_studentized_circular12'):
        rows=[r for r in cal['rows'] if r['method']==method and r['world']=='positive02']
        lower=min(r['primary']['wilson95'][0] for r in rows)
        current[method]=inference_design_gate(dict(base,method='asymptotic' if method=='monthly_hac12' else 'bootstrap',draws=1999,power_lower=lower))
    return {'version':'inference_resolution_v001','old_designs':old,'current_designs':current,'calendar_geometry':geometry(),
            'candidate_calibration_gates':cal['candidate_verdicts'],'method_selection':None,
            'distinction':'Minimum-p resolution is possible; adequate power/calibration and real weak-dependence assumptions are separate gates'}


def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join('---' for _ in headers)+' |',
                       *['| '+' | '.join(map(str,row))+' |' for row in rows]])


def generate(check=False):
    s=summary();cal=json.loads((DOCS/'phase3d_inference_calibration_v002.json').read_bytes());r=resolution(cal)
    gate_table=table(['Gate','Verdict'],s['gates'].items())
    identity_counts=', '.join(f"{count} {status.lower().replace('_',' ')}" for status,count in s['identity_status_counts'].items())
    null_table=table(['World / independent four-effect family','HAC raw / any Holm rejection / coverage','Bootstrap-t raw / any Holm rejection / coverage'],
        [(world,*[f"{x['raw']['fraction']:.1%} / {x['family']['fraction']:.1%} / {x['covered']['fraction']:.1%}" for x in cal['rows'] if x['world']==world and x['structure']=='independent'])
         for world in dict.fromkeys(x['world'] for x in cal['rows'])])
    validation=DOCS/'phase3d_closure_validation.json'
    power_table=table(['Annual effect (points)','HAC primary Holm power range','Bootstrap-t primary Holm power range'],
        [(effect,*[f"{min(x['primary']['fraction'] for x in cal['rows'] if x['method']==method and x['world']==world):.1%}–{max(x['primary']['fraction'] for x in cal['rows'] if x['method']==method and x['world']==world):.1%}"
                  for method in ('monthly_hac12','monthly_studentized_circular12')])
         for effect,world in [(2,'positive02'),(5,'positive05'),(10,'positive10'),(25,'positive25')]])
    v=json.loads(validation.read_bytes()) if validation.exists() else {}
    test_line=f"{v['tests_passed']} full local tests passed, {v['tests_skipped']} skipped; {v['public_tests_passed']} public/synthetic tests passed." if v else 'Final validation pending.'
    texts={
    'phase3d_closure_report.md':f'''# Phase 3D closure continuation

**Better source evidence; EXP005 remains NOT_READY.** As of 2026-10-12. The original Phase 3D checkpoint, old calibration failures, RevenueContract_v002, frozen frame and policy approval remain unchanged. [Implementation plan](phase3d_closure_plan.md) and [gate review](phase3d_closure_gate_review.md) define this bounded continuation.

All 89 existing originals for 30 revenue candidates were processed into source-review packets, including every one of the 29 discovered triples. The workflow retains {s['revenue_observations']} original annual revenue observations ({s['current_revenue_observations']} current-year observations) and {s['primary_rendering_matches']} Inline rendering matches. These include repeated/equivalent facts and comparisons, not unique economic lines. Two explicit 2020 assessed-tax disclosures—Apple and Microsoft—are reviewed at their original source locators. None establishes three-year economic-line, recognition or perimeter comparability; full certified triples remain 0/29. [Accounting review](phase3d_accounting_review.json) records each chain and exclusion category. Unreviewed note hits never create trusted full receipts.

The 60-case identity frame retains {identity_counts}. Tiffany's source explicitly reports common-stock NYSE suspension before the 2021-01-07 open; that is a partial end boundary, not a complete stable-ID span or the legal listing-removal instant. Six source-grounded lifecycle reviews distinguish USD 42 Whole Foods consideration, USD 131.50 Tiffany consideration, Celgene cash/stock/CVR, Alexion cash/ADS/election, Viacom class-specific conversion/fractional cash, and CBS as surviving issuer. Full terminal position certificates and complete NAV-capable paths remain 0. Cash amounts are disclosed consideration, not realized portfolio cash. Payment timing, excluded-holder treatment, successor/class bridges and listing starts remain missing. [Identity](phase3d_identity_closure.json) and [terminal](phase3d_terminal_closure.json) evidence retain every failed/unresolved case.

The source boundary excludes bodies for {s['outside_cutoff_documents_not_read']} existing post-2021 lifecycle documents; their metadata remains visible as out-of-scope evidence, and no case is dropped. No extra filing, price or identifier acquisition occurred. No Orbis or Nexus operation occurred. Source request counts: SEC 0 / OpenFIGI 0 / Tiingo 0 / FMP 0 / Orbis 0 / Nexus 0. Method documentation/action-tag lookups are recorded separately and are not source data acquisitions.

The new frozen monthly HAC/studentized circular-block candidates resolve the old minimum-p impossibility while retaining Holm across four formal effects. Resolution alone cannot establish calibration or power. [Design and calibration](phase3d_inference_design_v002.md) retain all null, positive/negative and dependence results. No method is selected; no real strategy returns or signal values enter inference. The daily arithmetic paired estimand is preserved in the equal 21-session synthetic geometry; calendar-weighted real-month implementation is still a prerequisite, not silently replaced by equal-month real inference.

{gate_table}

The compiler now refuses impossible minimum-p or unsupported declared power designs. Replay reports `git_commit_exact` separately from `relevant_code_hashes_exact`; changed relevant code still fails. Synthetic EXP999 remains the only accepted compile mode. Local Decimal execution and disabled Nexus adapter are preserved. Public CI runs a fixed synthetic whitelist with private reads and external network blocked; it does not certify sources, calibration, real execution or the full private integration suite.

**Validation:** {test_line} [Receipt](phase3d_closure_validation.json). Prior artifacts are hash-checked, and historical Phase 3D reports are not regenerated. Public summaries/reports need no private data; replaying source review requires original ignored bodies and cached parser receipts.

```sh
python -m src.research.phase3d.closure report --check
python -m src.research.phase3d.closure sources --check
python -m src.research.public_checks
python -m unittest discover -s tests -v
```

The existing 2015–2021 policy approval is reused without renewed approval; observed public availability stays UNKNOWN and no real eligibility view is activated. EXP004 remains paused and EXP005 absent. No acceleration, momentum, Sharpe/Sortino/drawdown, strategy return, optimization, sealed-stage opening, new experiment, paper/live action, graph, causal platform or Phase 4A occurred. **Stop after this continuation.** Remaining work is source-linked full accounting reviews, independently dated class/listing and complete terminal/payment evidence, and a separately reviewed inferential remedy if calibration/power fails. Do not weaken gates, extend dates or acquire a full market automatically.
''',
    'phase3d_closure_gate_review.md':f'''# Phase 3D closure gate review

{gate_table}

Resolution feasibility means the method can theoretically reach the declared threshold; it is not inferential validity. Full-source and execution prerequisites still fail. The selected frame is feasibility evidence, not a certified historical universe:60 candidates, 0 full spans, 0 complete terminal contracts, 0 complete NAV paths, 60 incomplete paths. No denominator loss is hidden. Owner policy approval is already recorded; do not ask again.

Scientific blockers remain: statement/line/scale and three-original accounting/perimeter review, listing-effective intervals and stable class bridge, payment/successor/contingent-recovery terms, adequate finite-sample calibrated paired inference, complete population/calendar coverage and certified execution. Phase 4A requires separate owner authorization after actual readiness; no artifact here registers or freezes EXP005.
''',
    'phase3d_inference_design_v002.md':f'''# Phase 3D inference redesign and finite-sample power

The revised [protocol](phase3d_inference_protocol_v002.json) and candidate code were frozen at 0c683a1/87593c0 before evaluation. The old protocols/results remain unchanged. This revision starts from 252×mean aligned daily net candidate-minus-momentum return differences. Cross-sectional dependence is aggregated inside the paired portfolio tape; repeated issuers, annual reporting shocks and rebalancing can still produce serial dependence. Monthly paired means model 21-session intervals; two 36-month funded windows avoid crossing funding boundaries. Real unequal-month weights are not implemented or certified by this synthetic comparison.

We retained four one-sided Holm hypotheses at 0.05. Cost/delay effects are robustness claims about one mechanism, but the prior design required formal support for each. Deleting them merely to improve power would weaken that promise. Positivity and the 2-point economic materiality rule remain separate; no outcome is rescued by a one-endpoint hierarchy.

Methods: Bartlett HAC 12 with intercept finite-sample correction and asymptotic normal reference, and within-window circular 12-month studentized bootstrap-t with the same HAC standard error, 1999 draws and seed 3003003. A fixed annual bandwidth reflects filing persistence, not a search-selected interval. Only 36 months/window makes its finite-sample approximation fragile. [Official HAC documentation](https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_hac.html) assumes consecutive equally spaced time periods; [block-bootstrap coverage research](https://arxiv.org/abs/0804.4361) explains why studentization is substantive, not an automatic validity guarantee. The implementation is a small transparent intercept kernel, not a new econometrics framework or an asserted reproduction of every paper method.

{null_table}

Raw rejection and any-family Holm rejection estimate size/FWER only in null worlds; in positive alternatives they describe rejection power. Coverage targets the known mean in each world. Regime shift is a stress diagnostic, not a common-mean coverage certificate.

{power_table}

Power ranges cover all three joint structures, with uncertainty intervals retained in JSON. Both methods failed size, coverage, the +10-point screen and the +2-point materiality gate. No tested effect is a certified detectable-effect threshold because calibration failed. Interval widths and effective-month diagnostics describe these synthetic samples only.

Each world has 200 replications; three joint structures—independent, fully correlated and mixed common shocks—test FWER. Full Wilson intervals, failures, effective-month diagnostics and annual interval widths are in [calibration](phase3d_inference_calibration_v002.json). Known alternatives at 2/5/10/25 annual percentage points report detectable effects under a fixed synthetic daily noise scale 0.01, not estimated real power. Mean-CI coverage and family-power are distinct. Both interval and p-value approximations must pass their fixed gates; no primary/stress failure is omitted.

Old sign designs cannot satisfy Holm: 1/64>0.0125 and 1/4>0.0125. The new HAC reference is continuous; bootstrap minimum p = 1/2000=0.0005, so both can resolve the threshold. [Resolution artifact](phase3d_inference_resolution.json) reports independent power gates and exact source/calendar geometry: {r['calendar_geometry']['sessions']} sessions / 84 monthly decision slots in 2015–2021. The six-year confirmation toy has 72 monthly units/1512 daily units; these are counts, not 72 independent observations or a completed future calendar certificate. Eligible certified issuer count remains 0. Existing conditional Development/Validation/Test dates stay unchanged and unactivated.

Candidate decisions: `{cal['candidate_verdicts']}`. No method is selected or certified for real inference. Failure at the materiality floor indicates this noise/dependence scenario is underpowered; it does not estimate real strategy volatility or prove all possible sample designs fail. Another method, horizon, estimand or hierarchy needs a new reviewed pre-performance protocol, not a post-failure parameter tweak. The reusable compiler gate enforces minimum-p and separately supported power before any future research path can compile.
''',
    'phase3d_public_ci.md':'''# Public and synthetic CI scope

`python -m src.research.public_checks` runs an explicit whitelist of Phase 3D proof, execution, accounting-contract, approval, inference and closure-source fixture tests. The runner denies repository data, private state, historical experiment files, `.env` reads and external socket connections. It uses no source/API credential. Tests use synthetic EXP999 temporary directories and public metadata; they neither call a source service nor execute an experiment.

The GitHub Actions workflow pins official checkout/setup action commits, installs only NumPy 2.2.6/jsonschema4.26.0/tzdata2026.5 on Python 3.13/Windows, then runs that whitelist. Checkout credentials are not persisted and permissions are read-only. Normal checkout/action/package installation requires network; research tests do not. This is not the full local private suite, original-file parsing/source reconciliation, Monte Carlo calibration or a production execution certificate. Hosted status must be observed separately; local success is not a claim that GitHub has already passed.
'''}
    outputs={'phase3d_closure_summary.json':json.dumps(s,sort_keys=True,indent=2)+'\n',
             'phase3d_inference_resolution.json':json.dumps(r,sort_keys=True,indent=2)+'\n',**texts}
    for name,content in outputs.items():
        path=DOCS/name
        if check:
            if not path.exists() or path.read_text(encoding='utf-8')!=content:raise ValueError('Closure report changed: '+name)
        else:path.write_text(content,encoding='utf-8',newline='\n')
    return len(outputs)
