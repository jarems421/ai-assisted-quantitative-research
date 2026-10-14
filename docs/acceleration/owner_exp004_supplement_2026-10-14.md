You are continuing Research OS.

Repository:
C:\Users\runni\quant\

GitHub:
jarems421/ai-assisted-quantitative-research

Branch:
main

Expected starting HEAD:
dea0f93adb12c0c21172b242b1800718f6d0bc67

======================================================================
OWNER DECISION
EXP004 — SUPPLEMENTAL EXECUTION INPUT ACQUISITION
======================================================================

Current state:

LOCAL_EXECUTION_OPEN_PRICES_BLOCKED

EXP004 economic hypothesis remains frozen and untested.

The local engine passed synthetic certification but real execution stopped because
the existing 28 EXP004 price extracts contain:

ticker
day
security_id
unadjustedClose

and do NOT contain execution OPEN prices.

This is now authorized for repair.

IMPORTANT:

Earlier repository evidence already shows that the SAME source table:

lake.sec_daily_ohlc

has been queried successfully for fields including:

openingPrice
closingPrice
unadjustedClose

in prior EXP002 source work.

Therefore this pass is NOT:

a new data vendor;
a new source family;
a new experiment;
a change to the frozen execution contract.

It is a bounded supplemental acquisition of omitted execution fields from the
same historical source.

If the required real execution inputs become certified:

continue automatically to local EXP004 Development.

Do not ask for another planning approval unless a genuine new blocker occurs.

======================================================================
1. PRESERVE HISTORY
======================================================================

Read and preserve:

docs/acceleration/exp004_local_execution_report.md
docs/acceleration/exp004_local_execution_certificate_v003.json

src/research/exp004_local_execution.py
src/research/exp004_local_preflight.py
src/research/exp004_inputs.py
src/research/exp004_compile.py

experiments/EXP004/spec.json
experiments/EXP004/freeze_versions/v002/
reports/EXP004_development_report.md

and existing raw EXP004 source receipts.

Do NOT modify previous immutable extraction requests/directories.

The 28 CLOSE-only extracts remain historical evidence.

Create a NEW versioned supplemental acquisition namespace.

Suggested:

data/raw/EXP004/execution_inputs_v001/

======================================================================
2. ECONOMIC DESIGN REMAINS UNCHANGED
======================================================================

Do not alter:

Development:
2015-01-02 through 2020-12-31

warmup:
existing frozen warmup

momentum horizons:
180
365 calendar days

portfolio sizes:
20
40

monthly schedule

09:30 OPEN execution

95% nominal deployment

fractional shares

0.10% fee per fill

cash dividends

EW benchmark

SPY buy-and-hold

four-cell surface

folds

selection rule

Validation/Test seals

No CLOSE execution substitution.

No VWAP.
No next-close.
No midpoint.
No new slippage assumption.

======================================================================
3. VERIFY SOURCE SCHEMA BEFORE LARGE ACQUISITION
======================================================================

Use prior repository receipts first.

They already document successful historical queries such as:

SELECT
    ticker,
    date,
    openingPrice,
    closingPrice,
    unadjustedClose,
    volume
FROM lake.sec_daily_ohlc
...

Do not infer schema solely from the table name.

If necessary, perform ONE bounded metadata/schema query for:

lake.sec_daily_ohlc

and archive it.

Required execution field:

openingPrice

Also preserve:

unadjustedClose

for NAV / reconciliation with the already frozen signal source.

If `openingPrice` is unavailable despite prior evidence:

STOP at OPEN_SOURCE_BLOCKED.

======================================================================
4. ACQUIRE OPEN PRICES FROM THE SAME SOURCE
======================================================================

Use the exact historical stable-ID join semantics already used by EXP004.

Acquire:

ticker
day
security_id
openingPrice
unadjustedClose

for the exact frozen warmup + Development date range.

Use:

lake.sec_daily_ohlc
JOIN lake.security_segments

with the same historical effective-span and CS rules.

Do not introduce:

current symbol
current membership
new asset-type logic
new universe screen

Prefer the same quarter-sized/chunked pattern as the existing 28 extracts.

Each new extraction must have:

immutable request
idempotency key
operation ID
row count
part hashes
source receipt

Do not overwrite existing CLOSE-only parts.

======================================================================
5. EXACT RECONCILIATION AGAINST FROZEN PRICE EXTRACTS
======================================================================

Before inspecting any economic result, reconcile the supplemental rows against
the existing frozen CLOSE rows.

For every old row key:

security_id
ticker
day

require an exact corresponding supplemental row.

Report:

old row count
new row count
matched keys
missing keys
extra keys
duplicate keys

For matched rows require:

old unadjustedClose == new unadjustedClose

under exact source representation / declared numeric tolerance if repository
source serialization requires one.

This is critical.

