You are continuing Research OS.

Repository:
C:\Users\runni\quant\

GitHub:
jarems421/ai-assisted-quantitative-research

Branch:
main

Expected starting HEAD:
6ac5d8987117778f8e7a60bf808a2300ef03254f

======================================================================
OWNER DECISION
EXP006 — SCALABLE ACCEPTANCE PROVENANCE REPAIR
======================================================================

Current state:

Availability v002 PASSED its scoped original-header chronology audit.

The automatic continuation then stopped at:

SCALABLE_ACCEPTANCE_PROVENANCE_BLOCKED

because the SEC bulk submissions `acceptanceDateTime` field does not reproduce
the original SGML ACCEPTANCE-DATETIME clock under one uniform representation.

The 48-record validation found:

24/48 literal bulk ISO values matched a retained raw-source UTC candidate
24/48 did not

BUT:

48/48 produced the same second-session eligible OPEN in the existing
calendar-only sensitivity.

This distinction is central.

The objective of this pass is NOT to reconstruct the exact raw acceptance
second for all 438,666 census rows.

The scientific requirement needed by EXP006 is narrower:

A scalable timing input must produce an execution eligibility DATE that is
demonstrably no earlier than the raw original acceptance chronology under the
declared uncertainty model.

If that property can be certified conservatively, exact clock reconstruction
is unnecessary.

If it cannot, test the official SEC Feed/Oldloads raw-header route as the
bounded fallback.

No performance is authorized before EXP006 is frozen.

======================================================================
1. PRESERVE CURRENT HISTORY
======================================================================

Do not overwrite or weaken:

docs/acceleration/exp006_freeze_review.md
docs/acceleration/exp006_bulk_clock_validation.json
docs/acceleration/exp006_bulk_bound_sensitivity.json
docs/acceleration/exp006_availability_contract_v002.json
docs/acceleration/exp006_chronology_validation_v002.json
docs/acceleration/exp006_source_coverage.json

The finding:

SCALABLE_ACCEPTANCE_PROVENANCE_BLOCKED

remains historically true for exact raw-clock reconstruction.

Do not relabel the mixed bulk field as original SGML ACCEPTANCE-DATETIME.

======================================================================
2. CHANGE THE CERTIFICATION QUESTION
======================================================================

The frozen execution policy ultimately consumes a trading-session boundary.

Therefore distinguish:

A. EXACT_CLOCK_EQUIVALENCE

from:

B. CONSERVATIVE_CIVIL_DATE_DOMINANCE

EXP006 requires B.

It does not require A if B is independently validated and explicitly modeled.

The test is:

For every audited original header,

BULK_DATE_ENVELOPE >= RAW_ACCEPTANCE_CIVIL_DATE

under every retained plausible interpretation required by the current
availability contract.

If that is true, then:

second regular NYSE session strictly after BULK_DATE_ENVELOPE

cannot be earlier than:

second regular NYSE session strictly after the raw acceptance civil date.

Do not infer exact timestamp equivalence.

======================================================================
3. PREDECLARE BULK DATE ENVELOPE
======================================================================

Before fetching any new raw headers, freeze the following candidate transform.

For each official SEC bulk `acceptanceDateTime` value construct:

1. lexical_date
   = calendar date written directly in the ISO string

2. literal_UTC_to_New_York_date
   = parse the ISO value literally according to its declared offset/Z and
     convert that instant to America/New_York, then take its civil date

3. filed_date
   = SEC FILED AS OF DATE / census filed date

Define:

BULK_DATE_ENVELOPE =
max(
    lexical_date,
    literal_UTC_to_New_York_date,
    filed_date
)

No per-CIK rule.

No per-year offsets.

No guessing whether an individual field is local or UTC.

No learned correction.

No outcome information.

This is intentionally conservative.

The existing second-session rule then becomes:

eligible_open =
09:30 America/New_York on the SECOND regular NYSE trading session strictly
after BULK_DATE_ENVELOPE.

Exact public availability remains UNKNOWN.

Timing class remains modeled, not observed.

Suggested new contract:

EXP006_item202_availability_v003

Do NOT rewrite v002.

======================================================================
4. VALIDATE THE DATE ENVELOPE AGAINST ORIGINAL HEADERS
======================================================================

The prior 48 filings are insufficient to certify scale.

Create a NEW frozen mechanical validation sample BEFORE requesting headers.

Maximum:

240 original filing-header requests

Target sample design:

2015–2020
all four quarters
8-K and 8-K/A
all six years

and deliberate SOURCE-CLOCK stress coverage based only on bulk metadata:

