# Opportunity Scout V003: Claude subscription workflow

**V003 IMPLEMENTED / SYNTHETIC PREFLIGHT COMPLETE / REAL GENERATION NOT_RUN.**

V003 is prospective and separate from the frozen, local-only V002 comparison. No real research input has been sent to Claude. The prepared package is local under `.research/opportunity_scout/real-comparison-v003`; its manifest and runtime summaries are recorded in [first_comparison_v003](first_comparison_v003/README.md). Owner hosted-data consent and acceptance of the model-pinning limitation remain outstanding. Do not execute the real comparison as part of implementation validation.

## 1. Research account and executable

Run in Windows PowerShell, from the repository root:

```powershell
Set-Location 'C:\Users\runni\quant-opportunity-scout-v1'
$claudeExe = 'C:\Users\runni\AppData\Local\Microsoft\WinGet\Packages\Anthropic.ClaudeCode_Microsoft.Winget.Source_8wekyb3d8bbwe\claude.exe'
$researchConfig = 'C:\Users\runni\.claude-research'
$evaluation = '.research/opportunity_scout/real-comparison-v003'
Test-Path -LiteralPath $claudeExe
python -m src.research.opportunity_scout.v003 inspect --executable $claudeExe --config $researchConfig
if ($LASTEXITCODE -ne 0) { throw 'Claude inspection failed; stop.' }
```

These are PowerShell variables, not aliases or global environment changes. The adapter selects `CLAUDE_CONFIG_DIR` only in each child process. It requires the existing research credential-store file without opening its contents, then requires `auth status` to report Claude.ai, first-party, Pro/Max subscription authentication. It strips inherited API keys, OAuth tokens, endpoint overrides, other-provider selectors and IDE variables. No login, logout, configuration rewrite or API-key registration is performed. Never change the development account to repair a research-account failure.

Without `--executable`, discovery uses an actual executable on PATH, then the known WinGet location. An explicitly selected missing executable fails; it never silently substitutes another. PowerShell aliases are irrelevant. Inspection performs version/help/auth checks, not generation; output excludes account email, tokens and credential contents.

## 2. Authentication, isolation and model identity

The installed CLI is **2.1.302**. Fictional connectivity checks resolved `opus` to **`claude-opus-5-5`** and successfully selected that full ID explicitly. Real execution uses that full ID, never `opus`. Every observed model identity in initialization, assistant messages and `modelUsage` must agree with the binding. A mismatch is retained as a failed attempt and stops further dispatch. Medium is requested both by `--effort medium` and the child environment; effective effort is `UNKNOWN` when the CLI does not echo it.

The adapter supplies print/stream-JSON mode, a replaced frozen system prompt, JSON schema, empty tool selection, explicit empty MCP configuration with strict mode, safe and restricted modes, empty setting sources, disabled skills and Chrome, denied permission prompts, fresh UUID and temporary directory, and disabled session persistence. The only admitted callable tool is the CLI's `StructuredOutput` formatting tool. The synthetic checks reported no skills or MCP servers. Built-in agent/plugin **names remain listed** in initialization; the Agent/Skill tools are absent and no subagents were spawned. This is CLI isolation, not an OS sandbox or independent certification of Anthropic internals. Managed policy files/registry presence blocks preflight because policy hooks can survive safe mode.

`CLAUDE_CODE_MAX_RETRIES=0`, `CLAUDE_CODE_MAX_TURNS=1` and fallback-disabling controls are child-only. A second distinct assistant message or repeated formatting call is rejected. Thinking and output stream chunks with the same message ID are one visible generation. The original overly strict stream-chunk validation failure is retained; it was corrected through offline replay of the same fictional output, with no retry. Provider request count remains `UNKNOWN` even when a message/request ID is visible.

**Model-pinning decision required:** the canonical model ID is selectable and checked, but immutable provider weights/build and future server remapping cannot be verified. Official execution is blocked unless the owner explicitly accepts this limitation in the exact authorisation record. If that level of pinning is unacceptable, leave the comparison NOT_RUN.

