# Phase 4A: candidate-family recommendation

**Recommend government procurement for the next bounded source-only pilot, pending owner approval.** No family has passed all mandatory gates. No event data, prices, signal, strategy or performance was acquired or computed.

| Family | Known score / maximum | Unknown criteria | Possible score interval | Gate status |
| --- | --- | --- | --- | --- |
| Government procurement award announcements | 20/32 | 2 | 20–24 | Deferred |
| FDA drug approval decisions | 18/32 | 2 | 18–22 | Deferred |
| Public merger-enforcement decisions | 15/32 | 2 | 15–19 | Deferred |

Scores are equal-weight ordinal engineering judgments from the predeclared [rubric](phase4a_plan.md), not alpha, sample-size estimates or probabilities. Intervals reflect missing scores, not confidence intervals. Unknown counts/inference prevent advancement for all three. The overlapping ranges do not establish a statistically dominant winner. [All sixteen criteria/rationales](phase4a_candidate_scorecard.json).

## Government procurement

Mechanism: an award may change a recipient’s expected backlog or cash generation. That requires distinguishing incremental work from options/modifications, obligation from ceiling/outlay, and genuinely new information from anticipated procurement. None is a trading signal here.

[USAspending documentation](https://api.usaspending.gov/docs/) and [transaction contracts](https://github.com/fedspendingtransparency/usaspending-api/blob/master/usaspending_api/api_contracts/contracts/v2/transactions.md) expose stable award identifiers and action/modification fields. [Search-date semantics](https://github.com/fedspendingtransparency/usaspending-api/blob/master/usaspending_api/api_contracts/search_filters.md) distinguish transaction/signature/update dates; they do not establish first-public timing. Older historical coverage is advertised, not audited for eligible public issuers. Actual usable/event-cluster counts remain UNKNOWN.

The defense announcement pages were unavailable in this tool (one 403 and one internal error). A publisher search snippet suggests scheduled publication, but it is not an archived historical release or evidence of exact first-public time. The pilot must establish an accessible official dated channel before extending retrieval. No evasion or event-record fetch was attempted.

Why prioritize it: stable transaction lineage and direct recipient-agency relationships can reuse the existing evidence contracts and later graph. In our qualitative judgment, ordinary awards have less intrinsic terminal-conversion burden than merger decisions. Selection, anticipation, repeated contractors and shared budget/agency shocks remain serious obstacles. Nonrecipients or sector peers are candidate comparisons, not certified counterfactuals. Many awards may provide only a few effective clusters.

## FDA drug approvals

[FDA data definitions](https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-data-files) document application/sponsor/status/document structures. [openFDA](https://open.fda.gov/apis/drug/drugsfda/) describes broad approved-product history and transformed API fields. These are documentation capabilities, not proof of historical public-owner coverage, availability or complete rejection/withdrawal outcomes.

Approval can change commercialization prospects, but sponsor/licensing rights, scheduled anticipation and an approval-selected denominator complicate controls. Repeated indications/products are not independent events. A separate complete application/negative-decision frame and dated rights-owner/security bridge would be needed. Its structured records are attractive; the current documented frame makes a balanced treatment/control design harder to justify cheaply.

## Merger-enforcement decisions

The [FTC case directory](https://www.ftc.gov/legal-library/browse/cases-proceedings) provides case/date/status navigation. Its broad enforcement total is not a count of merger decisions for publicly traded parties. Case-update dates and proceedings are not first-public announcement timestamps.

Changes in expected deal completion offer a mechanism, but enforcement is selected, anticipation is substantial and successive announcements per deal create dependence. Acquirer/target roles and cash/stock/ended-security transitions put the hard lifecycle problem inside the treatment itself. A complete untreated-deal frame, announcement chronology and terminal accounting would be required. This ranks below procurement for the cheapest next pilot, not for expected returns.

## Exact proposed next authorization

Approve government procurement as the next family **and authorize a source-only feasibility pilot**, pending review of its exact acquisition manifest. Proposed ceiling: 12 official announcement pages in fixed months January/March/May/July/September/November of 2019 and 2020, choosing the first available dated announcement in each month. Retain all page bytes, with at most one mechanically chosen first listed award per page for detailed identity probing; no amount or current-public-company filtering. This is a deliberately small feasibility frame, not an event-population census. Failed/missing/private-recipient cases remain in the denominator.

Proposed maximum 60 request starts including retries: up to 12 announcement/documentation requests, 12 USAspending award/transaction corroborations, 24 SEC identity documents and 12 OpenFIGI corroborations. No prices, FMP, Tiingo, Orbis, Nexus or Aurora; no source purchase. Freeze exact IDs/URLs/question manifest before dispatch, archive original bytes immediately, use one worker with no more than 2 starts/second and bounded retries consuming the ceiling; persistent 403/429 stops retrieval. Do not broaden the route to evade a failure. Access should be tested within the first authorized requests; a blocked publication channel can end the pilot cheaply.

Required output: observed versus modeled public timing, original award/action/amount semantics, dated recipient-parent/security plausibility, revision/missingness rules, an explicit denominator and effective-cluster sample geometry for a subsequent design. Controls and inferential assumptions must be reviewed before any larger campaign. V003’s filing-specific buffer is not automatically adopted for awards. No event threshold, holding period, effect size, causal identification or null method is selected now.

This proposed scope is **NOT_AUTHORIZED**. Family/pilot approval would not authorize a full backfill, real experiment registration/freeze, performance, graph, causal platform or paper/live activity. Full contract/freeze and any performance require separate explicit authorization. Per owner sections 18/32, stop here for review.

## Review provenance and limitations

[Source review ledger](phase4a_source_review.json): three browser tool calls, nine page opens (six accessible, three unavailable), two searches and four find operations. Hidden transport request totals, individual HTTP clocks and original body hashes are unavailable; private serialized tool observations are hashed and labelled as such. No primary event document/corpus or API data query was acquired. Search/case-page snippets incidentally expose contemporary metadata, but no individual case outcome, issuer or return was selected/analyzed. All derived scientific statements are feasibility judgments, not source certification.
