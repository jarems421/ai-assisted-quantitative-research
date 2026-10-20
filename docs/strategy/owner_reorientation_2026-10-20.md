# Research OS — Strategic Reorientation: From Backtesting Infrastructure to Alternative-Data Alpha Discovery

You are working in my existing quantitative research repository, Research OS:
https://github.com/jarems421/ai-assisted-quantitative-research

I am also attaching a comprehensive Deep Research report on obscure, unconventional, overlooked, and potentially under-researched financial data sources. You MUST read that report carefully. It is the primary source for identifying specific datasets, research leads, and proposed economic mechanisms. Do not assume its claims are established facts; verify the most important claims independently.

This task is a strategic research and engineering review. DO NOT start implementing a new strategy or building a large data framework until you have completed the review and presented a practical plan.

## 1. Understand our history first

Inspect the repository thoughtfully and thoroughly: README, architecture, prior experiments EXP001–EXP007 if present, research philosophy, experiment specifications, source feasibility investigations, backtesting engine, tests, documentation, data lineage rules, existing adapters, recent commits, and any current roadmap.

Prioritize human-authored, decision-relevant files. Do not waste time dumping every generated file or reading millions of data rows.

Understand especially the failures and lessons of EXP004–EXP007.

EXP004 was an ambitious common-stock momentum experiment. We built and validated considerable machinery, enriched 7,871,192 historic source rows with OPEN data, and ultimately could not certify 26 execution-critical historical gaps. Consequently the hypothesis was never honestly evaluated. Other experiments encountered similar feasibility issues around point-in-time data, issuer mapping, and historical coverage.

The original frozen experiments must remain preserved and honestly labelled. Do not silently repair, relax, or repurpose their rules or imply they produced economic results they did not produce.

The key institutional lesson is NOT that rigor is bad. It is that we previously applied heavyweight rigor and complex infrastructure before establishing whether the underlying economic experiment was practical, interesting, or valuable.

We want to reverse that order.

## 2. Adopt our new research philosophy

Research OS is moving toward the systematic discovery and evaluation of unconventional, economically meaningful information.

We are NOT primarily trying to invent another technical indicator, optimize RSI thresholds, stack moving averages, or repeatedly test popular textbook factors.

We want to investigate areas where a potentially valuable signal is hidden in data that is:
- Overlooked by conventional financial researchers.
- Public but operationally awkward, obscure, fragmented, or unintuitive.
- Seemingly unrelated to financial markets until a convincing economic connection is made.
- Buried in government records, archived websites, infrastructure systems, regulatory records, developer ecosystems, procurement systems, logistical flows, technical standards, licensing records, or other unusual sources.
- Potentially combinable with a second independent dataset to reveal a previously invisible economic relationship.

An illustrative example, NOT an instruction to prefer this idea: developer ecosystem activity might help identify emerging technology adoption before it appears in listed companies' reported revenues. GitHub commits alone are not proof of revenue growth; the chain of causality and historical evidence would need to be established.

The central questions are:

1. What real-world economic activity changes before prices fully reflect it?
2. Who observes that change first, and where does it leave a measurable data trail?
3. Can we reconstruct what a researcher could actually have known on each historical date?
4. Which specific listed securities are economically exposed to the change, and why?
5. What alternative explanations, confounders, or already-published strategies could explain the apparent signal?
6. Why might an edge persist despite professional arbitrage?
7. Can we test it with realistically obtainable data and a feasible trading setup?
8. If it works, does it survive sensible controls, plausible transaction costs, and untouched out-of-sample periods?

Originality alone is NOT sufficient. An exotic dataset that does not predict anything useful is worthless. Conversely, an apparently mundane dataset with an original and testable economic link may be very valuable.

We are looking for surprising, defensible, potentially powerful insights — not complexity for its own sake.

Do not claim any idea is truly unresearched merely because you cannot find a paper. Distinguish:
- Known and well-studied.
- Studied, but potentially with an overlooked data source or interaction.
- Sparse research / apparently underexplored.
- No closely matching public prior art found after a documented search.

## 3. Use the attached Deep Research report properly