## 3. Reproduce synthetic preflight

Mocked regression tests contact no model and use only fictional seeds/memory:

```powershell
python -m unittest discover -s tests/opportunity_scout -v
if ($LASTEXITCODE -ne 0) { throw 'Scout regression failed; stop.' }
python -m unittest tests.test_discovery_lab tests.test_graph -v
if ($LASTEXITCODE -ne 0) { throw 'Boundary regression failed; stop.' }
```

The following command **does contact Anthropic**, with only a fixed fictional Aster Crates / Lumen Packers arithmetic prompt and a tiny synthetic schema. It makes two visible invocations: alias discovery and explicit-ID verification. They consume no real comparison slot. Do not use arbitrary research text for preflight. Use a fresh output directory; do not overwrite the recorded check.

```powershell
$syntheticStore = '.research/opportunity_scout/my-v003-synthetic-preflight'
python -m src.research.opportunity_scout.v003 synthetic-preflight --store $syntheticStore --executable $claudeExe --config $researchConfig
if ($LASTEXITCODE -ne 0) { throw 'Synthetic preflight failed; inspect its retained receipt. Do not retry real slots.' }
$preflight = "$syntheticStore/exports/synthetic-preflight-v003.json"
```

The implementation's validated receipt is already at `.research/opportunity_scout/v003-validated-preflight/exports/synthetic-preflight-v003.json`. It preserves actual invocation timestamps, usage and raw synthetic CLI output, plus the hash/reason for the offline validator correction. Development-account file size/mtime checks were unchanged across the final two synthetic calls. No credential contents were inspected.

## 4. Prepare and validate frozen inputs

The prepared local package already exists. Inspect it without invoking a model:

```powershell
python -m src.research.opportunity_scout.v003 status $evaluation
if ($LASTEXITCODE -ne 0) { throw 'Frozen-package validation failed; stop.' }
Get-Content -LiteralPath "$evaluation/exports/comparison-manifest-v003.json"
Get-Content -LiteralPath "$evaluation/exports/comparison-runtime-v003.json"
```

Preparation for a **new** package, if needed, is offline:

```powershell
$newEvaluation = '.research/opportunity_scout/my-new-comparison-v003'
python -m src.research.opportunity_scout.v003 prepare $newEvaluation --preflight $preflight --package docs/opportunity_scout/first_comparison_v002
if ($LASTEXITCODE -ne 0) { throw 'Preparation failed; stop.' }
```

This replays V002's exact frozen blueprints into new append-only archives. It does not refresh the catalogue or import old generated ideas. New request files contain the exact transmitted text, schema and system prompt. The new manifest binds byte SHA-256 hashes of the files, source V002 provenance and implementation, together with the protocol, selected model and CLI preflight. Each attempt retains its original FORGE/RADAR/GAP/PLAIN allocation. The four conditions each reserve three attempts of two cards, totaling 12 attempts and 24 intended cards. New preparation times produce a different package digest; owner consent must match the actual package.

## 5. Review exact hosted-input authorisation

The current package already has **UNAPPROVED-owner-template-v003.json**. A new package can export its template once:

```powershell
python -m src.research.opportunity_scout.v003 consent-template $newEvaluation
if ($LASTEXITCODE -ne 0) { throw 'Template export failed; stop.' }
```

For the prepared package:

```powershell
Get-Content -LiteralPath "$evaluation/exports/UNAPPROVED-owner-template-v003.json"
Get-FileHash -Algorithm SHA256 -LiteralPath "$evaluation/exports/PLAIN-ATT-0001-request-v003.json"
Get-ChildItem -LiteralPath "$evaluation/exports" -Filter '*-request-v003.json'
Copy-Item -LiteralPath "$evaluation/exports/UNAPPROVED-owner-template-v003.json" -Destination "$evaluation/owner-reviewed-authorisation-v003.json"
```

