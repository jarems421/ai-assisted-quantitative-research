You are continuing Research OS.

Repository:
C:\Users\runni\quant\

GitHub:
jarems421/ai-assisted-quantitative-research

Branch:
main

Expected starting HEAD:
4b75f8d5eb9bf6cae451ec34afe45ec113c0ac97

======================================================================
OWNER DECISION
EXP004 — RESOLVE VPG IDENTITY DRIFT AND COMPLETE FROZEN-ROW ENRICHMENT
======================================================================

Current state:

LOCAL_EXECUTION_INPUTS_BLOCKED
SOURCE_RECONCILIATION_BLOCKED

EXP004 hypothesis remains frozen and untested.

The first supplemental OPEN-price quarter produced:

frozen rows:       256,677
supplemental rows: 256,677

exact full-key matches:
256,615

missing frozen keys:
62

replacement supplemental keys:
62

matched CLOSE mismatches:
0

positive finite OPENs:
256,677 / 256,677

All 62 substitutions concern:

ticker:
VPG

Frozen security ID:
ticker:VSHw@2010-06-24

Current rejoined security ID:
ticker:VSHw@2010-06-24#2

The ticker/date observations themselves match and all matched CLOSE values agree.

The previous stop was correct under the old exact-key contract.

The owner now authorizes ONE bounded investigation of this identity drift and,
if resolved, a corrected supplemental execution-field enrichment method.

Do NOT:

strip "#2" by assumption;
rewrite old frozen IDs;
project today's ticker backward;
launch another experiment;
create a generalized identity framework;
change any economic parameter.

======================================================================
1. FIRST: DETERMINE WHAT VPG / VSHw #2 ACTUALLY MEANS
======================================================================

Before acquiring another quarter, inspect all existing frozen/local evidence
for the two identities:

ticker:VSHw@2010-06-24

and

ticker:VSHw@2010-06-24#2

Use the existing frozen historical-security-span artifacts and, if required,
ONE bounded read-only current source query for the relevant VPG/VSH rows.

Compare at minimum:

ticker
security_id
CIK
asset_type
share/class field if present
share_class_figi if present
composite_figi if present
exchange/venue if present
from_date
to_date
source/provider identifiers
all other identity-defining columns available in the source

Also inspect whether:

the frozen source snapshot contained only one VPG/VSHw candidate;

the current source contains multiple candidates;

the "#2" suffix is generated because of a namespace collision;

another distinct economic security/class exists with the unsuffixed base ID;

the current record is merely a later deterministic serialization/name change.

Do not infer equivalence from the suffix alone.

======================================================================
2. REQUIRED VPG VERDICT
======================================================================

Use exactly one of:

VPG_SAME_SECURITY_NAMESPACE_DRIFT

VPG_DISTINCT_OR_AMBIGUOUS_SECURITY

VPG_IDENTITY_UNRESOLVED

VPG_SAME_SECURITY_NAMESPACE_DRIFT requires independent evidence that:

1. the frozen and current records refer to the same issuer;

2. they refer to the same economic common-equity class;

3. their effective historical period covering the affected dates is
   economically the same;

4. no second competing security/class makes the mapping ambiguous;

5. the difference is attributable to identifier namespace/serialization
   behaviour rather than a genuine historical security transition.

If those conditions cannot be demonstrated:

STOP at:

VPG_IDENTITY_BLOCKED

Do not continue acquisition.

======================================================================
3. DO NOT USE CURRENT SECURITY_SEGMENTS TO RE-IDENTIFY FROZEN ROWS
======================================================================

If VPG is proven to be namespace drift, the scientific correction is NOT:

replace old IDs with new IDs.

Instead preserve the frozen EXP004 security identity as authoritative.

The existing frozen rows already contain:

ticker
day
security_id
unadjustedClose

and were certified before performance.

The supplemental acquisition exists only to attach omitted execution fields.

Therefore create a new enrichment path using:

lake.sec_daily_ohlc

WITHOUT joining:

lake.security_segments.

Fetch only:

ticker
CAST(date AS DATE) AS day
openingPrice
unadjustedClose

for the exact frozen date ranges.

Do not ask the current source to re-derive security_id.

======================================================================
4. FROZEN PRICE-ROW ENRICHMENT KEY
======================================================================

