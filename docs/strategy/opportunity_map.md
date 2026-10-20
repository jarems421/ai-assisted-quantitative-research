# Opportunity map: operational data with an economic link

**2026-10-20; qualitative research priorities, not expected returns.** The supplied report proposes seven families (PDF pp. 2, 6–14). This map retains all seven, with Certificate Transparency as a component rather than an eighth independent trading hypothesis. No new family is needed to fill the shortlist. [Review](reorientation_review.md) · [Evidence and prior art](evidence_review.md) · [Primary pilot](web_adoption_pilot.md).

## Scores and practical ranking

Scores run from 1, unfavorable or severely unresolved, to 5, comparatively favorable. They express judgment under uncertainty, not measured signal strength or statistical probabilities. E and F are deliberately low: none of these leads has demonstrated a clean signal or a delayed price response here. All dimensions receive equal weight for this rough sum; an access/timing failure overrides any total. Ties are resolved by first-week learning value.

| Key | Dimension |
| --- | --- |
| A | Clear economic mechanism |
| B | Originality/crowding, given visible prior art |
| C | Usable historical information-time evidence |
| D | Listed-asset exposure linkage |
| E | Signal versus noise and confounding |
| F | Credible delayed response |
| G | Liquidity and manageable execution universe |
| H | Time/cost to first honest result |
| I | Fast falsification |
| J | Reusable value if investment hypothesis fails |

| Rank / family | A | B | C | D | E | F | G | H | I | J | /50 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 — public-web adoption | 4 | 2 | 3 | 4 | 2 | 2 | 4 | 4 | 5 | 5 | 35 |
| 2 — software consumption | 3 | 3 | 2 | 3 | 2 | 2 | 4 | 3 | 4 | 4 | 30 |
| 3 — NHTSA quality-report pressure | 4 | 1 | 2 | 4 | 2 | 2 | 4 | 3 | 4 | 4 | 30 |
| 4 — MAUDE reporting changes | 3 | 3 | 1 | 3 | 1 | 2 | 4 | 2 | 3 | 4 | 26 |
| 5 — KEV/OSV propagation | 3 | 1 | 2 | 2 | 2 | 2 | 4 | 2 | 3 | 4 | 25 |
| 6 — documentation/API changes | 3 | 4 | 2 | 3 | 1 | 2 | 4 | 1 | 2 | 3 | 25 |
| 7 — FCC + trademark + web convergence | 4 | 4 | 2 | 2 | 2 | 1 | 3 | 1 | 2 | 4 | 25 |

| Family | Evidence behind the important scores | Availability, first test and principal failure |
| --- | --- | --- |
| Web adoption | Existing commercial investment product lowers B; direct product/vendor bridge supports D. Precomputed technology observations improve H/I. Free tiers, detector changes and crawler selection lower E. No evidence supports F beyond a plausible processing-friction story. | HTTP Archive has documented monthly tables and technology fields. Historical publication/configuration remains to be checked. Start with two vendors, no new crawler. Fail within one day if timing/vintages or affordable export cannot be established. |
| Software consumption | Official graphs and package metadata exist, but developer usage may never monetize. Versioned artifacts improve reproducibility, while current graph resolution and missing original observation times lower C. Existing open-source finance literature limits broad novelty. | deps.dev snapshots, original package requirements and PyPI metadata are real. Actual snapshot depth and economically independent adopters are unmeasured. A bounded source check must establish dated edges, not reconstruct an old graph using today's resolver. |
| NHTSA | Product failures plausibly affect costs/demand, with few security mappings. Close complaint/financial prior art makes B=1. Receipt dates and updateable current files weaken C; publicity and installed fleet size weaken E. | Bulk complaint/communication datasets exist; historical public versions are unproved. Require actual archived publication evidence before a retrospective return test. Do not create a recall-selected sample. |
| MAUDE | Important surveillance record, but FDA explicitly cautions against inferred incidence/rate changes. No device-use denominator, supplement history and reporting incentives weaken A/C/E. Sparse direct finance search results do not prove an empty field. | openFDA exposes weekly updated data; MAUDE bulk/search surfaces have different update descriptions and latest-report behavior. A time-correct reporting-process study might be useful; a defect-rate trading pilot is not ready. |
| Vulnerability propagation | Known cyber/asset-pricing literature and obvious professional monitoring lower B. KEV inclusion can lag initial disclosure; component exposure does not establish a material revenue or liability channel. | CT/OSV/KEV and dependency versions are components, not a dated firm exposure panel. CISA's page was browser-denied in this review; no alternate acquisition attempted. Needs disclosure/exploitation/publication clocks separately. |
| Documentation changes | Potentially unusual incremental measurement, but a very large researcher-choice space and retrospectively selected pages lower E/H/I. Technical launches can precede monetization by months. | Common Crawl supports capture retrieval, not a complete weekly history of a chosen docs site. Freeze page universe and semantic taxonomy before outcomes; no LLM-selected interesting changes. |
| Shadow launch | Independent business traces make A appealing, but subsidiary ownership, confidential filings, variable commercialization lags and three-way historical joins make a first week implausible. | USPTO/FCC/CT surfaces are documented. Application dates and certificate issuance are not product launch or investor-publication times. Test a handful of predeclared cross-source matches before any securities study in a later project. |