If the supplemental query changes the historical population or CLOSE values
materially:

STOP at SOURCE_RECONCILIATION_BLOCKED.

Do not simply replace the frozen source.

======================================================================
6. OPEN PRICE VALIDATION
======================================================================

For every required execution session:

openingPrice must be:

present
finite
positive

Do not impute missing OPEN.

Do not substitute CLOSE.

Do not use adjacent-day prices.

Map OPEN through the exact historical stable ID/ticker valid on that session.

Report:

required execution security-session pairs
valid OPEN count
missing OPEN count
invalid OPEN count

Any required missing OPEN remains a fail-closed execution issue.

======================================================================
7. SPY EXECUTION INPUT
======================================================================

Acquire SPY execution data from the same historical price source where supported.

Required:

Development inception OPEN
daily or required-session OPENs for any delayed robustness later
daily close/NAV source if needed under the frozen implementation
cash-dividend source

Keep SPY separate from the common-stock candidate population.

Do not force SPY through the CS universe rule.

Freeze its exact provider/source identity separately.

======================================================================
8. CASH DIVIDEND INPUT
======================================================================

The repository already has prior evidence of:

lake.dividends

with at least:

ticker
exDividendDate
cashAmount

and prior bounded use alongside `stock_splits`.

Inspect/describe the exact table schema once if necessary.

Acquire Development dividend events only for securities that can enter the
frozen EXP004 executable populations plus SPY.

Prefer stable-ID/date reconciliation where possible.

At minimum preserve:

ticker
security identity mapping
ex-dividend date
cash amount
any pay/record/declaration fields if the source actually supplies them

Do not invent absent pay dates.

Do not assume an empty query means globally complete zero dividends unless the
source contract supports that claim.

======================================================================
9. DIVIDEND SEMANTICS CERTIFICATE
======================================================================

The frozen design says:

cash dividends.

Before real performance, define one exact local treatment consistent with the
source fields and available evidence.

Do NOT choose treatment based on resulting returns.

If the source supplies sufficient ex-date/payment semantics:

implement them exactly.

If the source only supplies ex-date + cashAmount:

determine whether a defensible frozen local accounting policy can credit the
economic entitlement without introducing lookahead.

Document the limitation.

If no scientifically defensible cash-dividend treatment can be certified:

STOP at DIVIDEND_EXECUTION_BLOCKED.

Do not silently ignore dividends.

======================================================================
10. SPLITS
======================================================================

Reuse the existing frozen split extraction and existing ambiguity policy.

Do not reacquire or redesign split handling unless a schema dependency requires
a bounded verification.

The existing signal-side split treatment remains unchanged.

Execution-side quantity adjustments must use the same source event economics
where applicable.

======================================================================
11. PATH CONTINUITY AUDIT BEFORE PERFORMANCE
======================================================================

After OPEN + dividend input reconciliation, construct the exact REAL frozen
execution paths WITHOUT calculating strategy returns.

You may inspect:

whether a session exists
whether an OPEN exists
whether a CLOSE exists
identity continuity
ticker transitions
corporate-action presence
terminal disappearance

Do NOT calculate:

strategy return
portfolio NAV performance
Sharpe
paired excess
winner

Use the already frozen targets.

For each cell and EW determine which stable IDs would actually be held between
rebalances.

This is allowed because target rankings were already frozen before this task.

======================================================================
12. TERMINAL EVENT DISCOVERY — ONLY ACTUAL HELD PATHS
======================================================================

Do NOT launch a broad corporate-action search across the entire historical
market.

First identify held paths that exhibit:

security disappearance before scheduled rebalance/exit
stable-ID discontinuity
ticker ending without certified continuation
known merger/cancellation/delisting marker

Report exact affected:

security_id
ticker
holding start
first unresolved date
strategy/benchmark

Only those cases require additional lifecycle resolution.

If zero actual held paths require terminal treatment:

record that and proceed.

If terminal cases exist:

run one bounded source-capability review for those exact cases.

Do not search unrelated securities.

======================================================================
13. TERMINAL ECONOMICS
======================================================================

For an actually held terminal security require evidence for one of:

cash merger consideration

stock merger ratio + successor identity

explicit cancellation / zero recovery

other exact economic terminal treatment

Never:

drop the observation
freeze last price forever
substitute today's ticker
assume zero
assume cash at last CLOSE

If any actually-held terminal event cannot be valued:

STOP at TERMINAL_EXECUTION_BLOCKED.

List every affected strategy/benchmark holding.

======================================================================
14. PRE-PERFORMANCE CERTIFICATE V004
======================================================================

If all required execution inputs pass:

create a new execution certificate version.

Suggested:

exp004_local_execution_certificate_v004.json

It must record:

economic spec hash unchanged

methodology hash unchanged

local engine hash

supplemental source query hashes

