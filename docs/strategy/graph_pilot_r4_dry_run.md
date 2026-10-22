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
| pin | the V2 snapshot binds commit, content digest and operator version | commit, tree digest and per-file digests (True); GRAPH_OPERATORS_V1_1 | PASS |
| pin | the running implementation matches the pin (content check on every query) | CONTENT_VERIFIED | PASS |
| legacy | a legacy (non-V2) snapshot carries no pin and is not checked | NOT_PINNED_LEGACY | PASS |
| pin | a snapshot pinned to another implementation refuses every arm query | refused: 'changed': ['src/research/graph/operators.py'] | PASS |
| pin | a V2 snapshot without a pin is refused | refused: must pin the Graph implementation | PASS |
| effort | contemporaneous G logging: derived and self-reported minutes agree within the threshold | span 16.0 vs self 16; session 16.0; flags none | PASS |
| effort | graph query and suggestion-review time are reported where measurable | 2 recorded queries; 9 self-reported graph minutes; review windows <= 7.0 min | PASS |
| effort | an inflated S effort is flagged against span, session and its append interval | span 14.0 vs self 46; flags ['EFFORT_DISCREPANCY', 'EFFORT_EXCEEDS_APPEND_INTERVAL', 'SELF_REPORTED_EXCEEDS_SESSION'] | PASS |
| effort | missing session bounds are reported, never inferred | session NOT_RECORDED, minutes UNKNOWN | PASS |
| effort | session bounds recorded by an assistant are refused | refused: recorded by the human operator | PASS |
| effort | graph minutes without any recorded graph query are flagged | ['GRAPH_TIME_WITHOUT_RECORDED_QUERIES'] | PASS |
| accounting | exported = logged + exported-but-unlogged, per class | economic 2=2+0; warning 4=1+3; unsupported 0 | PASS |
| accounting | declined suggestions are counted | {'ACCEPTED': 1, 'DECLINED': 1, 'UNRESOLVED': 0} | PASS |
| accounting | a zero denominator is explicit, not zero | {'numerator': 0, 'denominator': 0, 'value': 'UNDEFINED_ZERO_DENOMINATOR'} | PASS |
| accounting | outcomes are NOT_ADJUDICATED before adjudication | NOT_ADJUDICATED | PASS |
| accounting | a missing V2 export makes exported counts UNKNOWN, never zero | V2_EXPORT_MISSING; exported UNKNOWN | PASS |
| blinding | the aliased export passes the leak scan | 4 items, 0 findings | PASS |
| accounting | after adjudication, outcomes are counted per class with denominators | {'ECONOMIC_CONNECTION_CANDIDATE': {'CONFIRMED_AGAINST_ORIGINALS': 1, 'PLAUSIBLE_UNVERIFIED': 1, 'REJECTED_FALSE': 0, 'REJECTED_TRIVIAL': 0}, 'METHODOLOGICAL_WARNING': {'CONFIRMED_AGAINST_ORIGINALS': 0, 'PLAUSIBLE_UNVERIFIED': 0, 'REJECTED_FALSE': 0, 'REJECTED_TRIVIAL': 1}} | PASS |
| accounting | a warning confirmed as useful is never counted as an economic discovery | discoveries 1 -> 1; warnings confirmed 0 -> 1 | PASS |
| report | the paired report carries effort checks and suggestion accounting; one pair stays INCONCLUSIVE | INCONCLUSIVE | PASS |

## Effort (synthetic packet P1)

| Arm | Observed span (min) | Session (min) | Self-reported (min) | Flags |
|---|---:|---:|---:|---|
| S | 14.0 | 14.0 | 46 | EFFORT_DISCREPANCY, EFFORT_EXCEEDS_APPEND_INTERVAL, SELF_REPORTED_EXCEEDS_SESSION |
| G | 16.0 | 16.0 | 16 | none |

## Suggestion accounting (arm G, after the stand-in adjudication)

| Class | Exported | Logged | Accepted / declined / unresolved | Exported, unlogged | Adjudicated outcomes |
|---|---:|---:|---|---:|---|
| ECONOMIC_CONNECTION_CANDIDATE | 2 | 2 | 1 / 1 / 0 | 0 | CONFIRMED_AGAINST_ORIGINALS: 1, PLAUSIBLE_UNVERIFIED: 1 |
| METHODOLOGICAL_WARNING | 4 | 1 | 0 / 0 / 1 | 3 | REJECTED_TRIVIAL: 1 |
| UNSUPPORTED_MATCH | 0 | 0 | 0 / 0 / 0 | 0 | none |

- Confirmed economic discoveries: 1 (rule: ECONOMIC_CONNECTION_CANDIDATE + CONNECTION + ACCEPTED + CONFIRMED_AGAINST_ORIGINALS + MEANINGFUL).
- Methodological warnings confirmed: 0; never counted as discoveries.
- 28/28 checks passed.