Review all 12 request files locally, the protocol, source/file hashes, runtime, transmission scope and privacy statement. **Do not paste them into Claude for review.** Anthropic would receive each request's `transmitted_text`, `response_schema`, and `system_prompt`; eligible memory and the EF06 excerpt are included where the frozen lane specifies them. It does not receive the entire repository, other attempts' responses or the audit files merely because their hashes are listed.

The owner alone edits the copied record: set `owner_approved` to `true`, enter the actual `approving_owner`, enter the actual timezone-aware `approved_at` after package freeze, and set `accept_canonical_model_id_limit` to `true` only if accepted. Retain every other field unchanged. Approval is a human attestation, not a digital signature or proof of identity. An assistant must not fill these fields or infer consent from the subscription login.

Consumer subscription training and retention depend on the account's actual settings and terms; this task does not inspect or change them and establishes no zero-retention guarantee. Review them before approval. See Anthropic's [data usage](https://code.claude.com/docs/en/data-usage), [CLI controls](https://code.claude.com/docs/en/cli-reference), [environment controls](https://code.claude.com/docs/en/env-vars), and [managed-policy behavior](https://code.claude.com/docs/en/managed-settings).

After personally granting approval, import it locally. This command still does **not** generate:

```powershell
python -m src.research.opportunity_scout.v003 authorise $evaluation --owner-record "$evaluation/owner-reviewed-authorisation-v003.json"
if ($LASTEXITCODE -ne 0) { throw 'Owner authorisation rejected; stop.' }
python -m src.research.opportunity_scout.v003 status $evaluation
```

The import writes an immutable owner-authorisation file. Unknown identity/date, future or pre-freeze date, false approval, missing model-limit acceptance, different model, changed files or incomplete request coverage are rejected. Any source-code, CLI binary/help/version/auth/config or frozen-file drift also blocks execution. A changed package needs new prospective approval; never rewrite a started package.

## 6. Real execution — only in the separately approved next phase

**Do not run this command during implementation.** After the owner has supplied and imported valid consent:

```powershell
python -m src.research.opportunity_scout.v003 execute $evaluation --executable $claudeExe --config $researchConfig
if ($LASTEXITCODE -ne 0) { throw 'Execution rejected or interrupted; inspect status. Never redispatch.' }
python -m src.research.opportunity_scout.v003 status $evaluation
```

No manual copying of prompts/responses is needed. All checks precede generation. Each invocation receives only its frozen attempt input. A whole-run lock and a durable per-attempt event prevent concurrent dispatch and restart/retry after any dispatch. On invalid output, process failure, model/isolation error or token excess, remaining dispatch stops. A CLI failure can be recorded while the command returns a status object; **always inspect attempt statuses and counts**. A stopped run is incomplete, consumes its failed/interrupted slot and has no automatic continuation or replacement. Do not create a new comparison to hide a failed run.

The common caps remain 6,000 output / 30,000 input tokens per attempt, 1,800 generation wall seconds and 30 generation human minutes per condition. Output is requested at the cap; input usage is checked after response because the subscription CLI exposes no certified pre-dispatch tokenizer. Actual excess stops subsequent dispatch and is a deviation. Missing usage/effort blocks comparative eligibility. No additional API billing, paid enablement, scientific-source request, model fallback, Jev or market data is enabled.

## 7. Actual usage and effort

```powershell
python -m src.research.opportunity_scout.v003 status $evaluation
python -m src.research.opportunity_scout report "$evaluation/PLAIN"
Get-ChildItem -LiteralPath "$evaluation/exports" -Filter '*-invocation-v003.json'
```

Invocation receipts preserve original stdout/stderr unless apparent credentials require withholding, plus their hashes, safe arguments, explicit child controls, model metadata, usage components, measured monotonic elapsed time and timestamps. Receipt hashes are anchored in the append-only condition ledger. Known input totals include ordinary, cache-read and cache-creation input tokens. Thinking usage is separate when available. `total_cost_usd` is retained as a CLI list-price estimate, never a subscription invoice or actual charge; actual cost/currency remain UNKNOWN. Temperature and seed are UNKNOWN. One CLI process, one visible attempt and underlying provider requests are distinct; the last count remains UNKNOWN.

Setup/monitoring human minutes are never guessed. Before blinding, append honest per-attempt effort corrections with the existing CLI. Inspect the latest stored `generation_effort` record in `report`; its complete stored-record digest (including `kind`) is `correction_of`. Use the original measured wall/context values and a reason of at least five words:

```powershell
python -m src.research.opportunity_scout schema generation-effort
python -m src.research.opportunity_scout generation-effort "$evaluation/PLAIN" "$evaluation/owner-plain-effort-correction-1.json"
if ($LASTEXITCODE -ne 0) { throw 'Effort correction rejected; stop.' }
```

Repeat only with actual records for each attempt/condition, including all setup/monitoring time without double counting. Corrections append history; they cannot alter the fixed cards or invocation receipts. UNKNOWN time leaves comparison eligibility false.

## 8. Blinded human review and descriptive report

Create a private salt JSON locally, without publishing the salt or key:

```powershell
$saltFile = "$evaluation/private-salt.json"
$saltValue = [guid]::NewGuid().ToString() + [guid]::NewGuid().ToString()
$saltJson = @{ salt = $saltValue } | ConvertTo-Json -Compress
[System.IO.File]::WriteAllText((Join-Path (Get-Location).Path $saltFile), $saltJson, [System.Text.UTF8Encoding]::new($false))
python -m src.research.opportunity_scout.v003 blind $evaluation --salt-file $saltFile
if ($LASTEXITCODE -ne 0) { throw 'Blinded export rejected; stop.' }
```

Give the independent human reviewer **only** `exports/blinded-review-v003.json`. Withhold this guide's generator details, logs, condition reports, runtime, salt and `blinding-key-private-v003.json` until judgments are complete. All original cards, including weak, repetitive, invalid and surplus outputs, remain represented; missing reserved slots are explicit. Malformed non-card output remains in the private receipt, with missing slots visible. No repairs or selective review. Content can reveal lanes: blinding is partial and procedural. Disclose generation involvement/familiarity in notes; AI-assisted judgments are not independent human judgments.

The owner-provided judgments file is a JSON array. Each row requires `blind_id`, `reviewer:{kind:"HUMAN",id:"actual reviewer"}`, `independent_of_generation:true`, `coherent`, `falsifiable`, `research_worthy`, `evidence_integrity` (YES/NO/UNKNOWN), actual `minutes` or UNKNOWN, `notes`, and `atomic_answers` (yes/no/unsure) for `explicit_mechanism`, `evidence_supported`, `falsifiable`, `next_check_addresses_gap`, `certainty_exceeds_evidence`. No judgments are supplied by implementation. Review all slots; missing/invalid cards may receive UNKNOWN. The common review cap is 180 minutes per condition.

```powershell
python -m src.research.opportunity_scout.v003 evaluate $evaluation --judgments "$evaluation/human-judgments.json"
if ($LASTEXITCODE -ne 0) { throw 'Judgment import rejected; stop.' }
```

This imports the exact original judgment file into an exclusive, digest-named audit export with its descriptive report. It validates the sealed public packet/key and independent-human fields, reports missing reviews/effort and separate per-condition dimensions, and does not invent labels or a winner. Use distinct files for genuine amendments and retain prior reports. An identical import is refused rather than overwritten.

Substantive mechanism diversity still requires separate human comparison of transmission, economic roles and decisive measurements. No composite quality score, significance, novelty, profitable edge, Discovery Lab M/H approval or investment strategy follows. Jev remains a separately authorised optional shadow evaluator and is NOT_RUN here. V001/V002, Graph Pilot R3, Graph v1.1 and all source/experiment stops remain unchanged.
