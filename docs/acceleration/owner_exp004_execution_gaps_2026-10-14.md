You are continuing Research OS.

Repository:
C:\Users\runni\quant\

GitHub:
jarems421/ai-assisted-quantitative-research

Branch:
main

Expected starting HEAD:
c71aa02e3d04697b7be37cb948310b94cd2fc7a3

======================================================================
OWNER DECISION
EXP004 — BOUNDED 26-EXECUTION-GAP INVESTIGATION
AND PRE-PERFORMANCE NO-FILL CONTINGENCY AMENDMENT
======================================================================

Current state:

LOCAL_EXECUTION_INPUTS_BLOCKED
REQUIRED_EXECUTION_OPEN_ROWS_MISSING

EXP004 economic hypothesis remains UNTESTED.

Resolved successfully:

- VPG identity drift
- all 28 frozen price quarters
- 7,871,192 / 7,871,192 frozen rows enriched
- zero CLOSE mismatches
- zero ambiguous frozen price keys
- frozen security IDs preserved
- SPY Development price coverage 1,511 / 1,511 sessions

Remaining source problem:

273,115 required common-population security/session pairs

273,089 have positive finite OPENs

26 required stock-days have no source row at all

0 present OPENs are invalid

25 gaps affect EW only.

One gap:

TWMC / 2020-08-03

also affects:

M365_K20
M365_K40

The canonical list is in:

docs/acceleration/exp004_frozen_enrichment_report.md

Do not recreate that denominator from memory.

Use the exact persisted 26-case inventory.

======================================================================
1. PURPOSE
======================================================================

This task has ONE purpose:

determine what the 26 absent stock-day rows mean and whether EXP004 can adopt a
fully predeclared, source-supported no-fill contingency WITHOUT inspecting any
strategy return.

Possible reasons include:

A. the security traded and the primary vendor omitted the bar;

B. the security genuinely did not trade during that session;

C. a halt, suspension, listing transition, ticker transition or corporate event
made the intended execution impossible;

D. the historical source identity/date is wrong;

E. evidence is insufficient.

Do NOT equate:

missing vendor row

with:

no trading.

Do NOT equate:

a recovered daily OPEN

with:

a valid EXP004 execution price

until timing and raw-share price semantics are certified.

======================================================================
2. FIX THE POLICY BEFORE SOURCE INVESTIGATION
======================================================================

Before any new scientific source request:

create and commit/push a PRE-PERFORMANCE investigation + amendment policy.

Suggested files:

docs/acceleration/
exp004_execution_gap_investigation_plan_v001.json

docs/acceleration/
exp004_execution_gap_amendment_policy_v001.md

The policy must contain:

- exact 26-case SHA-pinned denominator;
- source-request ceiling;
- evidence hierarchy;
- classification rules;
- execution amendment mechanics below;
- explicit statement that no performance has been inspected;
- Validation accesses = 0;
- Test accesses = 0.

Push this checkpoint before making new source requests.

Do not alter:

experiments/EXP004/freeze_versions/v001/
experiments/EXP004/freeze_versions/v002/

Do not rewrite prior reports.

This is a separately versioned PRE-PERFORMANCE EXECUTION AMENDMENT.

======================================================================
3. REQUEST CEILING
======================================================================

Maximum:

40 NEW SCIENTIFIC SOURCE REQUEST SUBMISSIONS

for this entire task.

A scientific request means a new source query/API/document retrieval submitted
for evidence.

Status polling, manifest retrieval and downloading a result for an already
submitted query do NOT count as separate scientific requests.

A retry that creates a new query/submission DOES count.

Budget allocation ceiling:

1  existing-Lake batch diagnostic request
26 exact-case alternative price/status requests
8  official exchange / SEC / identity / status corroboration requests
5  source-schema / documentation requests

TOTAL MAXIMUM = 40

You may use fewer.

Batch requests wherever possible.

Do NOT:

buy data;
subscribe to a new paid vendor;
launch broad market history downloads;
search thousands of symbols;
start another source campaign.

If the ceiling is reached with unresolved cases:

STOP.

======================================================================
4. FIXED 26-CASE DENOMINATOR
======================================================================

Every one of the 26 cases remains in the audit.

Do not remove:

illiquid stocks;
foreign issuers;
OTC-like names;
awkward tickers;
ended securities;
TWMC;
EW-only cases.

