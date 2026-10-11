# Historical-symbol capability and blocker audit

As of 2026-10-11. **No source-defined historical common-stock execution route is certified.** Existing evidence establishes source identities and numeric inputs, but the tested publication/runtime route changes the population. EXP004 is operationally paused; its scientific freeze and prior authorization artifacts remain historical records.

| Capability | Evidence class | What is established / still missing |
|---|---|---|
| Source stable IDs and dated ticker segments | VERIFIED within audited Development source | Source-defined CS population and numeric QA pass; not an all-US-market completeness certificate or independent vendor-vintage guarantee |
| SDK `universe('SPECIFIC_ASSETS', …)` and `dynamic_rebalance` | DECLARED and locally compiled | Builder accepts symbol assets; declaration is not historical security-ID execution support |
| Disclosed custom points/`availableAt`/schedule | DECLARED; schedule VERIFIED | 72-point SPY schedule published; general historical lookup, missingness and identity completeness need runtime evidence |
| Full historical-symbol uploads | FAIL in existing receipts | Each of six streams: 273,115 requested rows, zero accepted, 4,445 rejected rows, 92 reported symbol names; ticker validation is the reported failure column |
| MCP synthetic dataset → indicator promotion | VERIFIED storage only | Four original fixture symbols accepted; no assertion about their execution binding follows |
| Promoted fixture + `SPECIFIC_ASSETS` daily engine | FAIL in existing diagnostic | On 2015-01-02: ADS/AHS/BBRY/AAPL requested; dynamic universe size 1 and AAPL only, before the fixture's all-ones filter |
| Server punctuation normalization | VERIFIED error messages only | BF.A → BF-A in error text maps to unchanged original rows; this is not certified class identity normalization |
| Renamed and ended security execution | UNKNOWN beyond demonstrated failure | No verified public SDK/MCP binding resolving stable IDs across effective dates; support must specify route and boundary |
| Delisting/merger final value and class changes | UNKNOWN for production population | Historical row availability is not evidence of terminal cash recovery, correct positions, dividends or corporate-action execution |
| Native historical index membership | MIXED separate EXP002 evidence | Transition examples worked, but 72 monthly source populations underfilled; index source cannot substitute for EXP004 source universe |

Sources: unchanged [runtime audit](../../experiments/EXP004/research/publication_runtime_audit.json), [Development report](../../reports/EXP004_development_report.md), [SDK inventory](../nexus_sdk_inventory.json), [MCP inventory](../nexus_mcp_inventory.json), EXP002/003 final reviews. The Phase 1 audit used archived declarations and installed SDK 1.42.0; it did not rediscover remote account capabilities. A future server version could behave differently, but that is unverified.

## Production certification contract

Certification is scoped to a route, engine/version, source snapshot, freeze hash, permitted dates and exact payload hash. It is not a platform-wide claim and does not authorize execution.

1. **Dated identity lineage:** every source `security_id` has an audited asset-class-specific binding at signal lookback and execution. Renames, reuse, multiple classes, ended histories and ambiguous spans must have documented semantics. Source ticker bytes remain preserved; any platform binding is a separately evidenced mapping, never today's ticker projected backwards.
2. **Full publication:** requested points reconcile to ready accepted points by identity, decision, availability and value/hash. No silently dropped rows, partial upload, substituted symbol or hidden current-survivor screen. Disclosed visibility and exact-date guards are behaviorally verified.
3. **Full runtime population:** archive exhaustive **pre-filter** identities for every relevant decision. Compare exact stable-ID/historical-ticker pairs, not counts, holdings or only selected top-K. Any missing, extra, duplicate, unknown or substituted identity fails. Counts alone fail because equal-sized substitutions are possible. If server audits expose only symbols, an independently audited dated binding plus exhaustive symbol list is required; otherwise status remains UNRESOLVED.
4. **Selection and matched comparator:** common maximum-horizon validity population and date keys reconcile locally to runtime; ranks/top-K and EW use that same population. No candidate selection can conceal a pruned transport superset.
5. **Execution lifecycle:** bounded non-alpha fixtures cover renamed/ended identities, ticker reuse, share classes, splits, dividends, terminal consideration, empty population/liquidation, open timing, costs and unchanged holdings. Reconcile orders/positions/cash to declared semantics. Where semantics cannot be established, fail explicitly rather than claim complete execution support.
6. **Receipts and scope:** retain request, source/fixture hashes, idempotency key, returned IDs, full event pagination/noise/audits, history, versions, dates, actual/unknown costs and failures. Event-retention gaps fail completeness. Future production route certificate must enumerate all required decisions/identities and reference immutable passing evidence, not a hand-set boolean or a four-name probe.
7. **Independent operational authorization:** separate owner instruction lifts pause only after reviewing route evidence. Validation/Test remain gated. Unknown submissions are reconciled under original keys; no automatic retry or hidden replacement.

`src/research/capabilities.py` supplies exact reconciliation and a fail-closed wrapper. Caller assertions of completeness/binding require independent source receipts; passing the function does not certify them. Empty requested/observed populations can reconcile only with complete evidence and certified bindings; liquidation still requires its separate runtime gate.

The pause guards EXP004 client creation, source extraction, publication/reconciliation, submission and polling, and Research OS job execution/poll/reconciliation/paper paths. Local compilation, read-only saved-evidence analysis and semantic audit remain available. These are repository controls, not server access control; arbitrary SDK/MCP use outside them remains prohibited by owner instructions. No automatic resume is provided.

## Fallback assessment

| Option | Technical possibility | Authorization / recommendation |
|---|---|---|
| Nexus supplies stable-ID or date-aware historical binding | Plausible; currently UNKNOWN | Preferred if documented and certified; no new remote operations authorized |
| Existing dataset promotion | Storage works; tested execution FAILS | Cannot certify or resume production |
| Audited dated execution alias map | Possible only if platform retains original historical prices, class and lifecycle | No map exists; needs independently verified lineage and authorization, not current-symbol rewriting |
| Explicit per-asset actions instead of dynamic universe | SDK builders exist; historical binding and scale unknown | Would need certification and review; no implementation or probe authorized |
| Current-symbol pruning / present-day survivor universe | Technically easy; changes design and comparator | Rejected for EXP004; not an acceleration route |
| Another engine/vendor | Potentially feasible after independent data and execution audit | No purchase or second production backtester authorized; defer |
| Local SEC source pilot | Does not solve Nexus execution, but isolates information provenance | Recommended next bounded milestone; specification only in this phase |

The [prepared support package](nexus_support/README.md) contains the existing synthetic request and allowlisted observations. No support message was sent and no new diagnostic was executed.
