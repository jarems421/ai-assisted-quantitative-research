EXP004 — Pre-Performance Corporate-Action QA Amendment
EXP004 remains economically untested. No candidate, benchmark, fold, Validation or Test performance has been observed.
Input QA discovered that some historical security/date windows cannot produce the frozen split-safe momentum signal because multiple distinct same-effective-date corporate-action factors exist without sufficient event/version lineage to determine one unique adjustment.
This is a source-integrity amendment, not an alpha redesign.
Do not attempt to resolve these cases by:
- choosing one factor
- multiplying all factors
- averaging factors
- ticker-specific manual corrections
- inspecting subsequent returns
- deleting affected securities permanently
1. Preserve the original freeze
Keep the original EXP004 freeze receipt, specification hash and methodology hash immutable.
Mark it:
SUPERSEDED_PRE_PERFORMANCE_BY_SOURCE_QA
Do not delete or overwrite it.
Record explicitly:
- zero EXP004 performance had been observed
- the amendment was triggered solely by production input QA
- affected events were identified before any candidate/benchmark run
2. Add one generic fail-closed corporate-action rule
Define an ambiguous corporate-action event as a security/effective-date group for which the frozen source inputs do not establish one unique economically applicable split/share-adjustment factor.
This includes, at minimum:
- more than one distinct factor for the same stable security and effective date without event lineage proving how they compose
- unresolved version/revision ambiguity
- another corporate-action state where the existing source contract cannot determine a unique split-continuity adjustment
Do not classify ordinary unique source split events as ambiguous merely because perfect vendor revision history is unavailable.
For every monthly decision T, inspect the complete maximum 365-calendar-day momentum lookback.
If that interval crosses an ambiguous corporate-action event for security S:
S = UNAVAILABLE_FOR_EXP004_AT_T
The security is excluded from the common eligible population for that decision.
This applies identically to:
- M180/K20
- M180/K40
- M365/K20
- M365/K40
- monthly equal-weight eligible-universe benchmark
Thus the 180-day strategy may not regain a security earlier than the 365-day strategy.
Maintain one common comparison universe.
Once the maximum 365-day lookback no longer crosses the ambiguous event, the security may become eligible again if all other frozen requirements pass.
This is a temporary information-quality exclusion, not permanent survivorship filtering.
3. Do not hard-code LADR, BTX or ALEX
Re-scan the entire pre-2021 Development source extract using the generic rule.
LADR, BTX and ALEX are discovered examples, not an exclusion list.
Produce a deterministic ledger containing:
- stable security ID
- ticker at event
- effective date
- distinct source factors
- ambiguity reason
- first affected EXP004 decision
- last affected EXP004 decision
- number of excluded security-decisions
Include all ambiguous groups, including ones that previously did not intersect an eligible window.
4. Preserve source evidence
Keep the original split rows unchanged.
Preserve the finding that LADR's same-date source factors correspond to a complex cash/stock distribution rather than treating them as a normal unique split.
External documentation may be recorded as explanatory evidence but must not be used to create ticker-specific corrected factors.
The strategy remains entirely systematic.
5. Optional adjusted-price diagnostic
Inspect whether the underlying/Nexus daily source exposes an authoritative split-adjusted OHLC field.
Current upstream documentation states aggregate bars are split-adjusted by default and not dividend-adjusted.
You may compare such adjusted prices around:
- LADR
- BTX
- ALEX
- several ordinary splits
strictly as a QA diagnostic.
Do not silently replace the frozen/local momentum implementation with adjusted bars during this amendment.
If adjusted bars demonstrate a substantially cleaner future implementation, document it for a later experiment or explicit separately reviewed EXP004 amendment.
The present fix is fail-closed exclusion.
6. Rebuild Development input QA
Apply the new corporate-action ambiguity rule and regenerate the Development input panels through 2020.
For every monthly decision report:
- source universe
- normal eligibility exclusions
- corporate-action ambiguity exclusions
- final common eligible population
- K20/K40 availability
Confirm:
- no duplicate identities
- no future price bars
- no ambiguous corporate-action window enters a momentum value
- all four cells use the same common maximum-horizon population
- equal-weight benchmark uses that same population
Do not inspect returns.
7. Amendment review and re-freeze
Update the EXP004 specification/methodology only as required to encode this single source-QA rule.
Do not change:
- research hypothesis
- 180/365 horizons
- K20/K40
- monthly cadence
- ranking
- costs
- benchmarks
- Development dates/folds
- Validation dates
- sealed Test
- selection rule
- robustness contract
Run:
python -m src.research audit EXP004
Run the complete test suite.
If the amended input contract passes, create a new immutable EXP004 freeze version and record:
- old freeze hash
- new freeze hash
- exact diff
- reason
- proof that zero performance was observed before amendment
Commit and push.
8. Continue directly into Development
Once the amended freeze and complete input QA pass, the existing Development execution authorization remains valid.
Do not ask for another design approval solely because this pre-performance source-QA amendment passed.
Generate/bind the required Development streams and execute the frozen four-fold EXP004 programme.
No 2021+ observations.
No Validation.
No Test.
No additional parameter cells.
Preserve all runs and failures.
Calculate the previously frozen independent metrics and selection contract.
Stop after Development and report the complete results.
Stop conditions
Stop instead of backtesting only if:
- the generic ambiguity rule cannot be implemented deterministically;
- additional QA reveals a materially broader corporate-action integrity failure rather than isolated fail-closed windows; or
- implementing this rule would require changing the economic definition of momentum.
Otherwise proceed.
Run tests, commit and push all verified work.

Why I prefer this over another source investigation
There are roughly 3,500–3,900 eligible price-history names per month, while the current QA has found three active problematic histories. We're talking about a tiny data-quality edge case, not evidence that the entire price database is unusable.
And LADR actually demonstrates why our QA was valuable: those two factors weren't obviously “duplicate bad rows.” They corresponded to alternative stock/cash election outcomes in a special distribution. ir.laddercapital.com
A real system should say:
\[
\text{cannot determine signal faithfully}
\quad\Rightarrow\quad
\text{signal unavailable}
\]
rather than:
\[
\text{eh, multiply both and hope}
\]