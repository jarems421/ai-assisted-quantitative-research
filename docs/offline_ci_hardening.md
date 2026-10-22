# Offline CI coverage and maintainability review

Review baseline: `1be7d8f2a3bb45d5c7d54f27b31d84cebcfbf3f9`, fetched `main`,
the merge of PR #14 after merged PRs #11–#13. Work is isolated on
`codex/offline-ci-hardening`; the separate N1 owner-setup branch is preserved.
This work changes engineering checks only. Fixture success establishes no
scientific validation, independent quality judgment or investment value.

## Coverage inventory

The machine-readable [inventory](../tests/offline_inventory.json) names every
`tests/**/test_*.py` module, its baseline CI membership, runner, review reason,
declared methods and exact exclusions. `python -m src.research.offline_checks
--inventory` reproduces it without importing tests. New/removed modules or changed
method inventories fail until reviewed. Counts of declared methods are not runtime
counts: the R3 process class inherits three scenarios, and unittest can collect
imported TestCase classes. Execution summaries are authoritative.

| Baseline at PR #14 | Modules | Declared methods | Baseline execution |
|---|---:|---:|---|
| `public_checks` | 32 | 403 | Windows, guarded; includes Discovery Lab and Graph |
| `opportunity_scout.v004_checks` | 14 | 264 | Windows, guarded; includes V001/V002 prompt fixtures |
| Scout R2/R3 process assurance | 2 | 3 | Windows; 6 runtime tests including inherited scenarios |
| N1 collector process assurance | 1 | 25 | Windows; 25 real local process tests |
| Additional modules omitted | 28 | 223 | Previously absent from public runner |
| Isolated SEC parser modules omitted | 2 | 5 | Developer-local interpreter required |

The additional runner executes **212** of those 223 methods unchanged. It adds
EXP001 performance/session/selection/reconciliation fixtures (15), core Research
OS fake transport/Store/analysis/reporting tests, EXP002–EXP004 contract and
provenance checks, capability pauses, PIT signals, fake SEC acquisition/error
receipts, inline parsing, exact reconciliation, Parquet/DuckDB, and support-case
redaction/tampering checks. The plain SDK `nexustrade==1.42.0` is needed for local
authoring and literal HTML projection; no SDK extras or client operation is needed.

Explicit exclusions, never optimistic skips:

| Exclusion | Tests | Actual dependency or side effect |
|---|---:|---|
| EXP001 `FinalTestIntegrationTests` | 9 | `setUpClass` reads ignored raw EXP001 and calls `process(workspace)`, rewriting canonical processed CSV/metrics/report. Includes a seemingly safe clock test whose class setup is unsafe. |
| EXP004 existing price-coverage test | 1 | Reads ignored EXP003 raw receipts; its local `exists`/skip behavior must not decide CI eligibility. |
| Research OS figure-rendering test | 1 | System font enumeration reads Windows fonts / invokes Linux fontconfig. Excluded from restricted IO pending a reviewed bundled-font fixture; no renderer or OS-font claim. |
| SEC isolated parser tests | 4 | `.research/sec-pilot-venv/Scripts/python.exe`, EdgarTools 5.62.0; self-skips if absent, child does not inherit new guard. |
| Phase3C isolated parser test | 1 | Same developer-specific Windows interpreter; fails rather than skips when absent. |

No included test needs credentials, account contents, hosted inference, live source
acquisition or actual experiment execution. Fake transport tests intentionally
exercise acquisition interfaces with literal bytes and temporary error receipts.
Some read already public, tracked experimental specs, provenance and processed
result hashes; this is read-only preservation checking, not private record access.
The isolated SEC dependency environment and OS font renderer remain outside the
confidently portable, restricted profile. No test is classified by its name alone.

## Reproduction and safety boundary

From a full Git checkout with CPython 3.13:

```sh
python -m pip install -r requirements-offline-ci.txt
python -m src.research.offline_checks --inventory
python -m unittest tests.test_offline_checks.GuardTests -v
# Choose the native guard class for the actual OS:
# Windows: python -m unittest tests.test_offline_checks.WindowsGuardTests -v
# Linux:   python -m unittest tests.test_offline_checks.LinuxGuardTests -v
python -m src.research.offline_checks
python -m src.research.public_checks
python -m src.research.opportunity_scout.v004_checks
python -m unittest tests.test_scout_v004_process_assurance tests.test_scout_v004_r3_process_assurance -v
# Windows native collector assurance:
python -m unittest tests.test_scout_n1_collector_process_assurance -v
```

Dependency installation and GitHub delivery are engineering operations, separate
from scientific-source access. The new Windows/Linux matrix installs exact direct
dependency versions already used by this project (including the otherwise omitted
plain SDK). Transitive dependencies retain pip's resolution; this is not a complete
dependency lock or a claim of bit-identical environments. Existing workflow/action
SHA pins and Python 3.13 requirements are retained; the original public workflow is
byte-unchanged.

