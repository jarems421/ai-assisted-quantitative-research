You are continuing Research OS.

Repository:
C:\Users\runni\quant\

GitHub:
jarems421/ai-assisted-quantitative-research

Branch:
main

Expected starting HEAD:
62bd3eec74811e148ec83aea9cdceb5da6c5c146

======================================================================
OWNER DECISION
EXP006 — FINAL BOUNDED IDENTITY REDESIGN
POST-MAY-2019 COVER-PAGE IDENTITY
======================================================================

Current state:

HISTORICAL_IDENTITY_BLOCKED

The previous 2015–2020 identity feasibility test returned:

0 / 240 FULLY_RESOLVED

under the existing requirement for:

complete dated listing span
stable class/provider bridge
and certified 20-session lifecycle.

Do NOT scale that failed route to the full population.

Do NOT perform another broad 2015–2020 identity campaign.

The owner authorizes ONE final pre-performance redesign of EXP006 identity and
Development scope.

No post-event returns have ever been accessed for EXP006.

Therefore this redesign is driven entirely by source/data feasibility and is
not performance-selected.

======================================================================
1. NEW FACTUAL BASIS TO VERIFY FROM PRIMARY SEC DOCUMENTATION
======================================================================

Before implementation, verify and archive the relevant official SEC rule /
compliance guidance.

The expected regulatory fact is:

Beginning May 2, 2019, Form 8-K cover pages were amended to require disclosure
for Section 12(b)-registered securities of:

- title of each class;
- trading symbol;
- exchange / market on which registered.

Important distinction:

The HUMAN-READABLE cover-page disclosure requirement generally became
effective May 2, 2019.

Inline XBRL TAGGING of those cover-page fields was phased in later by filer
category.

Therefore:

absence of dei:TradingSymbol / Inline XBRL tags does NOT necessarily imply the
human-readable 8-K cover lacks the required trading symbol.

Use official SEC sources.

Archive exact evidence and hashes.

If this factual basis is wrong:

STOP.

======================================================================
2. DESIGN REVISION — DEVELOPMENT START
======================================================================

Conditionally revise EXP006 Development to:

2019-05-02 through 2020-12-31

Historical confirmation remains:

2021-01-01 through 2026-09-30

and remains unopened.

The earlier 2015–2019-05-01 records remain historical source evidence but are
outside the revised executable Development population.

Reason for revision:

standardized contemporaneous security-identity fields became mandatory on
Form 8-K cover pages.

This is a SOURCE/IDENTITY feasibility revision made before any EXP006
performance.

It is NOT selected from returns.

Record the previous 2015–2020 proposal unchanged as historical design v001.

Create a separately versioned candidate design v002.

Do not silently rewrite prior artifacts.

======================================================================
3. DO NOT USE INLINE XBRL AS THE PRIMARY IDENTITY REQUIREMENT
======================================================================

The previous pass counted Inline symbol observations.

That is insufficient because Inline cover tagging had a phased compliance
schedule.

For filings on or after 2019-05-02, parse the ACTUAL HUMAN-READABLE 8-K cover
page.

Extract the cover-page securities table or equivalent presentation containing:

security class title
trading symbol
exchange / market

Preserve raw source locators.

If Inline XBRL contains the same information:

use it as corroboration.

Do not require it.

======================================================================
4. NEW IDENTITY CONCEPT
======================================================================

Replace the unnecessarily broad requirement:

COMPLETE HISTORICAL LISTING SPAN

with the narrower experiment-relevant requirement:

EVENT_DATE_TRADABLE_CLASS_CERTIFICATE

This is NOT a general relaxation of identity standards.

It is a separately versioned EXP006-specific certificate.

For an event to pass, contemporaneous evidence must establish at the decision
date:

1. issuer CIK;

2. exact registered security class title;

3. exact trading symbol;

4. exact exchange / principal US market;

5. that this is an eligible domestic common-equity class under the frozen
   class taxonomy;

6. a deterministic provider/permanent-security mapping for that exact
   symbol/class/exchange;

7. an economically resolvable path from entry through the 20-session exit.

The experiment does NOT need to prove the security's complete multi-year
listing history outside the relevant event-to-exit window.

======================================================================
5. WHY THIS IS SCIENTIFICALLY SUFFICIENT
======================================================================

The estimand concerns a 20-session predictive return beginning after a specific
SEC disclosure.

