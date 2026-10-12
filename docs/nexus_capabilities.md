# Nexus capabilities observed for Research OS v1

Current direction: [governing roadmap](acceleration/master_plan.md). This inventory records observed surfaces, not certification. Phase 3D permits only a disabled local adapter interface; no remote Nexus/Aurora call or EXP004 resume.

Inspected 2026-10-11 without submitting any Nexus job. Installed Python SDK: **1.42.0**. This session exposes **132 MCP tools** (the earlier VS Code discovery reported 136). Exact observed signatures and exposed tool declarations are in [SDK inventory](nexus_sdk_inventory.json) and [MCP inventory](nexus_mcp_inventory.json). These are local observations, not promises about every account's permissions.

| Task | Preferred surface | Actual operation / boundary |
|---|---|---|
| Deterministic simulations | SDK over versioned REST | `create_backtest`, `get_backtest`; explicit idempotency key; inline portfolio snapshots avoid draft creation |
| Sweeps / optimization | SDK over REST | `create_systematic_sweep`, `create_optimization`, corresponding getters; MCP `systematic_sweep` has `preview_only` and planned units |
| Walk-forward | SDK over REST | `create_walk_forward`, `get_walk_forward`; SDK `portfolio.walk_forward` builder; MCP preview returns fold/cost planning |
| History / events | MCP session bridge | `query_backtest_history` (up to 5,000 rows/page), `query_backtest_events` (50/page); events support raw JSON, noise, audits, uncollapsed repeats. No dedicated history/event reader found in SDK client |
| Aurora research | SDK or MCP | `create_agent` + `attach_agent` durable stream; MCP `create_agent`, `get_agent`, messages and trajectories. SDK has idempotency and optional USD ceiling; MCP has semi-automated mode |
| Agent evaluation | MCP | `run_agent_run_evaluator(agent_id, additional_context, model)`; optional paid action, not a general SDK method |
| Draft portfolios | SDK / MCP | `create_portfolio`, typed portfolio builders, explicit keys. Not required for inline backtests; not called during setup |
| Lake SQL / corpus | SDK | `create_lake_query`, `get_lake_query`, `lake.sql`, catalog/describe; MCP corpus search/screen also exists. SQL has parameters and idempotency; row-level availability and cutoff evidence still require audit |
| Dynamic cross-sectional selection | SDK builders | `dynamic_rebalance`, `universe`, `filter`, `select_top`, `select_percentile`, rank metrics, `Value` equal weighting or indicator weighting, holding/deployment limits; cadence belongs to strategy timing |
| Prospective turnover gates | SDK indicators | `rebalance_planned_turnover`, `rebalance_estimated_cost`, `rebalance_expected_benefit`, `rebalance_net_benefit` |
| Custom data | SDK / MCP | SDK custom indicator create/append/upload supports `observation`, `period_aggregate`, `disclosed`; MCP datasets and compute promotion exist. Filing/publication timestamps must be established independently |
| Paper deployment | SDK | `deploy` explicitly mints/activates paper from a chat draft, unlike brokerage operations. No idempotency parameter; never retry uncertain deployment automatically |
| Live brokerage / orders | Excluded | SDK exposes these but Research OS has no adapter or command for them |

The inspected SDK delegates to the observed REST base `https://nexustrade.io/api/v1`; Research OS uses SDK methods rather than inventing additional routes. MCP integration is an injected session bridge implementing `call(name, arguments)`, with exact observed names. It is deliberately not an invented REST endpoint or automatic OAuth implementation.

## Capability limits that affect safety

- Aurora exposes no SDK tool allowlist or sealed-date enforcement. A prompt is insufficient isolation. Remote Aurora execution is blocked in v1; role prompts, trajectory ingestion, and evaluation planning are available locally. A future audited server-side isolation mechanism is required before enabling agents. MCP semi-automated mode is not assumed to protect read-only sealed-data requests.
- SDK submission idempotency is available for backtests, sweeps, walk-forward, Lake, and agents. MCP backtest/sweep schemas have no idempotency argument. Use the SDK for repeated deterministic submissions.
- Backtest event traces have a documented three-day hot-store retention. Extract events first, then history, immediately after completion when events were requested. Never treat missing retained events as a complete audit.
- No account-specific live token-price endpoint was found in the exposed schemas/client. Pricing uses a dated, replaceable metadata file with an expiry; an expired quote blocks execution. Sweep and walk-forward server previews should supersede estimates when an authorized bridge is available.

## Pricing provenance

The configurable 2026-10-11 snapshot follows the official [backtesting cost documentation](https://nexustrade.io/docs/features/backtesting) and [optimizer formula](https://nexustrade.io/docs/features/optimization). Estimates account for calendar days, event multiplier, planned evaluations, asset factor, fold multiplier, and optimizer minimum. Estimates are not invoices; account exemptions are not assumed. Aurora requires a separately supplied current quote and USD ceiling. Documentation describes event generation more narrowly than the SDK; estimates conservatively apply its multiplier whenever events are requested. No live pricing or account entitlement was queried.