A small numerical fraction is not grounds for exclusion.

Report all 26 individually.

TWMC should be investigated FIRST because it directly affects two frozen
momentum cells.

Its result must NOT be used to modify the rules used for the other 25.

======================================================================
5. EVIDENCE HIERARCHY
======================================================================

Use evidence in this order.

FIRST:

existing immutable repository evidence;

existing EXP004 / EXP003 / EXP002 source receipts;

existing Lake source capability.

SECOND:

one bounded same-source diagnostic covering the exact 26 stock-days and, if
useful, the immediately surrounding certified sessions.

THIRD:

an independent historical market-data source capable of supplying the exact
security/day raw daily OHLC.

FOURTH:

official exchange, SEC, issuer or listing/corporate-action evidence when needed
to establish:

halt;
suspension;
listing transition;
delisting;
merger;
ticker change;
no trading;
other exact lifecycle condition.

OpenFIGI may corroborate security identity.

It cannot prove that trading occurred on a specific historical day.

Yahoo/yfinance, Stooq, generic finance websites or scraped pages may be used as
diagnostic corroboration.

They must NOT, by themselves, certify a recovered execution OPEN unless their
historical price semantics and security identity satisfy the contract below.

======================================================================
6. ALLOWED CASE VERDICTS
======================================================================

Each stock-day must receive exactly one of:

RECOVERED_EXECUTION_BAR

CERTIFIED_NO_TRADING

CERTIFIED_CORPORATE_OR_LISTING_INTERRUPTION

UNRESOLVED_VENDOR_GAP

IDENTITY_OR_SHARE_UNIT_CONFLICT

No other free-form category.

======================================================================
7. RECOVERED_EXECUTION_BAR STANDARD
======================================================================

A missing original row may be restored only if evidence establishes:

1. exact security identity on that date;

2. exact trading date;

3. an actual session OPEN and CLOSE;

4. OPEN corresponds to the same daily session-opening convention used by
   EXP004, not an adjusted synthetic value or arbitrary intraday observation;

5. price is raw/unadjusted in the same share-unit convention required by the
   EXP004 ledger;

6. no unresolved split/share-unit change makes the value incompatible;

7. source provenance and retrieval time are archived;

8. OPEN and CLOSE are finite and positive.

Do not use:

adjusted OPEN;
adjusted CLOSE;
prior close;
next close;
VWAP;
midpoint;
nearest observation;
forward fill;
backward fill.

If the alternative source cannot demonstrate raw/unadjusted share-unit
compatibility:

do not certify the bar.

======================================================================
8. SURROUNDING-SESSION CHECK FOR RECOVERED BARS
======================================================================

For every proposed recovered bar:

compare surrounding sessions against the existing frozen Lake observations.

Purpose:

detect:

split-scale mismatch;
adjusted/unadjusted mismatch;
wrong security;
ticker reuse;
obvious decimal/unit mismatch.

This is a SHARE-UNIT / IDENTITY sanity check.

Do NOT derive the missing price by interpolation.

Do NOT average vendors.

Do NOT select the vendor whose price produces a preferred return.

======================================================================
9. CERTIFIED_NO_TRADING STANDARD
======================================================================

Use CERTIFIED_NO_TRADING only where positive evidence establishes that the
security had no executable trading session for that security on the intended
date.

Absence from two vendors is not sufficient by itself.

Acceptable evidence may include:

official exchange/trading-status evidence;

source-supported historical listing/trading-status evidence;

an exact corporate/listing condition that demonstrates no trading;

other authoritative evidence specifically showing that no execution could have
occurred.

If the security merely lacks a vendor row but may have traded:

UNRESOLVED_VENDOR_GAP.

======================================================================
10. CORPORATE / LISTING INTERRUPTION
======================================================================

Use:

CERTIFIED_CORPORATE_OR_LISTING_INTERRUPTION

where the exact stock-day is explained by:

ticker transition;
merger;
listing transfer;
suspension;
delisting;
security termination;
other evidenced lifecycle event.

Do not automatically treat this as CERTIFIED_NO_TRADING.

Record the exact event and what execution would have been possible.

If lifecycle economics are needed to value an already-held position, flag the
case for the later held-terminal stage.

Do not solve the full terminal event in this task unless necessary merely to
classify the missing execution day.