old/new CLOSE reconciliation

OPEN coverage

SPY source

dividend source + semantics

split source

terminal-path result

population equality

Development-only bounds

Validation accesses = 0
Test accesses = 0

performance_executed = false

Push this certificate BEFORE any strategy metric exists.

======================================================================
15. DO NOT REQUIRE NEXUS
======================================================================

Nexus remains blocked and paused.

Do not:

publish custom indicators

run Nexus backtests

retry historical symbols

contact support

use Aurora

The certified local path is independent.

======================================================================
16. IF CERTIFICATE PASSES — RUN DEVELOPMENT
======================================================================

If and only if v004 passes:

RUN THE ALREADY-FROZEN EXP004 DEVELOPMENT PROGRAMME.

No further owner approval.

Run:

M180_K20
M180_K40
M365_K20
M365_K40
EW
SPY

for scored folds:

2017
2018
2019
2020

then:

six full-Development replays

exactly as already frozen.

======================================================================
17. PERFORMANCE METRICS
======================================================================

Use only frozen metrics and selection logic.

Report:

total return
zero-RF Sharpe
Sortino
annualized volatility
max drawdown
turnover
participation
fold-by-fold performance

paired mean daily excess vs EW

performance vs SPY

No new metric may determine selection.

No new significance rule.

No post-result design changes.

======================================================================
18. ROBUSTNESS
======================================================================

After the primary programme only:

+10 bps per side

+20 bps per side

one-session execution delay

bull/bear descriptive split

high/low-volatility descriptive split

Exactly as already frozen.

No additional robustness search.

======================================================================
19. SEALED PERIODS
======================================================================

Do NOT access:

2021–2023 Validation

2024 Test

2025+

No market values.
No summary.
No preview.

Validation accesses = 0
Test accesses = 0

required at final delivery.

======================================================================
20. STOP CONDITIONS
======================================================================

Stop before performance only if:

same-source OPEN field cannot be acquired

supplemental source keys fail reconciliation

required execution OPENs are missing

SPY execution source fails

cash dividends cannot be treated defensibly

actual held terminal paths cannot be valued

population equality fails

local engine certificate fails

sealed periods cannot remain inaccessible

Do not create another experiment.

Do not return to event-source discovery.

======================================================================
21. REQUEST DISCIPLINE
======================================================================

Authorized remote operations are limited to:

same-source EXP004 execution input acquisition

specifically:

lake.sec_daily_ohlc supplemental execution fields

lake.dividends

and only if needed after held-path audit:

bounded lifecycle evidence for ACTUALLY HELD unresolved terminal cases.

No new vendor.

No paid source.

No Nexus backtest.

No broad market source campaign.

======================================================================
22. TESTS
======================================================================

Add tests for:

supplemental row-key reconciliation

old/new CLOSE equality

positive OPEN validation

missing OPEN fail-closed

SPY separate binding

dividend entitlement

dividend payment/accounting rule

split quantity adjustment

ticker rename stable ID

actual-held-path terminal detection

terminal cash merger

terminal stock merger

terminal unresolved failure

no current-symbol substitution

population equality

sealed Validation/Test guard

certificate-before-performance

existing synthetic fixtures unchanged

======================================================================
23. FINAL DELIVERY
======================================================================

Report:

starting HEAD
final HEAD
commits
hosted CI

SUPPLEMENTAL SOURCE:

price-source table/schema
new row count
matched frozen row count
CLOSE mismatches
OPEN valid/missing/invalid
SPY coverage

DIVIDENDS:

events acquired
source fields
accounting semantics
coverage/issues

TERMINAL PATH:

actually held terminal cases
resolved
unresolved

CERTIFICATE:

v004 PASS/BLOCKED
engine hash
spec hash
methodology hash

If Development executes:

24 fold evaluations
6 full replays

all four-cell results
EW
SPY
paired excess
fold consistency
participation
turnover
robustness
selected candidate if any

Validation accesses = 0
Test accesses = 0

Final status must be one of:

LOCAL_EXECUTION_INPUTS_BLOCKED

LOCAL_EXECUTION_ACTIONS_BLOCKED

NO_EXP004_CANDIDATE_ADVANCES

EXP004_DEVELOPMENT_MIXED

EXP004_CANDIDATE_READY_FOR_VALIDATION_REVIEW

Then STOP.

======================================================================
24. OWNER INTENT
======================================================================

The last stop did NOT show that EXP004 cannot be executed locally.

It showed that the original EXP004 extraction selected only CLOSE even though
the historical OHLC source has previously exposed OPEN fields.

Acquire the omitted execution field from the SAME source.

Reconcile it exactly to the frozen source population.

Then certify only the dividend/lifecycle evidence the actual frozen holdings
need.

Do not invent another research problem.

If the inputs pass:

RUN DEVELOPMENT.