The supplemental OHLC row must be matched to the frozen EXP004 row using:

(ticker, day)

only AFTER verifying that this key is unique in the OHLC source.

The frozen:

security_id

is retained unchanged.

Conceptually:

FROZEN ROW:
(ticker, day, frozen_security_id, frozen_close)

+

SAME-SOURCE OHLC:
(ticker, day, openingPrice, current_close)

=

ENRICHED FROZEN ROW:
(ticker, day, frozen_security_id, openingPrice, frozen_close)

The identity does not get re-resolved.

======================================================================
5. FIRST-QUARTER KEY SAFETY TEST
======================================================================

Use the already acquired first-quarter source evidence where possible.

For:

2013-12-31 through 2014-03-31

verify:

every frozen (ticker, day) exists in lake.sec_daily_ohlc;

every frozen (ticker, day) matches exactly ONE OHLC row;

no duplicate OHLC row makes the key ambiguous;

no frozen row is missing;

no additional OHLC row is admitted to the experiment merely because it exists.

Report:

frozen rows
unique frozen ticker/day keys
matched source rows
missing
duplicate
ambiguous
unused source extras

Required:

missing = 0
duplicate/ambiguous = 0

If not:

STOP at PRICE_KEY_AMBIGUITY_BLOCKED.

======================================================================
6. CLOSE FIDELITY CHECK
======================================================================

For every enriched row require:

supplemental unadjustedClose
==
frozen unadjustedClose

under exact numeric source semantics.

This is the central proof that:

(ticker, day)

retrieved the same economic price observation that originally generated the
frozen row.

Do not introduce a tolerance after inspection.

If exact serialization differs but exact Decimal/numeric equivalence can be
predefined and justified, record that transformation explicitly before using
it elsewhere.

For the first quarter require:

CLOSE mismatch count = 0

before continuation.

======================================================================
7. VPG SPECIFIC CHECK
======================================================================

Explicitly show that the 62 affected VPG rows:

match exactly one OHLC record per date;

have identical frozen and supplemental unadjustedClose;

have valid positive openingPrice;

retain the ORIGINAL frozen security_id:

ticker:VSHw@2010-06-24

inside EXP004.

The current:

ticker:VSHw@2010-06-24#2

may be retained in provenance as observed current-source identity metadata.

It must NOT replace the frozen experiment identity.

======================================================================
8. CREATE A VERSIONED SOURCE-BRIDGE CERTIFICATE
======================================================================

If Sections 1–7 pass, create a compact certificate.

Suggested:

docs/acceleration/exp004_frozen_price_bridge_v001.json
docs/acceleration/exp004_frozen_price_bridge_report.md

Record:

VPG verdict

frozen identity artifact hash

current identity evidence hash

reason the IDs differ

price enrichment key

first-quarter uniqueness result

CLOSE equality result

OPEN coverage

explicit statement:

CURRENT SECURITY_SEGMENTS IS NOT USED TO REWRITE FROZEN EXP004 IDENTITY

This is not a new economic freeze.

It is execution-input provenance.

======================================================================
9. CONTINUE THE REMAINING 27 PRICE ACQUISITIONS
======================================================================

Only after the bridge certificate passes:

continue acquisition across the remaining frozen warmup/Development quarters.

Use the NEW price-only query:

SELECT
    ticker,
    CAST(date AS DATE) AS day,
    openingPrice,
    unadjustedClose
FROM lake.sec_daily_ohlc
WHERE date BETWEEN ...
ORDER BY ticker, date

or exact equivalent required by the source.

Do not join security_segments.

Chunk using the already frozen 28-quarter plan/dates.

Reuse completed first-quarter evidence rather than blindly re-requesting it.

======================================================================
10. EVERY QUARTER MUST RECONCILE TO FROZEN ROWS
======================================================================

For every quarter:

take the existing frozen EXP004 rows as the required population.

Join supplemental prices to those rows by:

ticker
day

Require:

one OHLC row for every frozen row;
no ambiguous duplicates;
supplemental CLOSE == frozen CLOSE;
openingPrice finite and > 0.

Report per quarter:

frozen rows
enriched rows
missing
duplicates
CLOSE mismatches
missing OPEN
invalid OPEN

Do NOT require a newly generated current security_id.

The frozen security_id remains the identity key for portfolio construction.