======================================================================
11. UNIVERSAL PRE-PERFORMANCE NO-FILL AMENDMENT
======================================================================

Freeze the following rule BEFORE looking at returns.

This rule applies universally to:

M180_K20
M180_K40
M365_K20
M365_K40
EW
SPY

and to future Validation/Test if EXP004 ever reaches them.

It is NOT specific to the observed 26 names.

----------------------------------------------------------------------
ACTIVE TARGET-WEIGHT ORDER
----------------------------------------------------------------------

A monthly rebalance creates target-weight instructions.

If a security has a certified executable OPEN on the intended session:

execute normally under the existing EXP004 rule.

If authoritative evidence establishes that the security cannot trade on the
intended session:

NO FILL occurs for that security.

The target instruction becomes PENDING.

Do not remove the security from the target population.

Do not redistribute its weight to other securities.

Do not substitute another security.

----------------------------------------------------------------------
NO-TRADE HELD SECURITY
----------------------------------------------------------------------

If the security is already held and cannot trade:

retain the existing quantity.

No sale proceeds are assumed.

No fee is charged.

For NAV/reference-equity purposes only:

use the most recent prior CERTIFIED CLOSE while the security is proven
non-trading.

This is a valuation mark only.

It is NOT an executable price.

If no prior certified close exists:

STOP.

----------------------------------------------------------------------
PENDING BUY / INCREASE
----------------------------------------------------------------------

If the target requires a buy or increase but the security cannot trade:

do not buy.

Its target weight remains unfilled/pending.

The unfilled allocation is NOT redistributed among other names.

Cash not consumed by that order remains cash.

Do not synthetically invest it.

----------------------------------------------------------------------
PENDING SELL / REDUCTION
----------------------------------------------------------------------

If the target requires a sell or reduction but the security cannot trade:

retain the position.

No sale proceeds are available.

The sell/reduction remains pending.

Other buys cannot rely on nonexistent proceeds.

----------------------------------------------------------------------
CASH CONSTRAINT
----------------------------------------------------------------------

Preserve:

long only;
no leverage;
no negative cash;
no proportional rescaling.

Process certified executable sells before buys exactly as the existing engine
does.

If a buy cannot be fully funded because an expected sale is still pending:

do NOT partially fill it.

Mark it:

PENDING_CASH_CONSTRAINED

and carry the target instruction forward.

No partial fill.

No leverage.

No redistribution.

----------------------------------------------------------------------
FIRST LATER EXECUTABLE SESSION
----------------------------------------------------------------------

A pending target instruction is reconsidered on each later session.

At the FIRST later session with a certified compatible OPEN:

take ONE pre-fill reference-equity snapshot for that session.

Use:

certified current OPENs for tradable held securities;

last certified CLOSE only for securities still positively certified
non-trading;

cash;

certified dividend/receivable balances when later action certification exists.

Then compute target quantity from:

ACTIVE target weight
x
that session's pre-fill reference equity
/
that security's certified OPEN.

This is a delayed TARGET-WEIGHT execution.

Do not freeze or guess quantity on the original missing-price day.

Process:

pending sells/reductions first;

then pending buys/increases;

stable security ID ascending inside each side.

Charge the normal 0.10% fee only when an actual fill occurs.

----------------------------------------------------------------------
NO RESIZING OF OTHER NAMES
----------------------------------------------------------------------

A missing or pending security never causes the remaining target weights to be
renormalized.

The portfolio may temporarily have:

extra cash;
a stale held position;
less than 95% desired deployed exposure.

That execution drag is part of the amended estimand.

----------------------------------------------------------------------
SUPERSESSION
----------------------------------------------------------------------

At the next scheduled monthly rebalance:

the NEW frozen target weights supersede all unfilled prior target instructions.

Cancel the old pending instructions.

Recompute the target instructions from the actual portfolio state.

An old pending order must never execute after a newer monthly decision has
superseded it.

----------------------------------------------------------------------
CORPORATE ACTION WHILE PENDING
----------------------------------------------------------------------

If a split occurs while a held order is pending:

apply the certified split to the held quantity before later execution.

If a terminal corporate event occurs before a pending order executes:

cancel the pending order for the terminated security.

For an already-held position:

use the later certified terminal-action rule.

For a pending buy into a security that terminates before fill:

