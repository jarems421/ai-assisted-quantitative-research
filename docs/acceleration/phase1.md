# Research acceleration: Phase 1 audit

As of 2026-10-11. **The fastest safe next milestone is a small accession-specific SEC ingestion pilot, while the existing Nexus historical-symbol case awaits a certified route.** No alpha experiment, remote diagnostic, freeze or paper deployment starts in this phase.

The owner approved milestone-by-milestone work in this order: certified data and execution → economically motivated forecasts → independent evidence of incremental alpha → risk-aware portfolio construction → forward paper evidence. The Phase 1 attachment explicitly says “EXP004 is operationally paused” and prohibits its candidate, benchmark, diagnostic, publication and other Nexus operations. That newer instruction supersedes continued execution language in the preserved historical Development report. [Operational pause](../../config/operational_pauses.json) is external to scientific stage; EXP004 remains `HYPOTHESIS_FROZEN` with both freeze versions unchanged. EXP001–EXP004 historical records are preserved.

## Reuse before building

`STEAL` means reuse the repository's implementation directly; it does not mean copy external code.

| Area | Decision | Existing implementation and evidence | Small remaining need |
|---|---|---|---|
| Submission, quota and idempotency | STEAL | `src/research/nexus.py` reserves durable jobs/trials before transport, hashes exact requests, serializes quota checks, retains UNKNOWN and requires reconciliation | No adapter rewrite; server-side idempotency behavior remains narrower evidence than local fake tests |
| Polling, receipts and pagination | STEAL | `nexus.py`, `extraction.py`, `store.py`: bounded reads/backoff, events first, raw/noise/condition audits, pagination exhaustion checks, immutable hashes, resumable IDs | Existing MCP extraction bridge required; event retention prevents assuming later re-extraction |
| Custom data | ADAPT | `custom_signals.py`, `exp004_streams.py`, `exp004_publication_reconcile.py`: disclosed availability, exact date/validity streams, versioned create intents | Publication acceptance and simulation identity are separate gates; no historical-symbol workaround certified |
| Historical identity | ADAPT | `pit_signals.resolve_identity`, `exp004_compile.py`, source QA and runtime audit; historical effective segments, stable IDs, shared maximum-horizon population | Shared exact population reconciliation added; platform dated binding still absent |
| Immutable provenance/PIT | ADAPT | `RawStore`, wire receipts, Parquet part hashes, `pit_signals.py`, existing EXP002/003 version/zero contracts | Byte-preserving SEC acquisition and accession manifest; do not infer zeros from absent filings |
| Trial accounting/stages | STEAL | SQLite `Store`, exported journals, schema/range/hash checks, family and evaluation ceilings, candidate controls, separate owner Test/paper gates | Operational pause added outside scientific state; no automatic freeze |
| Statistics/selection | STEAL | Frozen `performance.py`; `analysis.py` controls, parameter neighborhoods, fold alignment, regimes, moving blocks; `exp002_inference.py` paired effects and experiment policies | Tools exist, but no EXP004 strategy returns exist; generic Holm implementation is not an approved experiment inference policy |
| Capability reporting | BUILD (small) | Existing SDK/MCP inventories plus EXP004 audited receipts | This report, support summary generator and a scoped certification contract; no capability framework |
| SEC foundation | BUILD (next milestone only) | SQLite, DuckDB and PyArrow already available | [Three-filing pilot specification](sec_pilot.md); no backfill or new installed dependency now |
| Alpha factory / optimizer / dashboards | DEFER | Existing bounded grids, controls, reports and planning suffice for current research | Require data/execution gates, economic hypothesis and incremental evidence before portfolio optimization |

The audit reviewed the Research OS implementation, tests, EXP001 processed metrics/report, EXP002/003 final gate failures, EXP004 specification/state/trials, both receipts and source/runtime QA. All **191** indexed private runtime receipts matched their SHA-256 values. Raw audit evidence was inspected locally; no private raw file is copied into documentation. Baseline: **164 tests passed**. [Capability report](historical_execution.md) distinguishes software declarations from runtime evidence.

## Dependency and licence audit

No dependency was added or upgraded in the research environment. The owner's follow-up explicitly authorized downloading required dependencies, including PyArrow; an isolated pilot environment was prepared within Phase 1. Versions below distinguish the existing research environment from that preparation.

