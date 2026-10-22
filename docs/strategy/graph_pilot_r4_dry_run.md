# Graph Pilot R4 readiness: Phase A synthetic dry run

> DERIVED RESEARCH VIEW - NOT INDEPENDENT EVIDENCE - NO RESEARCH AUTHORITY

**NOT an R4 run.** Synthetic fixtures only, offline, in a temporary directory; no source fetched, no real campaign, session or adjudication. The adjudicator and operator are labelled fixture stand-ins. Regenerate with `python -m src.research.graph pilot r4-dry-run --write`; `--check` compares. Commit hashes and content digests are not printed, because they change with every implementation commit.

| Area | Check | Observed | Result |
|---|---|---|---|
| pin | a clean checkout pins commit and content | EXACT_COMMIT | PASS |
| pin | CRLF-only checkout differences verify (normalised), and are reported as dirty | EXACT_COMMIT; dirty ['src/research/graph/connections.py'] | PASS |
| pin | a dirty pinned set cannot be pinned | refused: uncommitted changes | PASS |
| pin | a changed implementation file refuses verification | refused: 'changed': ['src/research/graph/connections.py'] | PASS |
| pin | an added implementation file refuses verification | refused: 'added': ['src/research/graph/extra_module.py'] | PASS |
| pin | an unrelated commit with identical implementation passes as UNRELATED_COMMIT_CHANGE | UNRELATED_COMMIT_CHANGE | PASS |
| pin | missing git metadata cannot be pinned | refused: git metadata is unavailable | PASS |
| pin | missing git metadata at verification still enforces content | GIT_UNAVAILABLE_CONTENT_VERIFIED | PASS |
| pin | the boundary includes the R4 fetch tool and the offline guard (static import closure) | ['docs/strategy/graph_pilot/fetch_one.py', 'src/research/sec_pilot/parsing.py', 'src/research/spec.py'] | PASS |
| pin | the pin records Python and dependency versions | Python recorded; 5 distributions recorded | PASS |
| pin | a different Python or dependency version refuses verification | refused: the runtime differs | PASS |
| pin | the V2 snapshot binds commit, content digest and operator version | commit, tree digest and per-file digests (True); GRAPH_OPERATORS_V1_1 | PASS |
| pin | the running implementation matches the pin (content check on every query) | CONTENT_VERIFIED | PASS |
| legacy | a legacy (non-V2) snapshot carries no pin and is not checked | NOT_PINNED_LEGACY | PASS |
| pin | a snapshot pinned to another implementation refuses every arm query | refused: 'changed': ['src/research/graph/operators.py'] | PASS |
| pin | a V2 snapshot without a pin is refused | refused: must pin the Graph implementation | PASS |
| provenance | a modified saved running commit (all else intact) is refused before sealing | refused: not in this repository | PASS |
| provenance | replay after HEAD moves to an unrelated commit with identical pinned code is accepted | COMMIT_CONSISTENT_WITH_PIN | PASS |
| effort | contemporaneous G logging: no material discrepancy; the difference is still reported; evidence CONSISTENT | session 16.0 vs self 16 (0.0 min, 0.0%); CONSISTENT | PASS |
| effort | material threshold is the greater of 5 minutes or 10% of the comparator; smaller differences are reported | 54 vs 50: 4 min / 8.0%, threshold 5; 133 vs 120 material | PASS |
| effort | graph query and suggestion-review time are reported where measurable | 2 recorded queries; 9 self-reported graph minutes; review windows <= 7.0 min | PASS |
| effort | an inflated S effort is flagged against the session and its append interval; evidence CONTRADICTORY | session 14.0 vs self 46; CONTRADICTORY | PASS |
| effort | long gaps are descriptive only and never subtracted | DESCRIPTIVE_ONLY: listed, never subtracted from effort | PASS |
| effort | missing session attestations are reported, never inferred | session NOT_RECORDED, minutes UNKNOWN | PASS |
| effort | a START without its STOP is INCOMPLETE_NO_STOP | INCOMPLETE_NO_STOP | PASS |
| effort | an attestation is immutable (a second START is refused) | refused: already exists and is immutable | PASS |
| effort | assistant self-attestation is refused by name | refused: assistant self-attestation is refused | PASS |
| effort | an attestation by a non-human kind is refused | refused: attested by the human arm operator personally | PASS |
| effort | a STOP needs its START | refused: needs its START | PASS |
| effort | graph minutes without any recorded graph query are flagged | ['EFFORT_DIFFERENCE_BELOW_THRESHOLD', 'GRAPH_TIME_WITHOUT_RECORDED_QUERIES'] | PASS |
| accounting | exported = logged + exported-but-unlogged suggestions, per class | economic 2=2+0; warning 4=1+3; unsupported 0 | PASS |
| accounting | two rows sharing one origin: rows and suggestions are counted separately | 3 rows, 2 suggestions; rows {'ACCEPTED': 1, 'DECLINED': 1, 'UNRESOLVED': 1}; suggestions {'ANY_ACCEPTED': 1, 'ALL_DECLINED': 0, 'UNRESOLVED_OR_MIXED': 1} | PASS |
| accounting | every rate pairs a numerator and denominator of the same level | declined rows 1/3; all-declined suggestions 0/2 | PASS |
| accounting | a zero denominator is explicit, not zero | {'numerator': 0, 'denominator': 0, 'value': 'UNDEFINED_ZERO_DENOMINATOR'} | PASS |
| accounting | outcomes are NOT_ADJUDICATED before adjudication | NOT_ADJUDICATED | PASS |
| accounting | a missing V2 export makes exported counts UNKNOWN, never zero | V2_EXPORT_MISSING; exported UNKNOWN | PASS |
| blinding | the aliased export passes the leak scan | 5 items, 0 findings | PASS |
| accounting | after adjudication, every row keeps its own outcome (never overwritten by origin) | 3 rows, 2 suggestions; {'CONFIRMED_AGAINST_ORIGINALS': 1, 'PLAUSIBLE_UNVERIFIED': 2, 'REJECTED_FALSE': 0, 'REJECTED_TRIVIAL': 0} | PASS |
| accounting | two rows of one suggestion with different outcomes are both counted and the conflict is reported | conflicting suggestions 1; {'CONFIRMED_AGAINST_ORIGINALS': 1, 'PLAUSIBLE_UNVERIFIED': 1, 'REJECTED_FALSE': 1, 'REJECTED_TRIVIAL': 0} | PASS |
| accounting | a warning confirmed as useful is never counted as an economic discovery | discoveries 1 -> 1; warnings confirmed 0 -> 1 | PASS |
| effort | an attestation edited after blinding refuses unblinding | refused: changed after blinding | PASS |
| report | the report states the primary measure, both sensitivities and the effort evidence; one pair stays INCONCLUSIVE | INCONCLUSIVE; evidence ['CONSISTENT', 'CONTRADICTORY']; sensitivities {'session': 'NOT_VALID: a derived denominator is missing for some arm', 'observed_span': 'NOT_VALID: a derived denominator is missing for some arm'} | PASS |
| uniform pin | structured-search arm view (S, API) refuses a changed implementation | refused: differs from the snapshot pin | PASS |
| uniform pin | structured search (S, CLI baseline-search) refuses a changed implementation | refused: differs from the snapshot pin | PASS |
| uniform pin | graph query (G, API arm_graph) refuses a changed implementation | refused: differs from the snapshot pin | PASS |
| uniform pin | graph query (G, CLI revisit) refuses a changed implementation | refused: differs from the snapshot pin | PASS |
| uniform pin | export replay refuses a changed implementation | refused: differs from the snapshot pin | PASS |
| uniform pin | unblinding refuses a changed implementation | refused: differs from the snapshot pin | PASS |
| uniform pin | effort refuses a changed implementation | refused: differs from the snapshot pin | PASS |
| uniform pin | suggestion accounting refuses a changed implementation | refused: differs from the snapshot pin | PASS |
| uniform pin | verify refuses a changed implementation | refused: differs from the snapshot pin | PASS |

