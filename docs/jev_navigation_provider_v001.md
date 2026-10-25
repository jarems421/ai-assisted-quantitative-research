# Jev navigation: TypeSafe adapter and Quarry integration V001

2026-10-25. Additive integration over main `78d3f7c` and Quarry PR A. No research
provider or source was called. No live permission, effectiveness result, M/H decision,
campaign or study activation follows from this code, tests, draft PR or a merge.

## Existing contracts reused

The original `jev_navigation_v1` package and its historical fixtures remain byte
unchanged. `jev_navigation_integration_v1` uses its pinned workspace, questions,
record universe, deterministic blockers, citations, ranking and evaluation metrics.
All three tasks work: Evidence Prospector, Armoury/Graph Memory Navigator and Discovery
Workflow Navigator. No legacy Jev critic client is imported or revived. Forge provider
validator/reporting and all Scout, Graph, Discovery and Level A closures are unchanged.

The adapter accepts an existing navigation workspace. With `--quarry-export`, it also
requires a valid Quarry export whose re-derived bundle exactly equals that workspace.
Every later load revalidates the portable source package, original/text hashes, source
versions, stops, restrictions, question definitions, exact payload and implementation.
Quarry citations/restrictions stay in the supplied records sent as state; Jev neither
downloads nor certifies anything. Every report and inspection row has `authorises: []`.

## Official API verification

