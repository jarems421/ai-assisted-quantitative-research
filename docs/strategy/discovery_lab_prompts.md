# Discovery Lab research prompts

Structured prompts for Claude at each stage of an evidence-first discovery campaign. Print one with `python -m src.research.discovery prompt <stage>`; add `--ledger <file> --record <ID>` to append the current record and checklist as context. **Context is not evidence:** every factual field must be checked against a cited original.

Common rules apply to every stage:

- **Allowed:** propose observations, relationships, mechanisms, alternative explanations and the cheapest decisive check.
- **Not allowed to certify:** publication times, units or arithmetic, legal obligations, historical identity, access rights, allocations, completeness, outcome joins or any M/H judgment. These come from cited originals and a human reviewer.
- Write records using `python -m src.research.discovery template <type>`. Keep unknown facts as `UNKNOWN`; never fill them from memory, today's version or a later account.
- Ask for the **minimum additional evidence that could change the decision**. Stop when no affordable observation within existing authority could change it.
- Never claim that nobody else knows, uses or has discovered something. Record what was checked; keep private use UNKNOWN.
- Never inspect security returns or prices during discovery.

## `observation-first`

**Purpose:** find one economically informative change recorded in an original public source.

1. Name the source and the exact field, passage or table. What changed, from what to what, in what units and denominator?
2. Record the four clocks separately: economic occurrence, first public availability, source version and our retrieval. Which can be evidenced, and from what?
3. Which identified economic object does it describe (facility, licence, contract, lease, product, legal entity)?
4. Why is the change informative rather than a static level? What ordinary explanations exist?
5. Record it as an Observation Card even if it never becomes a claim. Do not search outcomes to decide whether it is "interesting".

Output: one `observation` record, plus a `source` passport if the source is new.

## `relationship-first`

**Purpose:** start from one independently documented economic relationship and look for measurable changes that could propagate through it.

1. Cite the original document establishing the relationship (ownership, operation, supply, lending, insurance, licence, predecessor obligation, dependence, substitution).
2. Give both entities stable identifiers. A name match is `NAME_MATCH_ONLY` and stays `UNVERIFIED`.
3. State the dated period over which it applies. Current ownership does not establish past ownership.
4. Can quantities be transferred or allocated between the entities? Unless an original document states the share, the allocation stays `UNVERIFIED`.
5. Which recorded quantities on either side could change, and where would that change be observed?

Output: one `relationship` record and candidate observation targets.

## `event-first`

**Purpose:** start from a concrete event capable of changing expectations (determination, licence change, cancellation, interruption, court decision).

1. Record the event as an `EVENT` observation with its publication record if one exists.
2. Which listed company is exposed, through which documented relationship?
3. Was the event forecastable from an earlier original observation, or only surprising in hindsight? Do not confuse the two.
4. Did the issuer or another obvious source explain the consequence at the same time? Check before asserting an increment.

Output: one `EVENT` observation; a candidate only if an earlier observation or a non-obvious transmission exists.

## `hypothesis-first`

**Purpose:** the preserved baseline. State a mechanism, then search for its required variables.

1. Write the mechanism in one paragraph, then name the single distinctive variable it needs, its units and its population.
2. Before any further reasoning, find one original record of that variable. If only a schema, index description or later account exists, record that depth honestly.
3. Do not extend the mechanism essay to compensate for an unobserved predictor.

Output: one `candidate` record (entry_record null) and effort records for every search, including failures.

## `extract-observation`

**Purpose:** turn one original document into an Observation Card.

- Copy the exact field or passage locator; record units and denominator as printed.
- Set depth to the strongest level the document itself supports: `VERIFIED_ORIGINAL_FIELD` only when the economic field is visible with provenance (sha256 or archive pointer).
- Set first-public time only from an original publication record; otherwise `UNKNOWN`. Document dates, HTTP headers, caches, filenames and search-index dates are not first-public certificates.
- List what the observation does **not** mean (for example: a ceiling is not actual throughput).

## `link-relationship`

**Purpose:** propose and evidence a relationship for an observation.

- Propose candidate links freely, but record only what an original document supports.
- Check identifier consistency against entities already in the ledger.
- Record limitations and alternative parties (co-owners, operators, guarantors, other obligors).

## `form-candidate`

**Purpose:** convert observation(s) and relationship(s) into an Economic Inference Card, then freeze it before examining the intended outcome.

Fill, in this order: distinctive predictor and units; linked company and verified exposure (gross and net separately); mechanism; independent outcome and its route; join requirements; information event and decision time; 5–20 session rationale; closest substitute (checked or explicitly not); exact increment; cheapest decisive falsification; missing variables; selection history; the three propositions (economic effect, informational advantage, residual investment value).

Then run `freeze`. Any later change to the predictor, population, mechanism, outcome object, company or claim basis creates a new version that is reported separately.

## `sceptic-measurement`

Is the predictor actually observable in the required units and population? Which field, at what depth? What proxy is being substituted (industry for company, capacity for spare capacity, gross for net, group for legal entity)? Record unchecked items in `not_checked`.

## `sceptic-economic`

Does the documented relationship produce the claimed financial consequence? An approved contract is not realised revenue; a reserve is not available cash; subsidiary activity is not retained parent profit; two related records do not establish causality.

## `sceptic-information`

Is the implication already explained by the issuer, regulator, established research or a specialist product? Cite what was actually checked. If the closest substitute was not checked, say so explicitly.

## `sceptic-timing`

Could a researcher have obtained the predictor and the relationship before the proposed decision time? Which of the four clocks is evidenced, and by what? A later description of an earlier filing is not that filing.

## `sceptic-selection`

Was the claim chosen because the answer was already known, because the event is famous, or after inspecting an outcome? Is it a purposive control? Record its selection history and whether it can ever count as untouched evidence.

## `sceptic-investment`

Even if the economics and timing hold, why might investors not already price this? What is the concrete expectation-revision event within 5–20 trading sessions? Economic importance is not a trading edge. Do not look at returns to answer.

## `next-evidence`

**Purpose:** choose the single cheapest observation that could change the disposition.

1. Run `checklist`. Take the first blocked requirement in the order predictor, units, outcome, join, exposure, public-time route.
2. Name one original document or field that would resolve or falsify it, its expected cost (time, starts, bytes) and whether it is within existing authority.
3. If it is outside authority, propose it as a `VERIFY` disposition (PROPOSAL_ONLY) and stop. If no affordable observation could change the decision, recommend HOLD or REJECT with a scoped reason.