======================================================================
11. NEW UNEXPECTED IDENTITY DRIFT
======================================================================

Because the new acquisition no longer re-runs identity resolution, current
security_segments drift should not affect the price bridge.

However, if the price source itself demonstrates a genuinely ambiguous
(ticker, day) observation:

STOP.

Do not create a generalized repair rule.

If another identity issue emerges independently of price enrichment:

report it specifically.

Do not generalize the VPG alias to unrelated securities.

======================================================================
12. COMPLETE DEVELOPMENT OPEN COVERAGE
======================================================================

After all quarters reconcile, calculate:

total frozen price rows

total enriched rows

unique frozen stable IDs

required Development execution security/session pairs

valid OPENs

missing OPENs

invalid OPENs

Required for execution:

every actually required execution security/session must have one positive,
finite OPEN.

Do not substitute CLOSE.

======================================================================
13. SPY
======================================================================

Then acquire/certify SPY separately from:

lake.sec_daily_ohlc

or the already approved same-source price surface.

SPY is not part of the CS candidate universe.

Required:

2015-01-02 inception OPEN

all later OPEN/CLOSE sessions needed by:

buy-and-hold NAV
one-session-delay robustness

Do not bind SPY to common-stock security_segments merely for symmetry.

Freeze its price-source identity separately.

======================================================================
14. DIVIDENDS
======================================================================

Only after OPEN enrichment passes:

inspect the already documented:

lake.dividends

surface.

Acquire dividends only for:

securities that can actually be held by the frozen four momentum strategies;

EW holdings as required;

SPY.

Do not download an unrelated full-market dividend history unless efficient
source mechanics make that unavoidable and bounded.

Preserve available fields exactly.

Do not invent:

pay date
record date
declaration time

if absent.

======================================================================
15. DIVIDEND ACCOUNTING CONTRACT
======================================================================

The economic design already requires:

cash dividends.

Before performance, freeze one source-supported accounting rule.

If source information can support exact entitlement/payment:

implement it.

If only exDividendDate + cashAmount are available:

determine whether a conservative local entitlement accounting treatment is
defensible for the backtest.

The rule must be chosen before performance.

Do not select the treatment from resulting returns.

If the dividend surface cannot support the frozen cash-dividend policy:

STOP at DIVIDEND_EXECUTION_BLOCKED.

======================================================================
16. ACTUAL HOLDING PATH DISCOVERY
======================================================================

Once OPENs and dividend semantics pass:

construct the frozen strategy holding schedules WITHOUT calculating portfolio
performance.

Use the already-frozen:

rankings
Top20/Top40 targets
EW population
monthly dates

Determine which stable securities would actually be held and over what dates.

This is execution-path certification, not performance analysis.

Do not calculate:

returns
Sharpe
paired excess
winner

yet.

======================================================================
17. TERMINAL EVENTS — ONLY FOR ACTUAL HOLDINGS
======================================================================

Inspect the actual frozen holding paths for:

ticker rename
security disappearance
merger
delisting
cancellation
class transition
other terminal lifecycle event

If none occur while held:

record zero observed held-terminal requirements and continue.

If they occur:

resolve ONLY those exact affected securities/events.

Do not start a market-wide lifecycle audit.

Require exact economics where needed:

cash consideration

stock consideration / successor ratio

explicit evidenced zero recovery

other source-supported terminal value

No:

last-price forever
silent drop
current-symbol substitution
assumed zero.

If an actually held terminal event cannot be valued:

STOP at TERMINAL_EXECUTION_BLOCKED.

======================================================================
18. PRE-PERFORMANCE LOCAL CERTIFICATE
======================================================================

If all execution-input gates pass, create:

exp004_local_execution_certificate_v004.json

or next repository-consistent version.

It must bind:

unchanged EXP004 spec hash

unchanged methodology hash

local engine hash

frozen input hashes

frozen-price-bridge hash

all OPEN source hashes

SPY source hash

dividend contract/source hash

split source hash

terminal-resolution hash if applicable

exact population reconciliation

Validation access count = 0

Test access count = 0

performance_executed = false

Push this certificate BEFORE calculating a single EXP004 economic metric.

======================================================================
19. THEN RUN DEVELOPMENT
======================================================================

If v004 passes:

DO NOT STOP FOR ANOTHER OWNER REVIEW.