Therefore the necessary identity question is:

"What exact tradable security did this filing identify at the decision time,
and can that exact security be valued through the frozen 20-session horizon?"

It is not:

"Can we reconstruct every listing transition over the issuer's entire
multi-year history?"

Preserve protection against:

current ticker projection
survivorship
multiple share classes
ticker renames
mergers
delistings
security cancellation
terminal consideration

but certify these within the required event-to-exit path.

======================================================================
6. FREEZE A NEW FEASIBILITY SAMPLE
======================================================================

Before retrieving new bodies/provider data, freeze a new deterministic sample
from:

confirmed original Item 2.02 filings
filed 2019-05-02 through 2020-12-31.

Maximum:

300 events.

Cover:

2019
2020

all quarters available after inception

repeat issuers

single-event issuers

shared-accession/cofiler cases

and source-observable:

multiple cover securities
different exchanges
ticker representations

No price-performance selection.

No fame selection.

No survivor filter.

Push the sample before remote acquisition.

======================================================================
7. COVER-PAGE PARSER
======================================================================

Implement a versioned parser for the required cover identity table.

It must support realistic presentation variants:

HTML tables
plain formatted text where necessary
whitespace
Unicode
multiple securities rows
multiple exchanges
multiple symbols

Do not use issuer-specific patches.

For every candidate output zero or more rows:

class_title
trading_symbol
exchange
source_locator
source_hash

Missing fields remain missing.

Do not infer a symbol from company name.

======================================================================
8. COMMON-EQUITY CLASS RULE
======================================================================

Freeze a source-only class taxonomy before provider queries.

Include clearly eligible ordinary/common equity.

Exclude where identifiable:

preferred stock
depositary shares
warrants
rights
units
debt
notes
convertible debt
ETF / fund-like classes

Do not assume every 12(b) security row is common equity.

If exactly one eligible common-equity class exists:

candidate class is deterministic.

If multiple eligible common-equity classes exist:

mark:

MULTIPLE_ELIGIBLE_CLASSES

and apply no discretionary choice yet.

Measure how common this is.

======================================================================
9. DATED IDENTITY CERTIFICATE
======================================================================

A passing event requires a contemporaneous cover-page identity tuple:

CIK
class title
symbol
exchange
filing/accession
decision date

This tuple itself is the dated evidence that the registrant represented that
class/symbol/exchange on that filing date.

Do NOT require a separately proven multi-year `effective_from/effective_to`
span merely to accept this point observation.

Do NOT reinterpret current OpenFIGI metadata as historical evidence.

The SEC filing provides the date.

======================================================================
10. PROVIDER / PERMANENT-ID BRIDGE
======================================================================

For each distinct source identity tuple, test the existing configured routes.

Prefer:

SEC dated tuple
+
OpenFIGI
+
configured market-data provider metadata

OpenFIGI is allowed to translate a precise SEC-dated:

symbol + exchange + class context

into candidate permanent identifiers.

The historical dating comes from SEC, not OpenFIGI.

Require deterministic mapping.

If multiple OpenFIGI/provider securities plausibly match:

AMBIGUOUS_PROVIDER_MAPPING.

No first-match choice.

Cache mapping by distinct dated security identity, not event.

======================================================================
11. EVENT-TO-EXIT PATH CERTIFICATE
======================================================================

The lifecycle requirement is now bounded to:

eligible entry
through
20th regular-session exit

for that exact event.

Before any strategy-return computation, certify that the provider can represent
the security throughout this path.

Required cases:

ordinary continuous trading

split

cash dividend

ticker rename

exchange change where encountered

merger / cash acquisition

stock consideration

delisting / cancellation

class conversion

If no terminal event occurs within the 20-session path:

a provider-supported continuous path is sufficient.

Do NOT require proof of future lifecycle beyond the frozen exit date.

======================================================================
12. IMPORTANT PERFORMANCE BOUNDARY
======================================================================

This identity/path certification may inspect only what is necessary to establish:

presence of sessions
identifier continuity
corporate actions
terminal-event terms
price-field availability

Do NOT calculate:

event return
control return
20-session return
paired effect
P&L
alpha
Sharpe

before freeze.

If code must verify that OPEN values exist, existence/null status is allowed.

Values themselves should not be summarized or used in design decisions.