do not buy;
release the pending instruction;
do not automatically buy the successor.

Any successor becomes eligible only through the normal frozen strategy rules or
certified held-stock-merger mechanics.

----------------------------------------------------------------------
FEES
----------------------------------------------------------------------

Fees occur only on actual fills:

0.10% per fill

No fee on:

no-fill;
pending order;
order cancellation;
supersession.

----------------------------------------------------------------------
DAILY MARKING DURING CERTIFIED NONTRADING
----------------------------------------------------------------------

A carried prior CLOSE may be used only for NAV valuation of an already-held
security during a positively certified non-trading period.

It must be labelled:

STALE_MARK_NONEXECUTABLE

It cannot be used for:

fills;
target quantity on the unavailable day;
signals;
ranking;
execution;
corporate consideration.

At the first later certified price observation:

resume actual marking.

======================================================================
12. MISSING VENDOR DATA IS NOT ELIGIBLE FOR NO-FILL
======================================================================

Critical rule:

The no-fill amendment can be invoked only for:

CERTIFIED_NO_TRADING

or a source-supported:

CERTIFIED_CORPORATE_OR_LISTING_INTERRUPTION

whose exact economics imply no executable trade.

It CANNOT be invoked merely because the primary vendor omitted a row.

If a case remains:

UNRESOLVED_VENDOR_GAP

EXP004 remains blocked.

No silent stale mark.

No assumed halt.

======================================================================
13. PRESERVE V001 ENGINE
======================================================================

Do not loosen:

EXP004_LOCAL_REFERENCE_V001

in place.

Its existing fail-closed behaviour is historical evidence.

Create a separately versioned engine only if the amendment becomes usable.

Suggested:

EXP004_LOCAL_REFERENCE_V002

or repository-consistent equivalent.

V002 must explicitly encode the pending target/no-fill semantics above.

Do not simply remove:

exact_population
missing-price
cash
identity

guards from V001.

Reuse tested ledger components where appropriate.

Preserve V001 byte-for-byte if practical.

======================================================================
14. SYNTHETIC TESTS BEFORE REAL USE
======================================================================

Add synthetic EXP999 fixtures for at least:

normal fill unchanged from V001;

missing new-buy security -> pending cash;

missing held sell -> retain quantity / no proceeds;

later first executable OPEN -> delayed fill;

pending sell then buy funded after sale;

cash-constrained buy -> pending, no partial fill;

no weight redistribution;

stable-ID order;

fee only on actual fill;

next-month supersession;

split while pending;

cash merger while pending;

stock merger while pending;

pending buy terminated before fill;

STALE_MARK_NONEXECUTABLE NAV valuation;

no stale mark used as execution price;

UNRESOLVED_VENDOR_GAP rejects execution;

recovered exact bar executes on intended day;

candidate and EW mechanics identical;

SPY mechanics identical if ever applicable.

V001 fixtures must remain passing.

======================================================================
15. INVESTIGATE TWMC FIRST
======================================================================

First exact case:

2020-08-03
TWMC
figi:BBG001S5WYG8

Affected:

EW
M365_K20
M365_K40

Determine whether:

TWMC traded that day;

a raw compatible OPEN/CLOSE can be recovered;

there was a halt/listing/corporate issue;

or the case remains unresolved.

Do not inspect strategy returns.

Do not alter the policy based on the answer.

Then process the other 25 under exactly the same evidence rules.

======================================================================
16. CASE RECEIPT
======================================================================

Create one immutable row per case with:

required_session

ticker

frozen_security_id

affected_cells

primary_source_bar_present = false

verdict

evidence_source_1

evidence_source_2 if needed

security_identity_verified

session_trading_status

recovered_open if permitted

recovered_close if permitted

raw_unadjusted_contract_verified

share_unit_verified

timing_contract_verified

surrounding_session_check

corporate_or_listing_event if any

first_later_certified_open_session if relevant

source hashes

notes

Do not include strategy return fields.

======================================================================
17. PASS CONDITIONS FOR THIS TASK
======================================================================

This 26-gap stage passes only if EVERY case is one of:

RECOVERED_EXECUTION_BAR

or

CERTIFIED_NO_TRADING

or

CERTIFIED_CORPORATE_OR_LISTING_INTERRUPTION
with complete execution interpretation.