| Dependency | Declared / installed | Licence and obligations | Disposition |
|---|---|---|---|
| Python / SQLite | Python 3.13; `sqlite3` standard library | Python licence; SQLite public domain; packaged components still have notices | Reuse |
| nexustrade | `==1.42.0` / 1.42.0 | Installed MIT licence; retain copyright/permission notices if redistributing code | Reuse; SDK licence does not grant vendor data redistribution rights |
| jsonschema | `>=4.23,<5` / 4.26.0 | Installed MIT `COPYING` | Existing bounded range retained; exact transitive lock deferred to pilot environment |
| duckdb | `==1.3.2` / 1.3.2 | [Core MIT licence at pinned tag](https://raw.githubusercontent.com/duckdb/duckdb/v1.3.2/LICENSE); bundled experimental Spark compatibility contains separate Apache-2.0 notice | Reuse SQL/Parquet facilities; retain applicable bundled notices |
| pyarrow | `==20.0.0` / 20.0.0 | Installed Apache-2.0 licence; preserve notices and applicable bundled third-party notices | Retain research environment pin |
| matplotlib | `==3.11.2` / 3.11.2 | Installed Matplotlib licence; retain notices; bundled fonts have their own licences | Presentation only |
| tzdata | `==2026.5` / 2026.5 | Installed Apache-2.0 package notice; timezone data has distinct upstream provenance | Reuse timezone support |
| edgartools | Isolated `==5.62.0` with `pyarrow==23.0.1`; absent from research environment | Installed MIT licence and resolved dependency notice inventory recorded | Metadata requires `pyarrow>=23.0.1`, conflicting with existing 20.0.0 pin; isolated installation preserves research environment |

Installed distribution licence files were inspected. No repository licence is invented; [publishing boundaries](../publishing.md) still apply. SEC publicly available submissions can contain third-party exhibits; public fixtures should be synthetic unless redistribution rights have been checked. The [isolated wheel lock](sec_pilot_requirements.lock) and [44-package notice/hash inventory](sec_pilot_dependency_inventory.json) record the preparation. No `[ai]`, cloud or hosted-service extras were installed. Unidecode is GPLv2-or-later; certifi, tqdm and orjson have MPL obligations; other packages retain their own notices. Dependencies are installed locally, not bundled or relicensed in this repository. Review redistribution obligations before distributing an environment or derived third-party code.

The isolated environment is ignored at `.research/sec-pilot-venv`. `pip check` passes; EdgarTools imports with external connections prohibited (Windows asyncio loopback permitted). PyArrow 23.0.1 writes a synthetic EXP999 Parquet table that existing PyArrow 20.0.0 and DuckDB 1.3.2 both read exactly. These dependency smoke checks do not certify filing parsing, throttling, SEC availability or historical identity. No filing retrieval or pilot implementation occurred.

## Backlog ordered by research value

| Priority | Milestone | Concrete completion gate | Why now / scope |
|---:|---|---|---|
| 1 | Small SEC accession pilot | Immutable bytes, deterministic parsing, four timestamp concepts, class identity and all [acceptance tests](sec_pilot.md) | Tests information provenance cheaply without predicting returns; no Nexus dependency |
| 2 | Nexus route certification | Support supplies documented dated binding; separately authorized bounded behavioral evidence passes [contract](historical_execution.md#production-certification-contract) | Removes the existing execution bottleneck; prepare support case now, owner decides whether to send/run |
| 3 | One economically motivated forecast specification | Predeclared mechanism, data cutoff, matched control, family/evaluation ceiling, net-cost falsification rule | Only after pilot evidence; EXP005 remains uncreated and unfrozen |
| 4 | Independent incremental-alpha study | Certified full population, complete Development folds and ablations, fixed selection and descriptive/inferential claims distinguished | No claims from software tests or source counts |
| 5 | Risk-aware construction | Evidence that forecasts add net value; predeclared risk/cost constraints and comparison to simple weights | Avoid optimizing unsupported forecasts |
| 6 | Forward paper | Separate human authorization after review; genuinely forward evidence measured after freeze | No paper/live operation in Phase 1 |

Minimal changes are operational guards, shared reconciliation, synthetic regression tests and offline allowlisted support packaging. Reconciliation is a reusable contract component, **not a replacement certificate** and is not wired into immutable historical signal/metric code. The existing EXP004 publication boolean is insufficient on its own; future certification integration must bind the full evidence described in the contract before execution is re-enabled.

## Verification and phase boundary

```sh
python -m unittest discover -s tests -v
python -m src.research audit EXP004
python -m src.research.support_case --check
python -m src.presentation.exp001 --check
```

Support check requires existing private receipts; the synthetic tests and public report require no remote access. Historical frozen artifacts, reports, processed results and experiment directories were byte-compared against the pre-change snapshot. Publication/runtime failure remains a failure regardless of software test outcome. The full suite includes existing deterministic EXP001 integration tests with its already-opened local records; this phase does not query any held-out data remotely or use those results to select fixtures.

Phase 1 validation: **176 tests passed** (164 existing, 12 new synthetic checks); EXP004 semantic audit passed at unchanged `HYPOTHESIS_FROZEN`; offline support verification passed against all 191 indexed receipts; presentation check passed all six deterministic artifacts. No historical artifact mismatch, research-environment dependency change or Nexus call occurred. Isolated dependency preparation additionally passed `pip check`, external-network-blocked imports and synthetic cross-version Parquet reading.

**Stop here.** Next decision: authorize the bounded SEC pilot implementation described in the specification. Sending the prepared Nexus case and any new diagnostic require separate authorization; no broad six-week infrastructure programme, historical SEC backfill, EXP005 freeze or remote performance study is implied.