**Best first experiment:** narrow public-web adoption, conditional on its one-day source gate. **Best long-term upside:** a credible, inexpensive customer-demand nowcast built from the same family; financial value remains speculative. **Most original combination in this search:** FCC/trademark/web convergence, with docs/API changes another frontier lead. **High-risk long shots:** those two frontier leads and MAUDE defect-pressure inference without reporting-version/exposure evidence. Originality does not override feasibility or prior art.

## Deep dive 1: web adoption, the recommended pilot

**Economic chain:** an independent site adopts a web platform → a detectable customer-side footprint appears → persistent, comparable observations may measure changes in the vendor's active ecosystem → that measurement might help forecast a subsequent disclosed operating metric → only then ask whether returns incorporate it slowly. Each arrow is an empirical claim. One site is not one billable customer, and changed infrastructure need not be changed spending.

Use **Shopify and Wix** as a deliberately selected two-vendor measurement study, not a representative software-stock universe. Shopify's MRR and Wix's Creative Subscriptions ARR are candidate targets with documented business definitions; pricing and product mix affect both. Existing issuer publications establish examples, not a complete historically consistent target panel. Map each product label to its historical issuer/class using dated issuer evidence; do not resolve every customer domain to a listed company.

The simplest source is `httparchive.crawl.pages` and its `technologies` field, restricted to one client and root pages. This avoids building a Common Crawl extraction engine. Do not combine HTTP Archive, CT, CrUX weights and DNS in the first model. Those extra sources create more clocks and choices; reserve them for an evidence-motivated later revision.

The primary measure should be a single persistent net-installation rate on origins successfully observed throughout its lookback. A later confirmation observation moves the signal's availability later; it cannot validate an earlier trade. A missing crawl is not an uninstall. Track common-origin coverage and newly observed/lost origins separately. A detector release causing a jump is a measurement discontinuity, not business growth.

Prior-art status: **studied/commercialized category, potentially useful measurement improvement**. BuiltWith's investor product directly contradicts a strong claim of professional obscurity. This review found no closely matching public paper for the exact proposed two-vendor, source-vintage-controlled transform in its limited search; that is not evidence that funds do not use it. Delayed response is a hypothesis to falsify, not the default.

Fast kill: no usable historical release/configuration evidence; no affordable sample/export; mostly free/invisible usage; or no incremental business-metric information relative to a simple trend baseline. A good operational nowcast with no return edge is still a useful completed research outcome. The full [pilot](web_adoption_pilot.md) supplies dates, schema, controls and gates.

## Deep dive 2: consumption of vendor-linked software, backup 1

**Economic chain:** independent projects choose a vendor's SDK → dependence or usage may indicate demand for that vendor's paid service → demand could precede disclosed customer/revenue changes. Downloads, commits and stars are weak proxies; bots, CI, mirrors, optional dependencies and free usage can dominate.

Proposed tiny scope: the official **Twilio SDK / TWLO** and **Datadog tracing client / DDOG**, two product-to-issuer bridges to verify before collection. Start with declared direct production dependencies only. A package name, official GitHub organization and today's ownership page are insufficient evidence of historical ownership or monetization. These are proposed mappings, not newly certified identities.