======================================================================
13. COVERAGE GATE
======================================================================

Retain the 95% standard.

But measure it against the REVISED event-date/path certificate, not the failed
full-history-span definition.

Report:

sample candidates

valid SEC cover identity tuple

single eligible common class

multiple eligible classes

provider/permanent-ID mapped

20-session path certified

fully resolved under v002 identity definition

coverage %

coverage by:
2019
2020
quarter
exchange
repeat/single issuer

Also report failures by reason.

PASS requires:

>=95% fully resolved

AND

no strong systematic failure in ended/renamed/multiple-class cases that would
create obvious survivorship bias.

If <95%:

STOP.

Do not lower the threshold.

======================================================================
14. CHECK WHETHER THE REGULATORY BOUNDARY ITSELF WORKS
======================================================================

The source scope begins exactly:

2019-05-02

because of the cover-page rule effective date.

Do not move inception later simply because coverage improves.

If early post-rule filings exhibit transition/noncompliance, retain them as
failures.

The purpose is to test whether this regulatory boundary creates a defensible
historical identity surface.

Do not search multiple inception dates.

======================================================================
15. IF SAMPLE PASSES — SCALE
======================================================================

If the <=300 event sample passes >=95%:

scale the event-date identity/path contract to the full confirmed Item 2.02
population from:

2019-05-02 through 2020-12-31.

Scale using distinct security identities/provider mappings wherever possible.

Do not perform one vendor mapping request per event unnecessarily.

Aggregate final trading observations by:

security identity
decision date

after resolving cofilers/source lineage.

Preserve all accessions.

======================================================================
16. UNKNOWN ITEM STATUS
======================================================================

Retain the existing:

113 keys / 107 accessions

UNKNOWN_ITEM_STATUS contract.

Only unknowns whose source date lies inside the revised Development period are
relevant to the revised missingness report.

They remain neither events nor controls.

Do not restart recovery.

Report their revised-period count.

======================================================================
17. CONTROL POPULATION
======================================================================

Controls must satisfy the SAME identity standard.

A non-Item filing cannot become a control merely because its ticker is easy to
resolve.

Construct control eligibility only from:

confirmed NON_ITEM202 original 8-Ks

inside the revised 2019-05-02–2020-12-31 population

with the same event-date identity/path certificate.

Unknown Item filings cannot be controls.

Identity-unresolved controls cannot be controls.

This symmetry is mandatory.

======================================================================
18. MARKET PROVIDER CERTIFICATE
======================================================================

If identity scaling passes:

complete the provider certification already required by EXP006.

Verify on predeclared fixtures:

normal security
split
dividend
ticker rename
ended security
terminal corporate action if present

No paid upgrade.

No Nexus historical execution.

No Aurora.

If current configured sources cannot preserve terminal economics:

MARKET_DATA_BLOCKED.

======================================================================
19. MATCHING
======================================================================

Then freeze the formal comparison rule before outcomes.

Use only PRE-EVENT:

industry
size
momentum
calendar proximity

as already approved.

Unknown/unresolved filings cannot enter.

Freeze deterministic tie-breaking.

No future outcome matching.

SPY remains descriptive.

======================================================================
20. INFERENCE
======================================================================

Use the actual REVISED Development geometry with synthetic outcomes only.

At most three inference methods.

Stress:

repeated issuers
calendar clustering
earnings seasons
industry/common shocks
persistent common components
20-session overlap
heterogeneity
missing matches

Select on calibration and coverage, not power alone.

Freeze before real outcomes.

======================================================================
21. POWER
======================================================================

Using synthetic outcomes report:

0.00 pp
+0.50 pp
+1.00 pp

under the actual revised 2019-05-02–2020-12-31 geometry.

The shorter Development period may reduce independent information.

If the already approved +0.50pp materiality threshold is effectively
untestable:

STOP at POWER_BLOCKED.

Do not extend the period backward to fix power.

Do not open confirmation.

======================================================================
22. DESIGN V002
======================================================================

If identity/provider/matching/inference/power all pass:

create the final versioned EXP006 design using:

FEATURE:
confirmed original 8-K Item 2.02

DEVELOPMENT:
2019-05-02 through 2020-12-31

CONFIRMATION:
2021-01-01 through 2026-09-30

AVAILABILITY:
existing certified v003 conservative date envelope

IDENTITY:
new event-date tradable-class + 20-session path certificate

