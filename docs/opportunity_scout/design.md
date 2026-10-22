# Opportunity Scout v1: design and implementation boundary

Starting main commit: **`5f3b7ef91cfca8e7d13661a577a67751165c65cd`**. Worktree: `quant-opportunity-scout-v1`; branch: `codex/opportunity-scout-v1`. The uncommitted main/pilot work and `codex/research-workspace` are excluded. No merges are authorised.

The owner's task authorises local offline engineering and evaluation, not source acquisition, paid inference, hosted transmission of unpublished research, or scientific adjudication. Discovery Lab, Graph v1, M/H, experiments, source stops, pilot state and their tests remain unchanged. New files stay in `src/research/opportunity_scout/`, `tests/opportunity_scout/` and this documentation directory.

## Report reading record

Read all **21 pages** of *Opportunity Scout Phase One: Building a High-Signal Idea Engine for Research OS*: 235,339 bytes; SHA-256 `5337da8156910b3f3d79c5b16f48fca8271518ff0bfeb28ce4da13bb7d713e30`. The supplied original and extracted text are retained under ignored `data/raw/opportunity_scout_20261021/`. The PDF is not redistributed. Its internal filecite tokens are interface references, not source certificates. Literature statistics and commercial comparisons below are attributed to the supplied report, not independently reproduced research results.

| Report pages | Recommendation | Implementation decision |
| --- | --- | --- |
| 1–6 | Co-Scientist, AI Scientist, retrieval-guided ideation and evaluation failures: generation and independent criticism serve different purposes | Generator output never verifies evidence or supplies independent review labels. Critic and external-novelty imports retain their own provenance. No automated experiments. |
| 2, 7–9 | Independent evidence, mechanism and research-memory lanes; constraint inversion | Separate frozen prompts. Forge receives neither seeds, historical memory nor another lane's ideas. Gap Explorer receives validated V002 gaps, original verdicts and citations; it must explain a changed domain and measurement requirement, without reopening prior work. |
| 4–6, 10 | MAP-Elites principle; diversity collapse | Fixed mechanism × evidence-maturity niches, separate sector/role/lane/requirement/pathway coverage, exact-core duplicates and uncertain mechanism proximity. No global quality score or evolutionary infrastructure. |
| 8, 11–12 | Source facts first; explicit conjectures; immutable cards | Approved bounded local seeds, four separate clocks, per-link assumptions, inherited evidence depth, immutable versions and replay-validated hash chain. UNKNOWN stays unknown. |
| 12–14 | Atomic Jev with abstention and shadow evaluation | Official TypeSafe request/response boundary, explicit unsure option, original distributions and confidence retained. Never routes, deletes, rejects or certifies. Hosted calls require separate payload-specific authorisation; no call is part of this build. |
| 14–16 | Four equal-budget conditions; independent blinded review | Frozen protocol below, identical card format, generation labels removed from reviewer packets, missing human judgments reported. Content may reveal the lane: blinding is procedural and partial. |
| 16–20 | Separate later outcome labels; incubator; postpone learning | Append-only effort, selection, research outcome and human M/H record references. Exact identifier/requirement reconsideration creates leads only. No learned weights, training, prompt adaptation, confidence thresholds or alpha prediction. |

The report supports directions, not proof that they improve financial research. Literature results do not transfer automatically to this domain. AlphaSense/Hebbia descriptions establish neither private investment usage nor a proprietary opportunity. Novelty remains separate from investment value.

## Existing contracts

Read the Discovery Lab design/guide, Graph v1 design/review, Measurement Gate M, strategic reorientation review, existing record/ledger validators and V002 catalogue. The authoritative vocabularies, canonical hashing and graph operators are reused rather than replaced. Historical F01/F03/F09/F19/SH09/EF03/EF06 reports supply bounded memory; a historical conclusion never becomes an original observation.

The scout checks structure, provenance consistency and next-question specificity. It does **not** implement another M/H checklist. READY means a human has marked an idea suitable for considering a separately authorised investigation; it is not M/H passed. The handoff is a proposal envelope because scouting-time fields cannot honestly satisfy a full Discovery Lab candidate record.

Runtime design: standard Python plus the existing jsonschema dependency; one bounded hash-chained JSONL archive per batch; strict JSON records; deterministic views; local CLI. Local Ollama is an optional generation provider. Operator-assisted prompts and responses use the same importer and validators. No fixture fallback is permitted.

Official integration references checked 2026-10-21: [TypeSafe System One](https://docs.typesafe.ai/api/system-one), [models](https://docs.typesafe.ai/models), [confidence](https://docs.typesafe.ai/confidence), and [Ollama generate](https://docs.ollama.com/api/generate). Requests are bounded, have no retries or redirects, and record returned model/usage separately from requested parameters. Costs remain UNKNOWN unless reported. Confidence is not used as a calibrated task probability. Independently operated Jev gateways are not the official endpoint and are not used.

The frozen evaluation protocol is committed before implementation or examination of demonstration outputs. Later engineering fixes preserve the protocol and disclose changes; they never tune selection against observed outcomes.
