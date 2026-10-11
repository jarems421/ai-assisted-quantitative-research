# EXP003 — momentum plus qualifying insider purchases

**DRAFT · NEEDS DESIGN REVISION.** Universe identity feasibility is supported within a deliberately source-defined historical common-equity population. Production joint signal coverage and chronology remain unresolved. No candidate performance, Nexus operation, spending or freeze occurred. EXP002 remains closed and unchanged.

Does adding publicly usable qualifying insider purchases to medium-term momentum improve **both mean daily net return and zero-RF Sharpe** versus matched momentum-only? Lower drawdown alone does not confirm this hypothesis. Momentum may represent gradual information incorporation and purchases management conviction; this is a rationale to test, not evidence of predictive power.

| Design component | Proposed contract |
|---|---|
| Historical universe | Source-covered `CS` security identities, historical effective ticker/date spans, unambiguous stable IDs and valid completed prices. No present-day/index membership; retain ended histories while eligible. |
| Momentum | 180 / 365 elapsed calendar days, completed split-continuous prices; no future split factor or dividend double counting |
| Insider | 30 / 90 calendar days of Distinct Qualifying Insider Purchasers; nonderivative P/A positive shares, including private purchases; stable owner/event dedup and availability-based corrections |
| Holdings and ranks | 20 / 40; monthly, equal signal ranks and equal security weights; at most eight composite cells |
| Controls | Four momentum-only cells; four insider-only cells; eight composite cells. Matched coverage/eligibility across families. |
| Benchmarks | Proposed explicit SPY buy-and-hold and monthly equal-weight entire eligible universe; implementation not frozen |
| Decision / execution | Preceding calendar day 21:00 New York / intended next trading session 09:30. Numeric, validity and exact full-session-date streams; inherited bounded fixture behavior. |
| Costs | $25,000 funding, 0.10% per fill, cash dividends; proposed nominal 95% deployment (bounded engine sample deployed 93.5%). Additional local 10 / 20 bps traded-notional stress; no native slippage claim. |
| Primary evidence | Paired net mean daily excess and separate zero-RF Sharpe difference; both positive. Descriptive paired block bootstrap, no significance/alpha claim. |
| Dates | Joint Development inception unresolved; end 2020-12-31. Folds, outer Validation and Test unresolved, all later observations prohibited. |
| Remote budget | Zero authorized. Conditional plan: 122 future evaluations including reserve, no jobs submitted. |

No institutional/13F signal, CUSIP omission rule, native S&P membership, uncertified ADV, market-cap filter or prospective rebalance metric enters EXP003. The historical source population can include unknown exchange/OTC venues; it is **not** advertised as a complete US exchange-listed or liquid universe. Non-CS and unknown subtype rows are excluded rather than guessed.

Read the [universe feasibility memo](research/universe_feasibility.md), [candidate/control definitions](candidate_definitions.json), [evaluation plan](evaluation_plan.json), [provenance](provenance.json) and [original request](research/owner_request_20261011.md). VERIFIED labels apply only to the named source declaration, observed sample or local software property; proposed production behavior remains separate.

The strict Research OS schema requires numeric eligibility thresholds and Development/outer Validation dates. These draft values are **nonexecuting placeholders**: inherited eligibility (25% DD, 20 trades, 35% participation) needs two-signal justification; selection aggregation/ties need settlement. The actual date decisions remain null in provenance; the one-day outer placeholder is not an evaluation window. Production PIT flags stay false, so the unchanged semantic audit rejects the draft. No audit or freeze gate was weakened to accommodate missing evidence. Everything from 2021 onward is sealed against design access.

Before freeze: establish the completed-price/insider per-decision intersection and certified zeros, then choose inception/folds from coverage alone; settle selection, ties, holdings-shortfall policy and benchmark/transport compilation; choose disjoint held-out dates without early observations; reconcile job amplification and a current token quote. These are focused implementation/coverage gates, not permission for another general source audit or a candidate run. If this operational universe proves unusable, stop and report **BLOCKED — UNIVERSE** rather than repairing it with present-day members.

Retain all cells, failures and poor results. Use simple adjacent-close returns, RF=0, 252 sessions/year, sample SD, zero-MAR all-return downside RMS, period-specific running-peak drawdown and $25,000 funding. Reuse the descriptive paired noncircular bootstrap: 20-return blocks, 10,000 draws, seed 2,002,001 and 95% percentile intervals. Holm is schema-reserved and inactive; the bootstrap supplies no p-values. Historical windows are workflow-held-out with known human/model contamination. Forward paper is required after separate owner approval, for at least six months and six monthly opportunities; no live-trading path.

Reproduce this local pass with `python -m src.research.design_exp003`; run `python -m src.research audit EXP003` (expected rejection while production PIT is unresolved) and `python -m unittest discover -s tests -v`. Existing ignored raw source receipts are required for count reproduction; synthetic rule tests run without them.
