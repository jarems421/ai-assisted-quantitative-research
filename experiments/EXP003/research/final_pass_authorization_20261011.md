This is much better than EXP002. The remaining problems are now focused implementation choices, not a collapsing data thesis.
And importantly: we should not start another giant audit loop. This should be the last pre-freeze pass for EXP003.
One thing to fix immediately: Codex set the remote budget to zero, but you already told me you want to use Nexus aggressively. So we should explicitly authorize Nexus for this focused pass.
Send Codex this:
EXP003 — Final Freeze-Readiness Pass
EXP003 remains DRAFT.
This is the final focused pre-freeze implementation pass.
Do not start another general data/source audit.
We already accept the source-defined historical common-equity universe concept unless this task demonstrates that it is operationally unusable.
No candidate performance may be inspected.
No optimization.
No outer Validation/Test observations.
No freeze automatically.
The owner explicitly authorizes up to 2,000 included Nexus research tokens for this task.
Use Nexus Lake, SDK, MCP, previews and minimal deterministic diagnostics freely where they resolve one of the remaining freeze gates.
Do not purchase additional credits.
1. Certify the production EXP003 universe
Primary universe concept:
historically source-covered common-stock (CS) security identities with valid historical identity spans and valid completed price history.
Requirements:
- historical effective ticker/security spans
- stable security identity
- CS classification
- valid price data at the decision date
- retain securities whose historical span later ends/delists
- exclude ambiguous identity/subtype rows
- never use current membership backwards
Do not require:
- S&P 500 membership
- market cap
- ADV
- present exchange membership
If exchange/OTC history cannot be certified, do not invent it.
Instead describe the universe precisely as a:
source-covered historical common-equity universe
rather than claiming it represents all exchange-listed U.S. stocks.
Produce monthly universe counts through Development for transparency.
If this source-defined universe is deterministic and historically reconstructible, mark the universe gate PASS.
Do not keep searching for a prettier universe merely because it is unconventional.
2. Establish production joint signal coverage
For every proposed monthly decision date before 2021 determine:
- universe count
- securities with valid momentum
- securities with valid insider state
- securities with both
- certified insider zero count
- unavailable insider count
- ambiguous identity count
Report:
- monthly counts
- annual summaries
- joint-coverage %
The composite and matched momentum-only portfolio must use the same eligible signal-coverage universe at each decision.
A stock cannot appear in momentum-only while being omitted from the composite merely because insider data are unavailable.
Separately report a broader momentum-universe diagnostic, but it is not the primary matched comparator.
3. Freeze insider zero semantics
Finalize when Distinct Qualifying Insider Purchasers = 0 is legitimate.
Numeric zero is allowed only when source coverage is sufficiently certified for that security/window and there are genuinely no qualifying active purchase events.
Otherwise:
UNAVAILABLE
not zero.
Preserve:
- validity companion
- session key
- as-of availability
- ambiguity exclusion
Quantify how often each state occurs.
Choose any necessary coverage threshold from coverage mechanics only, never subsequent returns.
4. Determine Development inception
Use the completed production contracts to determine the earliest date where every required candidate can be formed with:
- 365-calendar-day momentum history
- 90-calendar-day insider history
- certified universe identity
- valid price contract
- valid PIT insider state
Select inception strictly from availability.
Development must end:
2020-12-31
Do not force January 2015.
Prefer a clean calendar boundary if moving a few days/weeks later produces a clearer reproducible design.
5. Finalize Development folds
Once inception is known, define chronological expanding folds.
Prefer four clean annual held-out folds if feasible.
Example only, if coverage supports it:
- earlier years → 2017
- earlier years → 2018
- earlier years → 2019
- earlier years → 2020
Use only prior information for each fold.
Warmup is not scored.
Do not tune fold boundaries from results.
6. Finalize outer Validation and Test dates
These dates must be chosen now, before Development performance.
If data coverage supports them, use:
Outer Validation
2021-01-01 through 2023-12-31
Historical workflow-held-out Test
2024-01-01 through 2024-12-31
The Test must be sealed immediately in Research OS.
Do not retrieve observations from either period.
Explicitly label both as workflow-held-out historical data, not genuinely prospective unseen information.
Future paper trading remains the genuine forward test.
If source coverage itself cannot support these windows, change dates using coverage metadata only and explain why.
7. Final parameter surface
Freeze exactly:
Momentum
- 180 calendar days
- 365 calendar days
Insider
- 30 calendar days
- 90 calendar days
Holdings
- 20
- 40
Full composite:
2 × 2 × 2 = 8 cells
Momentum-only:
2 × 2 = 4 unique cells
Insider-only:
2 × 2 = 4 unique cells
Do not duplicate irrelevant parameter dimensions in ablations.
Do not introduce another axis.
Monthly cadence fixed.
Equal signal-rank weighting fixed.
Equal security weighting fixed.
Nominal deployment fixed according to the previously audited execution convention.
8. Holdings-shortfall rule
Predeclare what happens when fewer than 20/40 securities are eligible.
Do not silently alter the universe or ranking.
Prefer:
- hold every eligible security when eligible count < target K
- equal weight across those securities
- preserve remaining allocation as cash
unless Nexus mechanics require another deterministic implementation.
Establish the exact rule now.
Record frequency of historical coverage shortfalls without inspecting subsequent performance.
9. Selection rule
Replace inherited EXP001 eligibility assumptions where they are inappropriate for a monthly cross-sectional strategy.
Selection must answer the EXP003 hypothesis rather than merely maximize standalone Sharpe.
For every composite cell, compare against its matched momentum-only control using the same:
- momentum horizon
- holdings K
- decision dates
- eligible universe
- funding/cost assumptions
A composite cell is eligible to advance only if, across the predeclared Development/fold aggregation:
1. paired mean daily net return difference is positive
2. zero-RF Sharpe difference is positive
3. no critical execution/coverage rule fails
4. sufficient scheduled rebalance participation exists
Define the exact participation requirement before seeing results.
Among eligible composite configurations, use a predeclared robustness-oriented score.
Prefer a simple rule such as:
- highest median fold paired mean-return improvement
- with positive aggregate Sharpe improvement required
- tie broken by lower parameter sensitivity, then lower turnover
If another simple rule is methodologically cleaner, document it now.
Do not choose based on Test or outer Validation.
10. Parameter stability
Predeclare stability diagnostics across the eight-cell composite surface.
Record:
- neighbouring-cell performance
- fold consistency
- sign consistency of incremental effect
- parameter sensitivity
An isolated maximum should receive a fragility warning.
Do not automatically replace the winner with a neighbouring cell after results.
11. Benchmarks
Compile and freeze:
Primary matched control
Momentum-only.
Market benchmark
Explicit SPY buy-and-hold with the same period funding and fee conventions.
Universe benchmark
Monthly equal-weight eligible-universe portfolio.
Verify each portfolio definition compiles using actual Nexus SDK structures.
Do not run their performance yet.
12. Custom indicator production readiness
Generate the Development-period insider custom-indicator dataset only after all coverage contracts are final.
Do not generate Validation/Test custom data during Development.
Freeze:
- source hashes
- methodology hash
- Git SHA
- row count
- min/max source availability
- emitted decision dates
- validity stream
- session-key stream
Use versioned immutable datasets.
Confirm a future Validation/Test dataset version can be generated from the same frozen code without changing methodology.
13. Final statistical contract
Preserve:
- paired strategy/control daily returns
- 20-return blocks
- 10,000 resamples
- fixed seed 2002001
- 95% percentile intervals
Primary quantities:
- paired mean daily return difference
- Sharpe difference
Require positive observed values for both.
Bootstrap intervals are descriptive uncertainty.
Do not make significance or alpha claims from them.
Keep Development-selection bias explicitly disclosed.
14. Robustness contract
Predeclare, but do not execute yet:
- additional +10 bps traded-notional cost each side
- additional +20 bps each side
- one additional trading-session execution delay
- alternative insider window/momentum cell neighbourhoods via the already-declared grid
- broader momentum-only universe diagnostic
Weekly cadence is not part of EXP003 unless already required by the current specification.
Keep the experiment focused.
15. Evaluation count and Nexus budget
Compile the final number of:
- Development family/cell runs
- fold runs
- Development replays
- benchmarks
- robustness runs
- outer Validation runs
- eventual Test runs
- failure reserve
Use Nexus previews where available to establish actual planned amplification and current token estimate.
The owner is not concerned about small token usage.
Optimize for research quality, not minimum spend.
Do not add trials merely because credits are available.
16. Production-readiness audit
Update:
- EXP003 spec
- provenance
- design README
- universe_feasibility.md
- evaluation_plan.json
- candidate_definitions.json
Create:
- final_freeze_review.md
- production custom-signal manifest/spec as appropriate
Run:
python -m src.research audit EXP003
Do not weaken PIT, sealed-date, provenance or Test protections.
Correct schema rules if an inherited EXP001 assumption is genuinely inappropriate for EXP003, but document the methodological reason.
Run the complete repository test suite.
Commit and push.
Final response
Report:
- final universe definition
- monthly/annual universe and joint-coverage statistics
- certified-zero semantics
- Development inception
- Development folds
- Validation dates
- sealed Test dates
- exact parameter surface
- selection rule
- holdings-shortfall rule
- benchmark definitions
- robustness contract
- production custom-indicator readiness
- projected Nexus evaluations/tokens
- remaining noncritical limitations
- test count
- commit SHA
End with exactly one:
READY FOR FREEZE REVIEW
BLOCKED — UNIVERSE
NEEDS DESIGN REVISION
Do not freeze EXP003 automatically.