near UTC midnight
near New York midnight
pre-market
regular-session
after-market
Friday
DST transition windows
bulk lexical/raw-like representation class
bulk apparent UTC-converted representation class
the previously observed +4/+5-hour discrepancy class
the previously observed -4/-5-hour discrepancy class

Sampling may stratify on source timestamp representation because that is the
thing being validated.

It may NOT use:

issuer fame
ticker
future survival
prices
returns
Item 2.02 outcome performance

Retain the original 48 separately as the historical first audit.

Do not replace them.

======================================================================
5. PRIMARY PASS CONDITION
======================================================================

For every new sampled accession retrieve the original SEC filing header and
extract:

raw ACCEPTANCE-DATETIME
FILED AS OF DATE
form
accession
CIK

Derive all raw-source candidate civil dates under the already approved v002
uncertainty treatment.

For each filing test:

BULK_DATE_ENVELOPE >= max(raw_candidate_civil_dates)

and compare resulting eligible opens.

Required report:

sample size
year/form/quarter distribution
clock-stress distribution

raw civil-date exact matches
bulk envelope same-day
bulk envelope later-day
raw date later than envelope

same eligible open
bulk-envelope later eligible open
bulk-envelope earlier eligible open

The critical unacceptable count is:

BULK_ENVELOPE_EARLIER_THAN_RAW = 0 required

and:

ELIGIBLE_OPEN_EARLIER_THAN_RAW_POLICY_OPEN = 0 required

If either is nonzero:

do not patch individual records.

Proceed to the Feed/Oldloads fallback section.

======================================================================
6. DO NOT REQUIRE CLOCK EQUALITY
======================================================================

This repair explicitly does NOT require:

bulk ISO timestamp == SGML raw timestamp

because the previous audit already disproved that as a universal mapping.

The scalable bulk field is being evaluated only as an input to a conservative
DATE envelope.

If the envelope is later than the raw date, that is acceptable.

It is conservative timing latency.

Measure the delay distribution.

Report how often the new policy delays execution by:

0 sessions
1 session
2+ sessions

relative to the raw-header v002 rule.

This is a source/timing statistic, not market performance.

======================================================================
7. INDEPENDENT OFFICIAL ARCHIVE CROSS-CHECK
======================================================================

Independently test the official SEC historical raw-archive route.

SEC documentation describes:

/Archives/edgar/Feed/

and:

/Archives/edgar/Oldloads/

as historical filing archives, with Oldloads containing public submissions
complete with filing headers.

Do not assume the route works at the required scale merely from documentation.

Run a bounded feasibility test.

Select no more than:

12 filing days

mechanically across 2015–2020.

Prefer days containing records from the new validation sample.

For each route tested record:

HTTP status
archive path
compressed/uncompressed size
hash
whether accession lookup is possible
whether original ACCEPTANCE-DATETIME is recoverable
whether recovered header matches the direct original accession header

Do not fetch six years of archives in this section.

This is only a scalability/fallback feasibility certificate.

======================================================================
8. FALLBACK DECISION TREE
======================================================================

CASE A — DATE ENVELOPE PASSES

If:

bulk envelope never precedes raw candidate acceptance date

AND

eligible open never precedes raw-v002 eligible open

across the frozen expanded sample,

then certify:

SCALABLE_ACCEPTANCE_DATE_BOUND_READY

The scalable contract may use the bulk DATE envelope for full-population
eligibility.

It must explicitly state:

- bulk exact clock provenance remains unresolved;
- raw acceptance second is not reconstructed;
- exact public availability is UNKNOWN;
- the modeled execution bound was validated against original SEC headers;
- conservative later eligibility is accepted by design.

Do NOT require original raw headers for every census row.

Proceed automatically to remaining EXP006 gates.

CASE B — ENVELOPE FAILS BUT FEED/OLDLOADS WORKS

If any sampled raw acceptance civil date is later than the envelope:

do not broaden the transform after seeing the failures.

Instead evaluate the already predeclared SEC Feed/Oldloads route.

If an official archive supplies original filing headers reproducibly and can
be acquired/streamed at reasonable scale:

define a bounded raw-header acquisition plan.

Before executing it, estimate:

number of required archive files
total expected compressed bytes
total expected uncompressed bytes
request count
disk requirement
runtime

Do not begin an enormous acquisition blindly.

Prefer streaming extraction of only census accessions.

If feasible within ordinary local resources, proceed.

If not:

STOP at RAW_HEADER_SCALING_BLOCKED.

CASE C — BOTH FAIL

STOP.

Do not invent offsets.

======================================================================
9. IMPORTANT OPTIMIZATION: DO NOT REQUIRE ACCEPTANCE FOR IRRELEVANT ROWS
======================================================================