Read the entire attached report, including:
- Executive conclusions.
- Every individual hypothesis or opportunity.
- Data sources and primary URLs.
- Academic/practitioner citations.
- Claimed historical coverage and publication timing.
- Potential ticker/security mapping methods.
- Access, pricing, API, licensing, and rate-limit issues.
- Any proposed backtesting or falsification protocols.
- Caveats, negative findings, and competing explanations.

Do not merely summarize it. Critically assess it.

For every promising candidate, ask:
- Is the underlying dataset real and accessible?
- Does it have historical observations or only current snapshots?
- Can the historical information-availability timestamp be reconstructed without look-ahead?
- Does the proposed economic mechanism make sense?
- Is there a meaningful reason for an effect over 5, 10, or 20 trading days, or does another horizon fit better?
- Is exposure to the signal concentrated enough in identifiable listed firms to trade?
- What is already known in academic literature or industry?
- What exactly would falsify the hypothesis?
- What is the cheapest credible test?

Cite the report's specific pages or sections where possible. Separate:
(A) what the report actually establishes,
(B) what you verified independently,
(C) what remains a plausible but unverified hypothesis.

If a source is unavailable, a link is dead, or verification is impossible with current tools, explicitly flag that instead of filling gaps with assumptions.

## 4. Build a research opportunity map

Create a ranked shortlist from the report. Also propose a SMALL number of independently reasoned alternatives if the report overlooks a compelling opportunity.

Score each candidate on:

A. Economic plausibility and clarity of the causal mechanism.
B. Genuine originality / lack of obvious crowding, with prior-art evidence.
C. Availability of historical, point-in-time-correct data.
D. Strength of the connection between observable data and tradeable assets.
E. Potential signal strength relative to noise and confounding.
F. Plausibility of a delayed market response.
G. Liquidity, execution feasibility, and realistic capacity.
H. Time and cost to a FIRST HONEST ECONOMIC RESULT.
I. Ability to falsify quickly.
J. Value of the project even if the financial hypothesis fails.

You may use numerical scores, but explain the evidence behind the scores. Do not equate speculative upside with demonstrated profitability.

Distinguish:
- BEST FIRST EXPERIMENT: high research value and fast realistic feasibility.
- BEST LONG-TERM UPSIDE: potentially significant but harder to establish.
- MOST ORIGINAL: unusual information or novel combination.
- HIGH-RISK LONG SHOTS: interesting but substantial timestamp, mapping, legal, sample-size, or causality difficulties.

We don't want every opportunity discarded because it isn't immediately perfect. But we also don't want a six-week data archaeology expedition before seeing one meaningful result.

## 5. Choose an MVP research direction

Recommend ONE initial pilot and TWO backups.

For the primary pilot, give a concrete, actionable mini research design:

- Economic hypothesis, explicit null, and mechanism.
- Exact datasets, URLs/APIs/files and evidence that they exist.
- Required historical date range.
- Information publication/availability timestamps and lag convention.
- Data joins and identifier mapping.
- Simplest defensible signal construction.
- Realistic tradeable universe, preferably liquid securities with verifiable history.
- Expected information horizon, e.g. 5/10/20 sessions if justified.
- Benchmark(s) and negative-control/placebo tests.
- Execution assumption clearly separated from observed prices.
- Handling of splits, dividends, missing data, delistings where relevant.
- Transaction costs, turnover, and capacity caveats.
- Sample-size and coverage sufficiency.
- Clear pass/fail/stop criteria.
- Concrete definition of a successful FIRST TEST.

Be careful not to introduce a new feasibility nightmare by requiring decades of reconstructed intraday security-level OPEN bars, complex corporate-action identity joins, or impossible-to-verify vendor conventions just to obtain our first result.

Avoid treating adjusted-close returns as magically executable. Define them honestly as return measurements when appropriate and distinguish a simple economic screening test from a fully executable production backtest.

## 6. Rebuild the workflow around rapid learning

Propose a lean sequence:

Phase 0 — Literature and mechanism check:
Can we articulate a distinct, plausible economic hypothesis that isn't merely data-mined correlation?

Phase 1 — Source reality check:
Retrieve a small representative historical sample immediately. Confirm fields, historical depth, timestamp semantics, permitted access, and security linkage.

