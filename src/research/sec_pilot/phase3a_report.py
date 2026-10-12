"""Small human-facing Phase 3A outputs from canonical evidence; no network."""
import json
from src.research.sec_pilot.parsing import digest


def table(headers, rows):
    return '\n'.join(['| '+' | '.join(headers)+' |', '| '+' | '.join('---' for _ in headers)+' |']+
                     ['| '+' | '.join(str(x).replace('|', '\\|') if x is not None else 'UNRESOLVED' for x in row)+' |' for row in rows])


def render(e):
    gate_order = ('Acceptance timestamp interpretation', 'Exact public availability', 'Conservative eligibility policy',
                  'Historical class identity', 'Financial semantic interpretation', 'Text segmentation',
                  'Nexus historical execution', 'Phase 3B design readiness')
    policy = e['policy']
    financial = ['# Phase 3A: scoped financial-semantic QA', '',
                 '**'+e['gates']['Financial semantic interpretation']+'** — three archived 10-Ks, five annual concepts per filing. '
                 'This certificate covers the stated tagged values, contexts, units and primary-element reconciliation; it does not certify a forecast or trading eligibility.', '',
                 table(['Accession', 'Concept family', 'Exact value', 'Units', 'Fiscal start / end', 'Original duplicate elements', 'Status'],
                       [(f['accession'], f['family'], f.get('exact_value'), f['unit'],
                         f.get('period', {}).get('startDate', '?')+' / '+f.get('period', {}).get('endDate', '?'),
                         f['selected_duplicate_elements'], f['status']) for f in e['financial_results']]), '',
                 'Selection v001 requires the exact declared US-GAAP concept/namespace, matching issuer, no dimensions, current report-period end and a 350–380-day fiscal duration. '
                 'The five concepts are revenue excluding assessed tax, NetIncomeLoss, diluted EPS, weighted-average diluted shares and operating cash flow. '
                 'No quarter/YTD derivation, aggregation across dimensions, interpolation, restatement or split correction is applied.', '',
                 'Currency/share QName namespaces are checked, including the default namespace for bare `shares`. '
                 'Normalized instance values reconcile to the primary Inline XBRL elements with the same namespace, context and unit, '
                 'using explicit format, sign and powers-of-ten scale. Decimals are precision metadata, not a scale multiplier. '
                 'Original equivalent duplicate elements are retained; conflicting duplicates fail. Unsupported transformations or nested enclosing numeric renderings cannot certify a value.', '',
                 'The [canonical evidence](phase3a_evidence.json) records source hashes, exact concept/namespace/context/entity/dimensions/period, '
                 'unit, decimals, selected instance locators, original HTML line/column/element IDs and explicit rendering scales. '
                 'All alternatives remain in immutable Phase 2 snapshots and private versioned interpretation receipts. '
                 'Non-dimensional annual issuer facts are reconciled to the filing; no broader accounting taxonomy or product-segment-to-consolidated assumption is certified.', '',
                 '## Comparative presentation is accession-specific', '',
                 table(['Accession containing the observation', 'Period end', 'Reported diluted EPS (USD/share)'],
                       [(r['accession'], r['period_end'], r['value']) for r in e['apple_2019_eps_presentations']]), '',
                 'Apple’s later presentation must not replace the original 2019 filing’s observation. This report does not compute an earnings change across incompatible per-share bases. '
                 'No shares-outstanding value is substituted for weighted-average diluted shares. Facebook’s listed class is not inferred from consolidated EPS. '
                 'Exact public availability remains UNKNOWN; class bindings remain provisional; approved decision-eligibility policy remains absent.', '']
    identity = ['# Phase 3A: historical identity feasibility', '',
                '**PARTIAL.** Archived cover disclosures identify historically used symbols and classes; they do not supply a complete dated listing/identifier bridge.', '',
                table(['Source accession', 'Issuer CIK', 'Class', 'Historical ticker', 'Exchange', 'Vendor-observed identifier', 'Binding status'],
                      [(b.get('accession', 'Facebook financial class dimension'), b['issuer_cik'], b['class'], b.get('historical_symbol'),
                        b.get('exchange'), b.get('source_observed_security_id'), b['status']) for b in e['historical_identity_matrix']]), '',
                'Issuer CIK, submitting CIK, accession, class, security ID, ticker and listing interval remain separate fields. '
                'Submitting CIK is not inferred from the accession prefix. Effective-from/to dates are explicitly unresolved; a filing-date cover disclosure is a point observation, not an interval certificate. '
                'Each source-observed class row has original XBRL context/locator/hash and its evidence filing date in the canonical evidence. '
                'The Class B financial dimension supplies evidence of multiple classes, not a listed ticker or an exchange bridge.', '',
                table(['Historical ticker', 'Existing source ID', 'First / last observation', 'Dated source observations'],
                      [(r['ticker'], r['source_security_id'], r['first_observed']+' / '+r['last_observed'], r['dated_observations'])
                       for r in e['existing_identity_source_audit'].get('rows', [])]), '',
                'These counts come from eight existing hash-verified 2019/2020 EXP004 source parts. Only ticker, ID, dates and counts were inspected; '
                'no prices, returns or remote calls were used. The vendor’s `figi:` label and repeated observations do not independently certify identifier level, class identity, listing span, rename/merger lineage or terminal value. '
                'No current profile/ticker map, proxy ID or inferred listing dates are substituted. EXP004 inputs/population and its pause remain unchanged.', '',
                '## Smallest additional evidence', '',
                'Request a dated class-to-stable-ID bridge for AAPL common stock and Facebook Class A at the three filing/decision dates: '
                'issuer CIK, exact class, FIGI level, ticker, exchange, effective listing spans, source/vintage/hash and any intervening rename, merger or delisting events. '
                'Prefer the original vendor segment provenance or a documented identifier-provider historical extract plus issuer/exchange listing evidence. '
                'A current OpenFIGI/company response alone is not a historical interval certificate. No purchase, additional extract or full-universe import is authorized or performed. '
                'Any mapping to another class, overlapping segment, missing source or unresolved corporate action remains unavailable.', '']
    availability = ['# SEC decision eligibility v001 — PROPOSED, NOT APPROVED', '',
                    '**No real policy is approved or activated.** Policy hash: `'+e['policy_sha256']+'`.', '',
                    policy['rule']+'. Calendar: '+policy['calendar']+'. Scope: 2015–2020. Frozen calendar source hash: `'+policy['calendar_source_sha256']+'`.', '',
                    'Start from the later of the original acceptance wall-clock date and independently recorded official SEC filing date. '
                    'Skip weekends and full-day exchange holidays, wait through one complete later session, then use the following session’s 09:30 New York open. '
                    'The open uses seasonal EST/EDT via IANA America/New_York; early closes affect neither the selected open nor the whole-session count. '
                    'Unsupported dates, incomplete calendars, invalid/ambiguous wall times and contradictory chronology yield BLOCKED, not a guessed date.', '',
                    table(['Accession', 'Official SEC filing date', 'Illustrative proposed eligibility (UTC)', 'Activation'],
                          [(r['accession'], r['filing_date'], r['proposed_eligibility_at_utc'], 'NOT APPROVED') for r in e['acceptance_interpretations']]), '',
                    'Rationale: the SEC’s access guidance describes next-business-day dissemination for some late submissions; the website FAQ explicitly gives no guaranteed posting lag. '
                    'A full subsequent-session buffer is a conservative modeling choice, not evidence of an exact first-public timestamp or a guaranteed upper bound. '
                    'The two October dates remain illustrative while UTC acceptance interpretation is unresolved. Documentation reviewed in 2026 is not a contemporaneous dissemination receipt.', '',
                    '[SEC access guidance](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data), '
                    '[SEC website timing FAQ](https://www.sec.gov/about/webmaster-frequently-asked-questions). Source retrieval dates and byte hashes are in the canonical evidence.', '',
                    '## Conditions for any later activation', '',
                    '\n'.join('- '+c+'.' for c in policy['activation_conditions']), '',
                    'The implementation has no approval writer or automatic promotion command. A trusted owner receipt must separately bind the exact policy, interpretation snapshot and authority-artifact hash. '
                    'Synthetic receipts test this contract; they approve no real policy. Every contributor must satisfy certified acceptance, source lineage, declared bound and no contrary public evidence. '
                    'New sources/restatements receive new snapshots and new approval scope. A later metadata change cannot alter an earlier pinned view.', '',
                    'Observed `public_available_at_utc` remains nullable and unchanged. An approved modeled bound would be a separate field/basis; local 2026 download/ingestion and historical reconstruction are separate clocks. '
                    'This proposed policy does not certify identity or Nexus execution.', '']
    report = ['# Phase 3A: SEC source certification and identity feasibility', '',
              '**Fifteen scoped annual observations are certified; trading and execution remain blocked.** As of '+e['as_of']+'. '
              'No new filings, strategy research, performance queries, Nexus operations or EXP005 were started.', '',
              table(['Gate', 'Verdict'], [(g, e['gates'][g]) for g in gate_order]), '',
              '## Acceptance and public availability', '',
              table(['Accession', 'Original acceptance', 'Certified UTC', 'Seasonal ET candidate', 'Literal EST candidate', 'Interpretation'],
                    [(r['accession'], r['raw'], r['accepted_at_utc'], r['candidate_eastern_utc'], r['candidate_literal_est_utc'], r['status']) for r in e['acceptance_interpretations']]), '',
              'The [SEC PDS specification](https://www.sec.gov/files/info/edgar/pdsdissemspec072213.pdf), section 2.1, labels acceptance time “EST”. '
              'The [SEC FAQ](https://www.sec.gov/about/webmaster-frequently-asked-questions) ties the SGML timestamp to that definition. '
              'The archived [Regulation S-T business-hour rules](https://www.govinfo.gov/content/pkg/CFR-2011-title17-vol2/pdf/CFR-2011-title17-vol2-sec232-11.pdf) use standard or daylight time when applicable, '
              'but do not explicitly redefine the SGML field. Winter conversion converges under both interpretations; the two October conversions differ by an hour. '
              'Those candidates are separated from certified acceptance; no undocumented DST assumption is activated. A dated authoritative clarification of the SGML field’s daylight-saving behavior is the remaining timestamp blocker.', '',
              'The SEC FAQ states there is no first-public website timestamp and no guaranteed posting lag. The [SEC access guide](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data) notes next-business-day dissemination for some late filings; '
              'the PDS describes a subscriber feed, which is a different channel from website availability. Neither generic timing statement certifies an accession’s exact first-public instant. '
              'All observed public timestamps remain UNKNOWN. Four narrowly bounded documentation responses were archived privately, with URL/retrieval-time/byte hashes retained in evidence. No new filing acquisition occurred.', '',
              '## Scoped source findings', '',
              'See the [financial-semantic QA](phase3a_financial_qa.md), [historical identity matrix](phase3a_identity.md) and '
              '[proposed availability policy](availability_policy_v001.md). Each of five concepts per filing is selected by a separately versioned rule and reconciled to original primary Inline XBRL scale/context/unit. '
              'Original facts and alternatives remain immutable. AAPL/FB cover-page evidence and existing source identifiers improve feasibility but do not certify listing-effective spans or a class bridge.', '',
              table(['Accession', 'Candidate Item 1 / 1A / 7 / 8 lengths (characters)', 'Text verdict'],
                    [(r['accession'], ' / '.join(str(x.get('characters', 0)) for x in r['items']), r['status']) for r in e['text_assessment']]), '',
              'Pinned EdgarTools 5.62.0 supports `ParserConfig(form="10-K")`; the generic Phase 2 call did not provide a form. '
              'The configured offline probe extracts all twelve requested candidate items reproducibly. Item text hashes/character counts are retained; '
              'source start/end anchors, TOC exclusion and cross-reference boundaries are not independently certified. Segmentation is DEFERRED rather than inferred from plausible lengths. '
              'No new segmenter, embeddings, search service or sentiment model is built.', '',
              '## Nexus dependency', '',
              'Retain EXECUTION_BLOCKED. The [existing execution contract](historical_execution.md) still requires:', '',
              '- Source-side dated stable-ID/class/ticker/listing lineage, separate from SEC issuer identity.',
              '- Complete publication with preserved identity, availability, values and every requested point; storage acceptance alone is insufficient.',
              '- Exhaustive pre-filter runtime identity lists matching the certified population exactly, including renamed and ended histories; no equal-count substitution or current-survivor pruning.',
              '- Audited corporate-action, cash/stock conversion, merger/delisting terminal-value and position-transition handling under declared costs/timing.', '',
              'Source-side progress does not resolve the demonstrated Nexus pruning failure. No vendor call, support message, upload, diagnostic or EXP004 operation occurred.', '',
              '## Reproduction and preserved history', '',
              '```sh', 'python -m src.research.sec_pilot.phase3a --check',
              'python -m src.research.sec_pilot.phase3a --report-only --check',
              'python -m unittest discover -s tests -v', 'python -m src.research.sec_pilot replay',
              'python -m src.research.sec_pilot audit', 'python -m src.research.sec_pilot report --check',
              'python -m src.research audit EXP004', 'python -m src.presentation.exp001 --check', '```', '',
              'The full new check uses existing ignored Phase 2 snapshots, the four archived documentation responses and existing source parts; it has no acquisition path. '
              'Report-only regeneration needs the public canonical evidence. Versioned interpretation receipts use new content-hash filenames under ignored storage; earlier prototypes are retained. '
              'Phase 2 raw bodies, derived snapshots, hashes, original report/summary/validation and all frozen experiments remain unchanged. '
              'Legacy regression tests use already-opened EXP001 local records and do not authorize new held-out research access. Dependency pins and the isolated environment remain unchanged.', '',
              'The baseline was 191 passing tests. Final executed checks and counts are recorded in [validation](phase3a_validation.json). '
              'The code checkpoint `62a8abb` added interpretation/eligibility/semantic gates; subsequent verified commits and push status are reported in the delivery message.', '',
              '## Recommendation and stop', '',
              'READY_FOR_CONDITIONAL_DESIGN means enough scoped annual accounting evidence exists to discuss a future mechanism and data requirements. '
              'It is not permission to construct a trading-ready signal, run performance tests or freeze EXP005. Before executable research, obtain the October timestamp clarification, '
              'owner review of the proposed availability assumption, an independently dated class/ID bridge and certified population-preserving execution. '
              'Do not compute fundamental acceleration across incompatible comparative EPS/share bases or infer analyst earnings surprise without a separate expectations source.', '',
              '**Stopped after Phase 3A.** No Phase 3B, broader SEC backfill, real policy approval, portfolio optimization, purchases, Test opening, paper/live operation or new experiment is included.', '']
    return {'phase3a_report.md': '\n'.join(report), 'phase3a_financial_qa.md': '\n'.join(financial),
            'phase3a_identity.md': '\n'.join(identity), 'availability_policy_v001.md': '\n'.join(availability),
            'availability_policy_v001.json': json.dumps(policy, indent=2, sort_keys=True)+'\n'}