Exact candidate sources are [deps.dev API](https://docs.deps.dev/api/v3/), its [`bigquery-public-data.deps_dev_v1` snapshots](https://docs.deps.dev/bigquery/v1/), and original version-specific requirements/tarball hashes from the relevant package registry. PyPI's [`distribution_metadata`](https://docs.pypi.org/api/bigquery/) is a possible independent metadata source where a Python package is used. Do not silently switch ecosystems because one graph looks better. GH Archive is optional provenance, not a substitute for original requirements.

Measure monthly first observed independent dependents per existing dependent count, collapsing repeated releases from one dependent package. Preserve owner/fork/automation ambiguity; packages are not independent purchasing organizations. Use `SnapshotAt` or evidenced original public release time, never the age of an imported package as the age of today's resolved graph. A `Latest` view is not a historical view. Registry publication and a subsequently calculated/exported graph have separate clocks.

Hypothesis: this one consumption measure adds predictive information about the next disclosed paid-usage/customer metric beyond that metric's own trend. Null: it adds none, or only software popularity with no monetization. First falsification is the business-metric comparison; a potential later 20-session return horizon is a tentative common monthly screen, not a natural law of software demand. Sector and momentum controls and a noncommercial-package negative control are necessary.

**Backup limit:** two hours for source/configuration/depth and ownership feasibility, within the shared week budget. Establish whether a defensible 2020–2023 panel exists. Actual oldest snapshot is NOT_VERIFIED; do not promise four years from the overview's “look back” wording. If absent, stop rather than manufacture historical dependency resolutions. If both dated declarations and ownership pass, issue a short fixed backup manifest before measuring its business outcomes. It receives no automatic performance authority from this review.

Prior-art status: **studied broader open-source finance; specific consumption measurement potentially underexplored**. The original 2025 study on corporate code contributions studies announcement reactions, and the open-source innovation working paper also values repository releases. Neither establishes alpha from downstream dependencies; both refute a broad “GitHub has never been studied” pitch. [Contribution study](https://doi.org/10.1111/radm.12749), [author/institution-hosted working paper](https://cba.lmu.edu/media/lmucollegeofbusinessadministration/departments/finance/The%20Private%20Value%20of%20Open-Source%20Innovation.pdf).

## Deep dive 3: NHTSA complaint/communication pressure, backup 2

**Economic chain:** emerging product problems produce owner complaints and technical communications → economically material warranty/remediation/demand risk may become observable before a salient recall → investors might initially underweight it. Media attention, vehicle age/fleet size, reporting campaigns, regulation and known recalls can explain the same pattern.

The [official datasets page](https://www.nhtsa.gov/nhtsa-datasets-and-apis) provides complaint, investigation and manufacturer-communication downloads and layouts. Candidate keys include ODI complaint ID, manufacturer/make, model/year, component, received date and separately evidenced public version date. Inspect actual layouts before adopting field names. Use only **Ford/F** and **General Motors/GM** as an initial proposed US-parent scope; map brands/subsidiaries at the observation date and retain unresolved mappings. No Tesla/famous-recall selection and no “only ultimately recalled vehicles” filter.

Proposed signal: component-specific weekly complaint share within the manufacturer's total observed complaints, compared with its own trailing 52-week share; manufacturer-communication co-occurrence is one fixed corroboration flag, not a searched interaction family. This is **reporting pressure**, not a defect incidence estimate. Fleet/production data would be required for incidence claims. All observed manufacturer weeks belong to the denominator; absent/uncertified files are unavailable, not zero complaints.

Candidate period: 2019–2023, with 2019 for baseline and 2020–2023 for an exploratory screen if version history allows. Received date is not public availability. Require an archived public file or individual publication receipt/version with a defensible upper bound. A guessed 7/30-day receipt lag does not repair revised present-day files. A forward first-seen collector is a separate, slower design, not a retrospective remedy this week.

Null: no incremental future reporting/business-risk or 20-session relative-return information after known recall/investigation information and common auto exposure. A future return screen would measure F/GM against a predeclared auto-sector proxy and SPY, controlling prior momentum; negative controls include pseudo-dates and already-public recall status. Future recalls may be later outcomes, never a sample-selection filter or an input known earlier. Shorts/borrow are not assumed; initially study relative underperformance as measurement, without claiming an executable short portfolio.

Prior-art status: **known and studied**. The 2019/2020 complaint/insider study is unusually close, so any future work must identify a genuine incremental question, such as publication-vintage-controlled component-plus-communication pressure. Its published result does not supply that new result or our sample's timing. [Original paper](https://doi.org/10.1007/s11156-019-00866-9).

**Backup limit:** two hours to inspect a handful of neutral complaint/communication examples and original timing documentation, not download the full corpus. If historical versions/public bounds are unavailable, end the retrospective proposal. Do not reopen the prior FDA drug-decision pilot, infer no recall from a missing file or launch a new regulator-wide source campaign.
