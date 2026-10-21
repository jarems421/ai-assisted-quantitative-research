# First real comparison — generation NOT_RUN

The prospective [V002 protocol](../evaluation_protocol_v002.json) was frozen in `a5bba7f`. [V001](../evaluation_protocol.json) is unchanged. Canonical manifest digest: `91cbdb59cc15c8666ed6c95ee5923a2ce12c7e27d8ff1d785565eb6e585cd7a2`. Each blueprint contains the exact batch, input pool, three full prompts and reserved attempts. There are no generated cards, responses or human judgments. Export is not invocation.

Every condition has six cards, three attempts of two cards, at most 6,000 output and 30,000 input tokens per attempt, 30 generation human minutes, 1,800 generation wall seconds and 180 review minutes. Actual usage/effort differences within caps are reported. Missing usage/effort leaves comparative eligibility false. Failed/abandoned attempts consume slots: no repairs, replacements, retries, best-of sampling or silent model substitution.

The common pool contains one approved **retrospective EF06 report excerpt** plus frozen catalogue memory. The source snippet was used in the old operator example, so its selection is not independent of development. **No old hypotheses or responses are used.** Fresh generators must never see them. The small, narrow pool limits generalisation. Descriptions establish no inspection activity, original fields or historical information advantage; old verdicts and source closures stand.

No eligible model was configured: `SCOUT_LOCAL_MODEL` absent, no Ollama executable on PATH, and no listener at `127.0.0.1:11434`. No model was installed or called. This Codex conversation is not an independent generator. Supplied material is approved for local use only; no hosted transmission or scientific acquisition is authorised.

Run from `C:\Users\runni\quant-opportunity-scout-v1`, choosing a new destination:

```powershell
$evaluation = '.research/opportunity_scout/real-comparison-v002'
python -m src.research.opportunity_scout install-evaluation $evaluation --package docs/opportunity_scout/first_comparison_v002
python -m src.research.opportunity_scout evaluation-requests $evaluation
python -m src.research.opportunity_scout evaluation-status $evaluation
```

Request paths are `$evaluation/CONDITION/exports/ATT-000N-evaluation-request.json`. Give **only that request** to a new, empty, independent local model context for each of the 12 invocations, including within a condition. Do not expose the generator to this repository, old examples or other responses. For an operator-assisted local run, bind one actual model and identical sampling settings **before invoking anything**:

```powershell
python -m src.research.opportunity_scout bind-evaluation $evaluation --model 'YOUR_PINNED_LOCAL_MODEL' --parameters your-sampling-parameters.json
```

The parameters file is the exact JSON object supported by the chosen model, e.g. `{"seed":0,"temperature":0.8,"num_predict":6000}`. Binding is appended to all four hash-chained archives and cannot be replaced. Workflow append times cannot supply unavailable invocation timestamps.

Save each single response as `{"attempt_id":"ATT-0001","provenance":{...},"output":{"ideas":[...,...]}}`. Keep actual model/provider/settings, server usage or UNKNOWN, and original output. Import into its own condition archive and record effort, including failures:

```powershell
python -m src.research.opportunity_scout schema provenance
python -m src.research.opportunity_scout schema generation-effort
python -m src.research.opportunity_scout import-response "$evaluation/PLAIN" your-plain-response-1.json
python -m src.research.opportunity_scout generation-effort "$evaluation/PLAIN" your-plain-effort-1.json
```

Repeat for three requests in each of PLAIN, EVIDENCE_ONLY, MECHANISM_ONLY and HYBRID, always with fresh contexts. Effort needs `attempt_id`, human actor, `human_minutes`, `wall_seconds`, unique `context_id`, `fresh_context`, `no_prior_generated_cards`, `invocation_status` (INVOKED / NOT_INVOKED / UNKNOWN), and description. Reservations are not invocations. Unknown values stay UNKNOWN. To correct effort, append another record with `correction_of` equal to the previous stored effort-record digest and a concrete `correction_reason`. `report CONDITION` exposes those records; history is retained.

Alternatively, if an authorised local Ollama model becomes available, use this **in a newly installed evaluation directory, before operator binding or generation**:

```powershell
python -m src.research.opportunity_scout run-evaluation $evaluation --local-model 'YOUR_ALREADY_INSTALLED_PINNED_MODEL'
```

This binds the runtime and uses all 12 frozen prompts in stateless requests, with no model pull or retry. Operator setup/monitoring time remains UNKNOWN until honestly recorded by effort corrections. It refuses automatic redispatch after a recorded attempt. Transport failure can leave actual invocation UNKNOWN.

After generation, inspect accounting. Create a local `private-salt.json` containing `{"salt":"a private random value of at least 20 characters"}`; keep salt and key private:

```powershell
python -m src.research.opportunity_scout evaluation-status $evaluation
python -m src.research.opportunity_scout blind-evaluation $evaluation --salt-file private-salt.json
python -m src.research.opportunity_scout evaluate-blind "$evaluation/exports/blinded-review.json" "$evaluation/exports/blinding-key-private.json" --judgments human-judgments.json
```

Incomplete actual attempt counts or missing cards block packet creation. Other accounting gaps appear in the sealed audit with `comparative_eligible: false`; human labels cannot repair generation accounting. The reviewer receives **only the public packet**, never key or condition reports. Content can reveal lanes: blinding is partial and procedural. Disclose reviewer involvement or familiarity.

Judgments are an array of actual human records: `blind_id`, `reviewer:{kind:"HUMAN",id:...}`, `independent_of_generation:true`, `coherent`, `falsifiable`, `research_worthy`, `evidence_integrity` (YES/NO/UNKNOWN), `minutes`, `notes`, and `atomic_answers` (yes/no/unsure) for `explicit_mechanism`, `evidence_supported`, `falsifiable`, `next_check_addresses_gap`, `certainty_exceeds_evidence`. Review all 24 original cards, without shortlisting or replacing weak ones. Missing/over-budget review effort is reported. No labels are supplied here.

Substantive mechanism diversity needs human comparison of transmission, roles and decisive measurements. External novelty and source verification remain NOT_CHECKED. READY feasibility and Discovery Lab M/H are separate decisions. No Jev results or investment outcomes are supplied; even a complete comparison is descriptive.