## Effort (synthetic packet P1; primary measure = self-reported minutes)

| Arm | Observed span (min) | Attested session (min) | Self-reported (min) | Difference vs session | Evidence | Flags |
|---|---:|---:|---:|---|---|---|
| S | 14.0 | 14.0 | 46 | 32.0 min (228.6%) | CONTRADICTORY | EFFORT_DISCREPANCY, EFFORT_EXCEEDS_APPEND_INTERVAL, SELF_REPORTED_EXCEEDS_SESSION |
| G | 16.0 | 16.0 | 16 | 0.0 min (0.0%) | CONSISTENT | EFFORT_DIFFERENCE_BELOW_THRESHOLD |

## Suggestion accounting (arm G, after the stand-in adjudication)

| Class | Exported | Logged suggestions | Exported, unlogged | Logged rows | Rows accepted / declined / unresolved | Adjudicated rows |
|---|---:|---:|---:|---:|---|---|
| ECONOMIC_CONNECTION_CANDIDATE | 2 | 2 | 0 | 3 | 1 / 1 / 1 | CONFIRMED_AGAINST_ORIGINALS: 1, PLAUSIBLE_UNVERIFIED: 2 |
| METHODOLOGICAL_WARNING | 4 | 1 | 3 | 1 | 0 / 0 / 1 | REJECTED_TRIVIAL: 1 |
| UNSUPPORTED_MATCH | 0 | 0 | 0 | 0 | 0 / 0 / 0 | none |

- Confirmed economic discoveries: 1 row(s), 1 suggestion(s) (rule: ECONOMIC_CONNECTION_CANDIDATE + CONNECTION + ACCEPTED + CONFIRMED_AGAINST_ORIGINALS + MEANINGFUL).
- Methodological warnings confirmed: 0; never counted as discoveries.
- 51/51 checks passed.