Avoid processing hundreds of thousands of raw headers unnecessarily.

Maintain the source-defined census of all 8-K / 8-K/A rows.

But expensive raw-source timing acquisition, if needed, should be delayed
until the population has been narrowed by PRE-PERFORMANCE source contracts.

It is permissible to first determine:

source Item 2.02 classification
identity eligibility
benchmark candidate eligibility

using pre-outcome information.

Then acquire original acceptance headers only for rows that could enter:

event population

or

formal matched controls

provided the selection rule is frozen before outcomes and unavailable timing
causes fail-closed exclusion.

Do not use price returns to decide which headers to obtain.

This prevents a 400k-request anti-pattern.

======================================================================
10. ITEM 2.02 CLASSIFICATION CERTIFICATE
======================================================================

If scalable timing is repaired, continue.

The current bulk labels show approximately:

108,364 original Item 2.02 labels
983 amendment Item 2.02 labels

but they remain provisional.

Freeze a mechanical primary-document validation sample.

Maximum:

96 filings

Balanced where feasible across:

2015–2020
quarters
Item 2.02 positive
Item 2.02 negative
8-K
8-K/A

Compare:

bulk/source Item declaration

against:

original SEC header and primary filing content.

Report:

TP
TN
FP
FN
UNKNOWN
coverage

Do not use market outcomes.

If classification is materially unreliable:

STOP at ITEM202_CLASSIFICATION_BLOCKED.

Do not download every filing body merely to prove the label.

======================================================================
11. PAC / VERSION / MISSINGNESS
======================================================================

Continue the previously required PAC/version review.

The SEC documents that:

daily/feed/oldload indexes retain historical states differently from rebuilt
full/quarterly indexes after post-acceptance corrections/deletions.

Explicitly quantify what this experiment can and cannot reconstruct.

Preserve:

current-index census
amendments
duplicate/cofiler states
removed/unavailable states where evidenced
unknown historical deletions

Do not claim an untouched point-in-time index vintage unless the evidence
supports one.

Do not silently delete a filing because its current body is absent.

======================================================================
12. CONTINUE THE EXISTING EXP006 FREEZE CLOSURE
======================================================================

If timing and Item classification gates pass, automatically continue the prior
owner-authorized closure.

Do NOT return for another planning approval.

Continue only what remains:

dated issuer -> security/class identity

cofiler reconciliation

renames / ticker changes

ended classes / delistings / mergers / terminal value

market-data provider certification

population-preserving local execution

exact deterministic matching rule

inference calibration

synthetic power/effective geometry

Proof v2 final pre-freeze compilation

Do not reopen:

feature
20-session horizon
Development dates
confirmation dates
cost
materiality
trial ceiling

Those remain owner-approved.

======================================================================
13. HISTORICAL IDENTITY
======================================================================

Build only the minimum identity layer needed by EXP006.

Required distinction:

issuer CIK
legal filer
security/class
exchange
ticker
effective date span
provider identifier

No current-ticker shortcut.

No survivor-only join.

Cofilers must not create duplicate independent trades.

Unresolved identities stay unavailable.

Before performance report:

mapped events
unresolved events
renamed classes
ended classes
terminal paths resolved
terminal paths unresolved

If performance would require dropping unresolved ended securities:

BLOCK.

======================================================================
14. MARKET DATA
======================================================================

Inspect existing configured credentials without printing or committing secrets.

No paid upgrade.

No Nexus historical execution.

Certify one existing provider on a tiny predeclared sample covering where
possible:

ordinary security
split
dividend
ticker rename
ended/delisted security

Required:

historical OPEN
corporate actions
ended-security support
reproducible identifier mapping

If no existing provider can preserve the required population:

MARKET_DATA_BLOCKED.

======================================================================
15. MATCHING RULE
======================================================================

Freeze BEFORE outcome returns:

contemporaneous non-Item-2.02 comparison selection using the already approved
dimensions:

industry
size
momentum
calendar proximity

No future fields.

No return-based weights.

No post-result matching changes.

Deterministic tie break.

Missing valid match => unavailable.

SPY remains descriptive only.

Hash the matching rule before Development market outcomes are calculated.

======================================================================
16. INFERENCE
======================================================================

Before performance use REAL event geometry but SYNTHETIC outcomes only.

At most THREE inference candidates.

Must stress:

repeated issuers
calendar clustering
earnings seasons
industry/common factors
persistent common components
20-session overlap
unequal event counts
heterogeneity
missing controls

Choose based primarily on:

null rejection near 5%
coverage near 95%
common-factor robustness
compatibility with actual geometry

not on power alone.

Retain failed methods.