HORIZON:
20 regular trading sessions

COST:
10 bps per side

ROBUSTNESS:
20 bps per side
+1-session delay

MATERIALITY:
paired net mean >= +0.50 percentage point
AND positive two-sided 95% lower endpoint

TRIAL CEILING:
12

UNKNOWN ITEM STATUS:
explicitly retained/excluded symmetrically

Document explicitly that Development inception was revised pre-performance
because standardized Form 8-K security-identity disclosure became effective
May 2, 2019.

======================================================================
23. PROOF + FREEZE
======================================================================

Run Proof v2.

If all mandatory gates pass:

create/register:

EXP006_SEC_ITEM202_PREDICTIVE

Push a distinct:

PRE-PERFORMANCE FREEZE

commit.

At that commit:

performance evaluations = 0
confirmation accesses = 0

Do not amend or rewrite it later.

======================================================================
24. DEVELOPMENT
======================================================================

Only after the pushed freeze commit exists:

run the single frozen Development evaluation.

No redesign afterward.

No alternative inception.

No alternate identity rule.

No alternative class selection.

No alternative horizon.

No alternative matching.

No alternative inference.

Historical confirmation remains unopened.

confirmation_access_count = 0.

======================================================================
25. VERDICT
======================================================================

Use:

DEVELOPMENT_FAIL
DEVELOPMENT_MIXED
DEVELOPMENT_PASS_FOR_CONFIRMATION_REVIEW

PASS still requires BOTH:

paired net mean >= +0.50 percentage point

AND

positive two-sided 95% lower confidence endpoint.

No post-result rescue.

======================================================================
26. FINAL STOP IF THIS IDENTITY REDESIGN FAILS
======================================================================

This is the final bounded public/free-data identity repair for EXP006.

If the post-May-2-2019 source identity sample fails the unchanged 95% standard:

ABANDON_EXP006_SOURCE_FEASIBILITY

Preserve the hypothesis as untested.

Do NOT:

launch another identity source search;
add another commercial provider;
lower the threshold;
move inception again;
use current tickers;
use survivor-only data;
start Phase 4B merely to rescue EXP006.

The research result would be:

Item 2.02 economic hypothesis untested because reproducible historical
security identity could not be certified from the authorized source stack.

That is an acceptable result.

======================================================================
27. TESTS
======================================================================

Add tests for:

post-2019 raw cover identity parsing

cover identity without Inline XBRL

multiple securities rows

single common class

preferred/warrant exclusion

multiple common classes -> ambiguous

SEC dated identity + current OpenFIGI mapping does not become dated by itself

provider mapping ambiguity

20-session path continuous

rename within path

split within path

dividend within path

terminal event unresolved -> blocked

no need for lifecycle evidence after exit

pre-May-2-2019 event ineligible under revised design

controls use same identity rule

unknown Item excluded from both populations

confirmation inaccessible

freeze before performance

Public CI remains network-free.

======================================================================
28. FINAL DELIVERY
======================================================================

Report:

starting HEAD
final HEAD
commits
hosted CI

SEC RULE:
official evidence
effective date
human-readable disclosure vs Inline-tagging distinction

REVISED POPULATION:
confirmed Item events 2019-05-02–2020-12-31
confirmed non-Item controls
unknown source states

IDENTITY SAMPLE:
sample size
cover identity success
single-class rate
provider mapping rate
path certification rate
fully resolved %
coverage by year/quarter
failure reasons

If scaled:
full event identity coverage
control identity coverage
renames
multiple classes
terminal cases

If continuation reaches later gates:
provider
matching
inference
power

If frozen:
EXP006 spec hash
freeze SHA

If Development runs:
event count
matched pairs
net paired mean
95% CI
p-value
materiality
verdict

confirmation accesses MUST equal zero.

Then STOP.

======================================================================
29. OWNER INTENT
======================================================================

Do not solve more identity history than the experiment needs.

The previous test correctly showed that public/current metadata does not provide
complete historical listing spans.

However, from May 2, 2019 onward, the SEC filing itself should provide a
contemporaneous security-class / trading-symbol / exchange observation.

Test whether that standardized regulatory surface is sufficient to identify the
actual tradable class and certify its 20-session path.

If yes:

continue toward freeze.

If no:

EXP006 ends as a documented source-feasibility failure.

No more planning loops.