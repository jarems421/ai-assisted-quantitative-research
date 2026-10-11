# Prepared Nexus support case: historical population pruning

**Prepared for owner review; not sent.** SDK 1.42.0; observed 2026-10-11. Public package contains an allowlisted derived summary and an existing synthetic request, not private raw event records. [evidence.json](evidence.json) is reproducibly generated from hash-verified local originals.

Problem: a historical source-defined common-stock universe cannot be published/executed without identity loss. Six large custom-indicator streams each requested 273,115 points and failed ticker validation (4,445 rejected rows, zero accepted). A separate four-row all-ones promotion fixture stored ADS, AHS, BBRY and AAPL under their original names. Its one-session daily engine request for 2015-01-02 produced pre-filter dynamic `universeSize=1`, AAPL only.

Existing backtest: `6acbf2738c2f7fb888b4df99`. Promoted dataset: `6acbf1ffedda2368845aa437`; indicator: `6acbf200edda2368845aa439`. Six events, one complete page, raw/noise/condition audit flags enabled, repeats uncollapsed. No candidate signals or alpha comparison were studied. This is a population failure independent of whether the fixture placed any trade; no performance result is included.

Minimal reproduction **description**, not a command to run:

1. Inspect the existing all-ones asset indicator at the IDs above; its four points refer to original historical symbols. The package's `synthetic_points` preserves all four fixture rows and their 2015-01-02T02:00:00Z availability.
2. Inspect the archived inline portfolio/request in `synthetic_reproduction_request`: `SPECIFIC_ASSETS` contains ADS/AHS/BBRY/AAPL, all-ones custom filter, equal value weights, 1% nominal deployment, open condition on exactly 20150102, Day interval, $25,000, cash dividends, fractional shares, 0.10% per-fill stock fee, events requested.
3. Compare the archived requested population to the archived pre-filter dynamic audit: expected 4; observed 1 (AAPL). There is no need to rerun to demonstrate the existing failure.

Questions for Nexus: Which documented API/asset identifier preserves renamed and ended common-stock histories at historical dates? Does the custom upload validator use today's symbol registry? Where does `SPECIFIC_ASSETS` drop unresolved identities, and can it expose an exhaustive pre-filter ID audit? How are class punctuation, ticker reuse, terminal merger/delisting values and position transitions handled? Provide route/version documentation and a behavioral evidence path meeting the [certification contract](../historical_execution.md#production-certification-contract). Storage acceptance alone is insufficient.

```sh
python -m src.research.support_case
python -m src.research.support_case --check
```

Both commands are offline. They require the ignored original receipts, verify all 191 indexed hashes and decode the existing complete event page. Only explicit allowed fields are exported; user/account IDs, prices, engine summaries and private market datasets remain private. Original request/event SHA-256 links are retained in the summary. Public clones can inspect this package but cannot independently verify private originals. Do not submit this request, republish data, send a support message or rerun diagnostics without separate authorization.