Run the frozen EXP004 Development programme.

Scored folds:

2017
2018
2019
2020

Evaluate:

M180_K20
M180_K40
M365_K20
M365_K40
EW
SPY

Then execute:

six full-Development replays

using the exact frozen contract.

======================================================================
20. PERFORMANCE
======================================================================

Use only predeclared metrics:

total return
zero-RF Sharpe
Sortino
annualized volatility
max drawdown
turnover
participation
fold results

paired mean daily excess vs EW

comparison versus SPY

Do not change the selection statistic.

Do not add a new alpha parameter.

Do not optimize after seeing results.

======================================================================
21. SELECTION
======================================================================

Retain the existing frozen advancement rules.

Require:

positive incremental performance versus EW;

fold consistency;

adequate participation;

no critical data/execution failure;

complete four-cell surface.

Do not simply choose highest Sharpe.

Apply the frozen deterministic tie-break.

======================================================================
22. ROBUSTNESS
======================================================================

Only after primary Development:

+10 bps per side

+20 bps per side

one-session execution delay

bull/bear descriptive decomposition

high/low-volatility descriptive decomposition

No extra tests.

======================================================================
23. SEALED PERIODS
======================================================================

Do not access:

2021–2023 Validation

2024 Test

2025+

Required final counts:

Validation market/outcome accesses = 0
Test market/outcome accesses = 0

No preview.

======================================================================
24. FINAL STATUS
======================================================================

Allowed statuses:

VPG_IDENTITY_BLOCKED

PRICE_KEY_AMBIGUITY_BLOCKED

SOURCE_RECONCILIATION_BLOCKED

LOCAL_EXECUTION_INPUTS_BLOCKED

DIVIDEND_EXECUTION_BLOCKED

TERMINAL_EXECUTION_BLOCKED

NO_EXP004_CANDIDATE_ADVANCES

EXP004_DEVELOPMENT_MIXED

EXP004_CANDIDATE_READY_FOR_VALIDATION_REVIEW

If an economic result runs:

do not automatically open Validation.

Stop for owner review.

======================================================================
25. DO NOT START ANOTHER RESEARCH LOOP
======================================================================

Do not:

create EXP008

search new event sources

add vendors

change momentum horizons

change K

change universe

change costs

change benchmarks

retry Nexus backtesting

start Phase 4B

start live/paper

If the bounded frozen-row enrichment fails:

report the exact blocker and stop.

======================================================================
26. TESTS
======================================================================

Add focused tests for:

VPG namespace-drift evidence

current security_segments never rewriting frozen ID

price-only query excludes security_segments join

ticker/day uniqueness

duplicate ticker/day fail-closed

missing price row fail-closed

frozen/new CLOSE equality

VPG frozen ID preservation

positive OPEN validation

quarter reconciliation

SPY separate source binding

dividend rule

actual-held terminal detection

sealed periods

certificate before metrics

all previous synthetic execution fixtures unchanged

======================================================================
27. FINAL DELIVERY
======================================================================

Report:

starting HEAD
final HEAD
commits
hosted CI

VPG:

old ID
new ID
issuer/class evidence
effective-span evidence
namespace-drift verdict

PRICE BRIDGE:

all 28 quarter results
frozen rows
enriched rows
ticker/day ambiguities
CLOSE mismatches
OPEN coverage

SPY:
coverage

DIVIDENDS:
events
semantics
coverage

TERMINALS:
actual held cases
resolved
unresolved

CERTIFICATE:
v004 result
hashes

If Development ran:

24 fold evaluations

6 full replays

four-cell metrics

EW

SPY

paired excess

fold consistency

turnover

participation

robustness

candidate selection / no-advance verdict

Validation accesses = 0
Test accesses = 0

Then STOP.

======================================================================
28. OWNER INTENT
======================================================================

The previous source mismatch does not show that the historical price observation
changed.

It shows that re-running a mutable identity join can produce a different
identifier namespace.

EXP004 identity was already frozen.

Do not ask today's security_segments table to redefine yesterday's frozen
identity merely to fetch an omitted price column.

First independently establish what happened to VPG.

Then enrich frozen rows with same-source OHLC fields using the narrowest safe
price key.

If the bridge is defensible:

finish execution certification and RUN DEVELOPMENT.

If it is not:

stop clearly.

No more architecture.