Public documentation was reviewed on 2026-10-25, without calling an authenticated
endpoint. The [System One API reference](https://docs.typesafe.ai/api/system-one)
specifies `POST https://api.typesafe.ai/v1/systemone`, bearer authentication, supplied
`state`, named `questions`, `model`, returned `answers`/model and token usage. The
[Choice specification](https://docs.typesafe.ai/primitives/choice) explicitly defines
`type`, `instructions` and the named `criteria` map. The response includes the selected
option, probabilities and confidence. These are documented fields, not an inferred
free-text protocol. The existing yes/no/unsure vocabulary stays a three-option Choice;
no conversion to binary Noul or probability threshold is introduced.

The [confidence formula](https://docs.typesafe.ai/confidence) defines the statistic
checked by the response validator. Ties and explicit unsure remain abstentions. The
exact option keys, distributions, argmax, confidence and integer usage are validated.
The raw response is never corrected or replaced. Invalid results retain their bytes
and give the deterministic baseline, with an explicit failure count/status.

The [models reference](https://docs.typesafe.ai/models) documents `jev-1.13.0` and
`jev-1.14.0`, default context limits and current input-only pricing. The
[authenticated model-list reference](https://docs.typesafe.ai/api/list-models) describes
account-scoped listing. The models reference warns that lists may contain aliases
without the versioned IDs. Consequently an alias listing is insufficient verification
of the exact version. No model-list call occurs here; eventual activation requires
independently obtained account-specific version confirmation. This may require a
provider/account confirmation outside the adapter. No version is silently substituted.

Reviewed contract facts and URLs are recorded in
`docs/jev_navigation_provider_v001/typesafe_contract_v001.json`. Public docs do not
verify any user's account, runtime identity, availability, hard billing cap or invoice.

## Prepare and inspect, with no activation

```powershell
python -m src.research.jev_navigation_integration_v1 prepare .research/jev-navigation-v1-quarry --quarry-export .research/quarry-v1-handoff --model jev-1.14.0 --out .research/jev-provider-v1-request
python -m src.research.jev_navigation_integration_v1 report .research/jev-provider-v1-request
python -m src.research.jev_navigation_integration_v1 demo --out .research/jev-provider-v1-demo
```

`prepare` creates exact `payload.bin` and `plan.json` in a new private ignored workspace.
It creates no credential, activation form or owner judgment. The operator inspects
those exact bytes. The payload uses only documented fields; it keeps the existing
bounded questions and supplied state. It is limited to 64 KiB by this adapter, not a
claim of verified provider tokenization. Provider context errors remain preserved
failures. There are no images, long-context headers, tools, URLs to fetch or SDKs.

There is **no dispatch CLI command**. The independently testable Python `dispatch`
entry point defaults to `enabled=False` and refuses before reading credentials or
account evidence. A later separately authorised operator integration could explicitly
enable it only after satisfying every gate below. This task never enables real HTTP.

## Owner activation gates and spend boundary

`workspace.APPROVAL` is the strict completed-approval schema; assistants must not fill
LIVE approvals or create account verification records. A future human owner supplies:

- The exact plan/payload hashes, permitted data classification and explicit disclosure
  approval, named owner, timezone-aware approval/expiry window, and one-request cap.
- A non-secret account context, fresh independently obtained account evidence (hashed
  and retained) confirming the exact version, effective price and output billing.
- Independent confirmation of an enforceable provider/account hard spending limit,
  remaining allowance no greater than the owner's cap, and a private durable audit
  directory. This code cannot create or independently verify that account control.

The conservative maximum default-context reservation is **2,753 micro-USD**, rounded
up from 65,536 input tokens at 42 USD/billion. It is never released, even after a
failure. Returned usage is retained, but **actual cost remains UNKNOWN**: token usage
is not an invoice. Input usage above the reviewed bound is invalid and never ranked.
There is no documented request-level dollar limiter in the reviewed API; the account
hard-limit evidence is therefore mandatory. If that control or exact version cannot
be independently established, LIVE dispatch stays blocked. This is not an assertion
that TypeSafe offers such a cap to any particular account. Account-wide concurrent
activity, refreshed pricing and the external billing configuration are owner concerns
to verify prospectively; no local reservation can itself enforce a remote bill.

Only a named `TYPESAFE_API_KEY` environment credential is read, at actual dispatch.
There is no `.env` loading, login, token extraction, credential inspection, browser
automation, hosted-model fallback or provider substitution. Development/tests use
`fixture_transport` with SYNTHETIC evidence and SYNTHETIC approval/account doubles;
these cannot activate the production transport. No real key is needed for tests.

The workspace and owner-managed audit directory both receive a create-only attempt
claim before any launch. A workspace/plan permits one attempt. Partial/interrupted
claims cannot resume or retry. Retain the audit directory: copying/deleting every
claim and mutable local hash is not prevented by cryptography or authenticated
identity. Approval records are operator attestations, not proof of a human identity.

The direct transport performs one fixed-host TLS POST with a 30-second socket timeout,
one MiB response bound, no redirect following, retries, proxies or fallback. Raw bytes
are written and fsynced in bounded chunks before parsing. Oversize capture keeps at
most one MiB plus its overflow marker byte, stops reading and is never parsed. HTTP
denials/redirects, malformed answers, model drift and transport exceptions are retained
failures. Only exception type is recorded, never exception text that may expose secrets.
Interrupted capture remains UNKNOWN; do not claim zero requests after a launch marker
without evidence. Reports use `{at_least, exact}`; synthetic transport records explicitly
have zero external requests. Keep raw response/account evidence files private.

The requested and returned models, payload/raw hashes, usage, HTTP status, reservation
and unknown actual cost are retained. Their binding is local capture provenance:
**the provider is not assumed to echo or authenticate a request hash**. A returned
model string is provider-reported identity, not proof of runtime execution or accuracy.

## Evaluation readiness

The [existing prospective protocol](jev_navigation_v001/evaluation_protocol.md) remains
the evaluation authority. Independently assemble and label a private frozen holdout
before viewing output; assistants must not supply human labels, reasons, exposure
declarations, seals or consensus. Do not use the public designer controls as a holdout.

`freeze-evaluation <provider-workspace> <registration.json>` records opaque hashes
of separately supplied labels and their independence/exposure record, the exact
request/record universe, fixed budgets and endpoints, and a separately supplied
complete structured-search/analyst baseline ordering. It does not open the labels or
put them in the payload. The existing keyword/Graph baseline is also retained. The
registration must precede dispatch and its hash is included in the attempt claim.

`compare <workspace> <labels.json> <independence-record>` verifies those hashes and
reuses `evaluation.at_budget` for precision, recall, false priorities, missed important
evidence, unresolved labels and abstentions at the same budgets for all orderings.
It reports invalid-response counts/status, exact citations and stop preservation.
Full human time accounting, independent assembly and judgments remain external
records; the software does not certify them. Synthetic transport results cannot be
relabelled as an independent human holdout or established accuracy.

## Demonstrations and remaining owner actions

The demo retains a fictional original, an F1 measurement lead, an F2 decoy and an
ambiguous passage, then exercises the exact provider-shaped payload/raw response with
an injected transport. It compares fixed inspection budgets to both baselines, keeps
the whole queue and abstentions, and leaves the Anvil packet pending. Tests also cover
contradictory workflow classifications: deterministic HOLD/stops always win. Nothing
writes Graph/Armoury memory, Discovery records, source decisions or human judgments.

For a small real evaluation the owner must separately approve an independently
labelled frozen holdout, exact payloads/classification, account/version and billing
controls, request/spend caps, and stopping arrangements. Source acquisition remains
absent from Quarry V001; only separately authorised or owner-supplied documents enter.
Real human Anvil inspection and exact-study readiness are subsequent independent acts.
No accuracy, scientific authority, source authenticity or real-study readiness has
been established by the offline end-to-end software demonstration.