Freeze the chosen procedure before returns.

If none calibrates:

INFERENCE_BLOCKED.

======================================================================
17. POWER
======================================================================

Using synthetic outcomes only report power at:

0.00 pp
+0.50 pp
+1.00 pp

for the frozen procedure and actual source/matching geometry.

Do not equate filing rows with independent N.

If +0.50 pp is effectively untestable under the declared materiality rule:

STOP before freeze.

======================================================================
18. PRE-PERFORMANCE FREEZE
======================================================================

If every mandatory gate passes:

create/register:

EXP006_SEC_ITEM202_PREDICTIVE

Run Proof v2.

Freeze exact hashes for:

source census
Item classification
availability v003 / selected raw fallback
calendar
identity
market-data source
matching
execution
cost
inference
trial family
environment/code

At this point:

performance_executed = false
confirmation_accesses = 0

Commit and PUSH the frozen EXP006 specification.

This PRE-PERFORMANCE FREEZE commit must exist before any Development return
artifact.

Do not amend it.

======================================================================
19. DEVELOPMENT
======================================================================

Only after the pushed freeze commit exists:

Development performance is authorized for:

2015-01-01 through 2020-12-31

Run exactly the frozen evaluation.

No tuning.

No alternative horizon.

No alternate matching.

No alternate inference.

No redesign.

Historical workflow-held-out confirmation:

2021-01-01 through 2026-09-30

must remain unopened.

confirmation_access_count = 0

required.

======================================================================
20. DEVELOPMENT VERDICT
======================================================================

Use only:

DEVELOPMENT_FAIL
DEVELOPMENT_MIXED
DEVELOPMENT_PASS_FOR_CONFIRMATION_REVIEW

PASS requires BOTH:

paired net 20-session mean >= +0.50 percentage point

AND

positive two-sided 95% lower confidence endpoint versus zero.

Do not promote a merely positive point estimate.

Do not redesign after failure.

======================================================================
21. REQUEST DISCIPLINE
======================================================================

New direct-header validation:

maximum 240 filing-header starts

Feed/Oldloads feasibility:

maximum 12 filing-day archive GETs
plus minimal index/HEAD discovery needed

Primary classification validation:

maximum 96 original filing/body starts

Use caches first.

Use SEC bulk/index surfaces first.

No hundreds-of-thousands individual request campaign.

No denial bypass.

No purchase.

No Nexus/Aurora.

======================================================================
22. TESTS
======================================================================

Add tests for:

bulk lexical-date extraction
literal UTC -> New York civil date
date-envelope max rule
raw acceptance date equal envelope
raw acceptance date earlier than envelope
raw acceptance date later than envelope => fail
DST
midnight
filed-date adjustment
eligible-open monotonicity
bulk envelope can only preserve/delay raw-rule open
Feed/Oldloads exact-header reconciliation
classification confusion accounting
unavailable timing fail-closed
historical v001/v002 artifacts unchanged
held-out confirmation inaccessible
freeze-before-performance enforcement

Public CI must remain network-free.

======================================================================
23. DO NOT OVERENGINEER
======================================================================

Do not build:

another architecture layer
a general corporate graph
a general EDGAR lake
a generalized timestamp inference engine
a learned timezone classifier
a new strategy
a new external integration
Phase 5
live/paper trading

This is one source-provenance repair followed by existing EXP006 closure.

======================================================================
24. FINAL DELIVERY
======================================================================

Report:

starting HEAD
final HEAD
commits
hosted CI

DATE PROVENANCE:
expanded validation sample size
raw-date dominance failures
same eligible open count
later eligible open count
earlier eligible open count
delay distribution
Feed/Oldloads feasibility result

SOURCE:
census rows
8-K
8-K/A
CIKs
certified Item 2.02 count
unknown classification count
PAC/version limitations

If closure continues:

identity coverage
terminal coverage
market-data provider
benchmark match coverage
inference calibration
synthetic power

If freeze occurs:

EXP006 spec hash
freeze commit SHA

If Development occurs:

eligible event count
matched-pair count
net paired effect
95% CI
p-value
materiality result
Development verdict

confirmation accesses must equal zero.

Then STOP.

======================================================================
25. OWNER INTENT
======================================================================

The project has already established that exact bulk-clock reconstruction is not
available from one universal mapping.

Do not solve a harder problem than the experiment needs.

The actual safety property is:

execution must not occur before the source chronology permits it.

A conservative date bound is scientifically acceptable if:

it is declared before performance,
validated against primary headers,
never produces an earlier eligible open,
and its uncertainty is explicit.

If that works, continue.

If it does not, use the official raw archive fallback.

Do not create another planning loop.