Phase 2 — Minimal end-to-end feasibility:
Produce a tiny but complete dataset joining a historically observable signal to subsequent security returns. Show actual row counts, missingness, timing, and examples.

Phase 3 — First honest economic result:
Use simple transparent analysis and a minimal credible strategy/benchmark comparison. Include negative controls and sensible costs. Do not optimize until the baseline outcome is known.

Phase 4 — Validation:
Only for ideas that survive early falsification, expand periods, challenge assumptions, test robustness and pre-declare any untouched holdout.

Phase 5 — Engineering hardening:
Only once warranted, integrate into Research OS's more sophisticated reusable pipeline and reporting framework.

We should have a decision or a falsifiable result within days, not spend weeks just proving that the experiment's data source exists.

Timebox work. Provide a specific one-week initial schedule with measurable deliverables and stop conditions.

There should be no infinite 'one more source investigation' loops. If a candidate fails its feasibility gate, document the failure, stop, and move to a backup without compromising frozen historical results.

## 7. Decide what to preserve, simplify, and change in Research OS

Identify which existing parts of the repository are truly reusable for this approach:
- Data ingestion and quality checks.
- Backtesting primitives.
- Research notebooks or statistical analysis.
- Reproducibility and metadata.
- Reporting.
- Tests.
- Data provenance and look-ahead controls.

Then distinguish:
- KEEP: already valuable infrastructure.
- SIMPLIFY: sound but disproportionate controls/process.
- ADD: only what the initial pilot demonstrably requires.
- DEFER: future research platform ambitions.
- ARCHIVE: historical experiments and obsolete operational work.

Do not propose a wholesale rewrite merely because our research direction is changing.
Do not add heavyweight orchestration, distributed data systems, a complex experiment registry, or extra abstraction layers without an immediate need.

The goal is to make Research OS a nimble, credible research laboratory with rapid hypothesis turnover AND scientific integrity.

## 8. Important research discipline

Never:
- Label an anomaly 'alpha' before robust evidence.
- Cherry-pick the best hypothesis, universe, horizon, or parameters and then present the result as untouched validation.
- Leak revised/current data into historical periods.
- Treat data's event date as necessarily equal to its public availability date.
- Mistake a data source's existence today for the existence of a reconstructable historical feed.
- Ignore rights, APIs' terms of use, practical collection costs, and rate limits.
- Quietly change previously frozen experiment definitions.
- Present an incomplete backtest as completed.
- Spend substantial time implementing before confirming basic data feasibility.

Do:
- Be imaginative in data discovery.
- Seek non-obvious, testable economic relationships.
- Search for contradictions and prior art.
- Distinguish economic screening from execution-realistic backtests.
- Prefer actual empirical measurements over elaborate theoretical architecture.
- Preserve honest negative findings.
- Move on quickly from blocked ideas.

## 9. Your deliverables for THIS task

Before any major code changes, produce a substantive strategic review in Markdown with:

1. Current Research OS assessment: what we have, what failed, what is valuable.
2. Synthesis of the attached Deep Research report, including important findings AND weaknesses, grounded in report citations.
3. Ranked opportunity matrix with explanations and practical data availability.
4. Deep dives on the strongest 3 candidates.
5. Your recommended ONE first pilot, with a defensible rationale and two backups.
6. Exact minimal datasets, identifiers, historical joins, timestamp controls, and planned economic test.
7. One-week implementation and experiment schedule, with explicit stop/go gates.
8. Repo change plan: keep / simplify / add / defer / archive, with likely paths/files.
9. A short list of unanswered questions that are truly blocking decisions.
10. A clear 'first thing to do tomorrow' task that leads toward a real measurable result.

If useful, write a review document under docs/strategy/, but do not alter frozen experiments or start a major implementation. If the report is not accessible, STOP and ask for it; do not invent its findings.

Your ultimate objective is not to make Research OS look sophisticated.

It is to make Research OS genuinely GOOD AT DISCOVERING, TESTING, AND REJECTING UNUSUAL INVESTMENT HYPOTHESES — rapidly, rigorously, creatively, and with real evidence.

Read first. Think critically. Recommend a direction. Present the plan for my approval before implementation.