The **additional** runner installs a Python audit hook before test imports. It
denies DNS, outbound TCP including loopback, UDP send, subprocesses/shells/forks,
private/untracked file opens, writes outside its temporary fixture tree, and SQLite
databases outside that tree. Mocking `Path.open`, `builtins.open` or Popen does not
remove the hook. Denials derive from BaseException to avoid application error
assertions swallowing them; a separate violation latch fails the run even if a
test catches BaseException. Real NexusTrade client construction is separately
refused; local authoring and fake transports remain available. Unexpected skips, test-count mismatches, loader errors
and empty selection fail. Every exclusion and a machine-readable `OFFLINE_RESULT`
are printed. Guard self-tests use fictional paths and actual denied operations in
a separate process, so expected denials do not pollute the suite's latch.

Tests receive an allowlisted environment, temporary HOME/USERPROFILE/cache/temp
directories and no credential environment. Read access is limited to tracked public
files (excluding `data/raw` and `.research`), the Python installation and fixture
scratch. Bytecode lookup is redirected to scratch. Real repository files are
read-only; fixture stores named `data/raw` or `experiments` are allowed only inside
scratch. Linux fd-relative cleanup resolves the actual directory descriptor;
unsupported platforms fail closed. Symlink creation is refused.
The first native Linux run demonstrated a blocked `/usr/share/zoneinfo` read:
the additional runner now selects the pinned `tzdata` wheel on both systems using
`zoneinfo.reset_tzpath(())`. Production calendar/metric code is unchanged.
The first hosted Windows run also exposed an extended-path prefix from
`Path.resolve()` during concurrent fixture directory creation. The guard now
normalises equivalent drive/UNC extended prefixes before boundary comparison;
a native Windows regression checks scratch writes and forbidden repository writes
through extended paths. The original concurrent archive test stays unchanged.
Guard counts are seven portable tests plus one native test per OS. The other OS's
native class is excluded by workflow selection and would explicitly skip if invoked
directly; it never counts as simulated native assurance.
Linux's `open` audit event omits `dir_fd`: the guard records that argument in a
thread-local wrapper while preserving the original native syscall. Its Linux
regression exercises nested temporary-tree cleanup and descriptor-relative reads,
alongside denied writes/reads outside scratch. No fd-based cleanup is replaced
with a simulated path deletion.

These are guards for reviewed Python tests, **not an OS security sandbox for
hostile tests or native extensions**. SQLite/PyArrow/DuckDB perform some native IO
that Python audit hooks cannot universally mediate; reviewed tests pass only
temporary literal/local paths to those interfaces. GitHub starts from a clean
checkout without private archives or account configuration. Future tests that use
native external IO need renewed review or OS-level isolation. Inherited file
descriptors are not content-isolated. Do not execute arbitrary plugins inside this
runner and describe them as sandboxed.

Existing public/Scout runners retain their original safeguards and limitations:
Python open patches, an external socket guard that permits internal loopback, and
Scout's Popen refusal. Graph legitimately uses read-only full Git history and
throwaway Git repositories for hash/reveal-order checks. The two Scout lock suites
run fixed local Python children on both systems outside the no-process guard.
N1 collector tests remain on Windows to preserve native process assurance; Linux
fixture success cannot certify Windows Job Objects, creation timestamps or cleanup.
Pure OS metadata/path fixtures in Scout do not count as native OS assurance.
The first Linux Scout run demonstrated that setup-python's `python` symlink is
refused by the existing N1 fixture binary-binding gate. The Linux workflow now
executes the resolved interpreter binary itself before entering the same guarded
Scout suite. It does not mock `sys.executable`, weaken symlink refusal or change
the fixture/production binding code. All original test methods remain unchanged.

## Maintainability assessment

No production refactor is justified in this patch. Expanding executable coverage
reduces regression risk immediately without changing frozen source inventories or
mixing a hash-bound implementation change into CI work. Baseline measurements:

