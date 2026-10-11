EXP002 — Final Two-Gate Resolution
EXP002 remains DRAFT.
This task addresses only the two remaining critical source gates identified by the final pre-freeze review:
1. historical large-cap universe membership / security identity
2. institutional CUSIP identity / certified omission-as-zero
Do not reopen already-passed gates.
Do not evaluate candidate performance.
Do not optimize.
Do not query outer Validation or Test observations.
Do not freeze automatically.
Candidate-formation cutoff remains 2020-12-31.
The owner authorizes Nexus Lake, MCP, SDK and minimal deterministic backtests required to resolve these two gates.
GATE A — Historical S&P 500 membership
The previous local constituent reconstruction is rejected because it is underfilled, contains symbol-rename/reuse problems and leaves 19 security IDs unresolved.
Do not continue repairing that list by applying present-day symbols backwards.
Instead investigate Nexus's native historical index-membership infrastructure.
Observed/public Nexus capabilities include:
- Is Index Member(asset, "SP500")
- lake.index_constituents
- historical simulations
A1. Inspect the actual declarations
Determine:
- exact SDK/MCP declaration for Is Index Member
- index_constituents schema
- identifier fields
- effective/start/end dates
- symbol fields
- stable security IDs if available
- index identifier/name conventions
Do not infer fields.
A2. Point-in-time historical membership test
Create a bounded diagnostic set of known membership transitions entirely before 2021.
Include examples of:
- addition
- removal
- ticker rename
- security later delisted
- company that is a current member but was not yet a member historically
- company that was a historical member but is not a current member
Compare, for the same historical dates:
1. Lake index_constituents
2. native Is Index Member
3. independent historical membership evidence where useful
Do not inspect returns.
The goal is to establish whether membership is evaluated as of the historical simulation date, rather than from today's index.
A3. Monthly population audit
For every monthly decision date in the proposed Development window:
- obtain native historical S&P 500 membership
- count members
- count unique stable identities
- count unresolved identities
- count ticker changes
- count later-delisted/removed securities
Explain any material underfill/overfill.
Do not require a literal count of exactly 500 if the source legitimately represents multiple share classes or effective-date mechanics.
What matters is that unexplained missing names are not silently discarded.
A4. Preferred primary universe
If native historical membership passes:
make the primary universe:
historical SP500 membership as evaluated by the certified native/index-constituent source
intersected with:
- stock/common-equity classification where safely available
- nominal historical price >= $5
Do not maintain a redundant hand-built membership list as the authoritative universe.
Preserve the local reconstruction only as an audit comparison.
If native historical membership fails the point-in-time test, mark Gate A FAIL and stop trying increasingly complicated substitutions.
GATE B — Institutional identity and omission-as-zero
The existing matched-manager institutional construction is retained.
Do not fall back to native NetHolderChange.
We need a defensible date-aware identity contract.
B1. Inspect the published ownership resolver
The open-source austin-starks/sec-ownership-disclosures pipeline is documented as the ownership engine behind NexusTrade.
Pin the exact dataset/code revision used in this audit.
Inspect its actual implementation and methodology for:
- resolvedTicker
- CUSIP mappings
- N-PORT mappings
- OpenFIGI mappings
- date spans
- availableAt
- ambiguous mappings
- null mappings
The published methodology specifically warns against undated CUSIP mappings and resolves holdings against date-valid spans.
Do not reimplement a simpler ticker crosswalk if the audited resolver already solves the problem more safely.
B2. Build a dated security-identity contract
For every institutional security used in EXP002 require:
- original CUSIP
- filing accession
- manager CIK
- reporting quarter
- availableAt
- date-valid resolved ticker/security identity
- mapping source
- mapping validity span
- mapping confidence/status
A mapping with no valid span at the filing's availability date is unavailable.
Never use today's ticker backwards.
Never strip foreign venue/currency suffixes merely to force a match.
Never convert unresolved identity to zero.
B3. Omission-as-zero contract
For a candidate security S, manager M and quarter Q, not held may be recorded only when all are true:
- M has a certified complete eligible filing for Q
- the filing state has been reconstructed as-of the decision timestamp
- amendments/additions known by that timestamp have been applied correctly
- security S has a unique valid contemporaneous identity/CUSIP contract
- all filing rows necessary for that state are available
- S's valid identity is absent from the reconstructed complete holdings
Otherwise the state is unavailable, not zero.
B4. Demonstrate real usable cohorts
Using only pre-2021 data, run a coverage/mechanics audit over a reproducible date-stratified sample of historical index members.
Do not select securities based on performance.
Across several quarter pairs and years report:
- eligible securities
- managers public after the fixed 60-day maturity gate
- complete manager filings
- matched managers across adjacent quarters
- identity resolution %
- unresolved CUSIPs
- securities for which omission-as-zero is certifiable
- cohort coverage %
Demonstrate that the institutional signal can actually be produced for a meaningful portion of the proposed universe.
B5. Final quality floor
Based on coverage mechanics only, finalize:
- minimum matched-manager count
- minimum known-cohort coverage
- maximum staleness
Use simple conservative round thresholds.
Do not select thresholds based on future returns.
Record the complete distributions used to choose them.
Resolve Development inception only after both gates
If Gate A and Gate B both pass, calculate the earliest date at which the complete frozen inputs are available for:
- 365-calendar-day momentum
- 90-day insider window
- two adjacent mature institutional cohorts
- 60-day institutional quarter gate
- valid historical index membership
Choose Development inception strictly from data availability.
Development ends 2020-12-31.
Then finalize the chronological fold boundaries.
Do not force a 2015 start.
Stop rule
This is important.
Do not launch another broad EXP002 design revision after this task.
At completion:
If both Gate A and Gate B pass
update the final freeze-review package and return:
READY FOR FREEZE REVIEW
If Gate A passes but Gate B fails
return:
BLOCKED — INSTITUTIONAL SIGNAL
and prepare, but do not execute, a proposal to fork a new experiment using momentum + insider only.
Do not quietly remove the institutional signal from EXP002.
If Gate B passes but Gate A fails
return:
BLOCKED — UNIVERSE
and identify the simplest independently auditable universe available without performance search.
If both fail
return:
ABANDON EXP002
Preserve EXP002 as a documented negative research-design result.
Artifacts
Update:
- final_freeze_review.md
- spec.json
- provenance.json
- README.md
- universe_audit.md
- pit_audit.md
- custom_signal_spec.md
- evaluation_plan.json
Create:
- index_membership_certification.md
- institutional_identity_certification.md
Raw receipts remain ignored.
Run the full repository test suite.
Commit and push if tests pass.
Finish with:
- Gate A result
- Gate B result
- historical-universe contract
- institutional identity contract
- omission-as-zero contract
- final Development start/folds if available
- unresolved noncritical limitations
- Nexus calls/jobs used
- tests
- commit SHA
Do not freeze automatically.

My expectation is that this has a real chance of passing rather than simply producing another 15-page list of unknowns.
The institutional resolver is particularly promising. The public Nexus ownership pipeline explicitly says 13F gives you CUSIP, not ticker/CIK, and resolves it using N-PORT plus OpenFIGI with dated spans. It also intentionally returns null when a CUSIP has no valid mapping rather than manufacturing one. GitHub That is almost exactly the identity contract Codex has been trying to invent itself.
For the universe, I’d similarly rather verify Nexus's native historical SP500 membership than maintain our own fragile symbol list. Nexus documents Is Index Member as a supported indicator, so now we need to test its historical semantics rather than merely trust the name. NexusTrade
And I’d enforce that stop rule. The current review itself says the remaining work is specifically constituent/identifier history plus the institutional identity/zero contract; it explicitly warns against today's symbols backwards or unknown holdings as zero.    Pasted markdown
So this is the last shot for the current three-signal EXP002 design.
If it passes, freeze.
If institutional identity still fails after using the actual date-aware CUSIP resolver, I would stop weakening EXP002 and create a clean EXP003/EXP002B momentum + insider experiment instead. That would be better science than spending another day trying to force 13F data into a contract it cannot support.