Required unresolved counts:

UNRESOLVED_VENDOR_GAP = 0

IDENTITY_OR_SHARE_UNIT_CONFLICT = 0

If even one remains unresolved:

STOP.

Do not argue that 1 / 273,115 is immaterial.

======================================================================
18. VERSIONED AMENDMENT RECEIPT
======================================================================

If and only if all 26 resolve:

create a separate receipt, e.g.:

experiments/EXP004/execution_amendments/v001/receipt.json

and:

docs/acceleration/
exp004_execution_gap_amendment_report.md

Bind:

original frozen spec hash

original methodology hash

V001 engine hash

V002 engine hash if created

26-case inventory hash

all case-evidence hashes

request count

classification counts

exact no-fill semantics hash

performance_executed = false

Validation accesses = 0

Test accesses = 0

Explicitly state:

THE ORIGINAL EXP004 FREEZE IS PRESERVED.

THIS IS A PRE-PERFORMANCE EXECUTION-CONTINGENCY AMENDMENT CREATED AFTER
DISCOVERING MISSING EXECUTION-DAY SOURCE ROWS BUT BEFORE OBSERVING ANY
STRATEGY PERFORMANCE.

Do not pretend the execution contract was never amended.

======================================================================
19. DO NOT PROCEED DOWNSTREAM IN THIS TASK
======================================================================

Even if all 26 cases resolve:

STOP AFTER THE VERSIONED EXECUTION AMENDMENT RECEIPT.

Do NOT yet run:

dividend acquisition;

dividend accounting;

held-terminal audit beyond what was necessary to classify these 26 days;

v004 local execution certificate;

24 fold evaluations;

six full replays;

performance;

robustness;

Validation;

Test.

This task has a deliberate endpoint.

Owner review comes next.

======================================================================
20. SOURCE DISCIPLINE
======================================================================

No new experiment.

No EXP008.

No Nexus backtests.

No Aurora.

No optimizer.

No paper/live.

No 2021+ data.

No performance metrics.

No broad corporate-action archaeology.

No market-wide alternative-vendor acquisition.

Only the 26 fixed stock-days and strictly necessary adjacent/context evidence.

======================================================================
21. FINAL STATUS
======================================================================

Return exactly one primary status:

EXECUTION_GAPS_RESOLVED_WITH_AMENDMENT_READY

or

EXECUTION_GAPS_UNRESOLVED

or

EXECUTION_SOURCE_CONTRACT_CONFLICT

If blocked:

list unresolved cases and the precise reason.

If passed:

report classification totals and confirm all 26 remain represented in the
experiment.

======================================================================
22. FINAL DELIVERY
======================================================================

Report:

starting HEAD
final HEAD
commits
hosted CI

REQUEST BUDGET:

scientific request ceiling
scientific requests used
polls/downloads separately
remaining allowance

26-CASE AUDIT:

RECOVERED_EXECUTION_BAR count

CERTIFIED_NO_TRADING count

CERTIFIED_CORPORATE_OR_LISTING_INTERRUPTION count

UNRESOLVED_VENDOR_GAP count

IDENTITY_OR_SHARE_UNIT_CONFLICT count

TWMC verdict

all 26 individual rows

AMENDMENT:

policy hash

receipt hash

V001 preserved

V002 hash if created

synthetic tests

cash rule

pending-buy rule

pending-sell rule

later-fill rule

supersession rule

fee rule

terminal-while-pending rule

stale NAV mark rule

NO PERFORMANCE:

24 folds = NOT_RUN
6 full replays = NOT_RUN
Development performance evaluations = 0
Validation accesses = 0
Test accesses = 0

Then STOP.

======================================================================
23. OWNER INTENT
======================================================================

The 28-quarter historical-price repair succeeded.

The remaining problem is now only 26 exact execution stock-days.

Do not turn this into another architecture project.

Determine whether each represents:

recoverable missing market data;

true non-trading;

a lifecycle interruption;

or unresolved evidence.

Freeze the no-fill semantics before source investigation.

Apply them universally and symmetrically.

Do not drop the securities.

Do not ignore EW.

Do not use the numerical smallness of the problem as justification.

If all 26 can be supported:

freeze the separate pre-performance execution amendment and stop for review.

If even one cannot:

stop EXP004 clearly.

No returns yet.