| Module | Lines | Concrete risk | Small next step, separately reviewed |
|---|---:|---|---|
| `graph/pilot.py` | 1,348 | `derived_effort` (80 lines) combines timestamp collection, session comparison, flags and reporting; `suggestion_accounting` (72) combines export/row/outcome joins. Legacy/prospective distinctions make generic aggregation unsafe. | Add golden output comparisons for legacy, prospective, missing-cost and missing-effort cases before extracting a pure collector. Keep UNKNOWN propagation and existing entrypoints. |
| `graph/operators.py` | 614 | Shared/complements/revisit repeat basis collection and suggestion assembly, but differ in permitted evidence, period/identity filters and categorical classification. Existing `order_bases`, `suggestion_id`, `suggestion` already share the safe mechanics. | Keep operator-specific joins explicit. Extract only an identical pure fragment after byte-equal suggestion/export fixtures; never consolidate on superficial resemblance. |
| `graph/ai_review.py` | 567 | Primary/cross validators duplicate envelope/provenance/declaration checks, while label authority and evidence support rules differ. `reconcile` (61 lines) combines admissibility and diagnostic counts. | First pin malformed-envelope error precedence and exact messages; then consider one private envelope reader. Do not share scientific label rules or alter stage order. |
| `opportunity_scout/engine.py` | 349 | `apply` (131 lines) is the append/replay state machine. Validation/mutation ordering and late imports protect versioned records; extracting handlers can change partial mutation on failure. | Parameterised append-versus-replay negative fixtures and state-before/state-after assertions before any per-event extraction. Preserve the public function and frozen schema/runtime inventories. |
| `tests/test_graph.py` | 1,670 | Many independent protocols share fixtures, class aliases and inherited helpers. Moving classes can duplicate/disappear tests under unittest discovery or alter module ROOT/path expectations. | Inventory runtime IDs first; move only a cohesive class group after asserting identical IDs/counts and full CLI/rehearsal/hash outputs. Keep full-history tests and tampering cases. |

Do not deduplicate versioned R2/R3 policies or promote a generalized serializer/hash
utility: canonicalisation, line-ending normalisation and immutable export semantics
are deliberately context-specific. A new utility inside Graph would change its
computed implementation closure and require separate provenance verification.

## Smallest useful Scout effectiveness follow-up — proposal only

Use the existing [V001/A/B FORGE proposal](opportunity_scout/prompt_evaluation_v001.json)
and [V002 instructions](opportunity_scout/prompt_research_v002.md): six matched
attempt blocks, two intended cards per attempt, three prompt variants, 18 attempts /
36 intended slots. This reuses the implemented balanced ordering and accounting;
no new evaluation subsystem is needed. It requires separate prospective approval,
runtime/resource bindings and completed N1 readiness. Do not substitute prompts in
the frozen V004 protocol or spend its reservations.

Before generation, freeze the existing research comparison corpus, all prompt/model
settings, attempt order, useful-hypothesis criteria and effort collection. Preserve
invalid, empty and failed attempts; cluster the same mechanism once per arm and
disclose overlap across arms. Two independent humans should review shuffled cards
with prompt IDs hidden, seal reviews before reveal, and disclose prior exposure and
content-based unblinding. If only AI review is feasible, label it AI-adjudicated,
record model/exposure/dependence and do not call it independent human validation.
Disagreements remain unresolved. Create no labels in this engineering task.

For each mechanism, separately assess economic coherence, novelty versus the frozen
corpus (external novelty remains uncertain), falsifiable predictor/outcome direction,
and a plausible source/measurement/join route with missing inputs explicit. Report
distinct useful mechanisms per total human supervision/review hour, with failed work
in the denominator; also report time per useful hypothesis, failure rate, clustering
disagreements, generation time and attributable usage/cost separately. UNKNOWN effort
or cost stays UNKNOWN. This tiny descriptive pilot can reject impractical prompts;
it cannot establish a small quality improvement, M/H passage or investment edge.

The separate N1 readiness work continues on its own branch under its existing
authority. This patch preserves its mainline fixture and Windows process coverage;
it does not inspect accounts, run Claude, supply owner consent or enable native
launch. The remaining live observer/runtime/consent gates stay unchanged.

## Verification receipt

Local Windows verification: **918 passed, zero skipped** (403 public, 264 Scout,
212 additional, 6 cross-process locks, 25 N1 collector and 8 selected guard tests).
The 11 method/class exclusions plus 5 isolated-parser tests are excluded explicitly;
they are not reported as passes. No original test method was edited.

| Workflow selection | Windows | Linux |
|---|---:|---:|
| Existing guarded public suite | 403 | 403 |
| Existing guarded Scout suite | 264 | 264 |
| Additional restricted suite | 212 | 212 |
| Portable guard tests | 7 | 7 |
| Native guard test | 1 Windows | 1 Linux |
| Actual Python process lock tests | 6 | 6 |
| Native N1 collector tests | 25 | Excluded: Windows assurance |
| Total selected | **918** | **893** |

The first native CI runs found the timezone, extended-path and descriptor issues
described above; those failed attempts remain in GitHub history. On code commit
`05f9d18`, both OS jobs passed the additional suite and their native guard test;
Linux also passed the existing public suite before this receipt was written.
The final full-workflow conclusions and links are recorded in
[draft PR #16](https://github.com/jarems421/ai-assisted-quantitative-research/pull/16);
[its checks](https://github.com/jarems421/ai-assisted-quantitative-research/pull/16/checks)
show the current exact-head outcome. Platform-conditioned workflow steps are
exclusions, distinct from unittest skips. The unchanged original Windows workflow
additionally repeats its original 698 tests; do not add these duplicates to the
unique coverage totals. These counts describe software fixtures, not research results.
