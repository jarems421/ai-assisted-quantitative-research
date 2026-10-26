# Connected offline investigation rehearsal V001

This campaign-side integration references native records. It adds no source dispatcher,
scientific gate, scheduler, acquisition permission or source-discovery request schema.
The existing `campaign_evidence_v1 rehearse` and its foundation-only outcome remain
unchanged. This is a distinct rehearsal with actual native custody completion.

**Integration base:** Source Custody PR #46 merged into main at
`2329502099621ca3722f0dc9f1426149d1e4ba89`. This branch incorporates that actual merge.
Native custody is mandatory: missing custody refuses the command before creating a
rehearsal and causes the connected tests to fail. There is no dependency-based test
skip, and the restricted runner's no-skip rule is unchanged. Earlier provisional
rehearsals remain separate historical artifacts; they are not silently upgraded.

## One command, one fictional original

Choose a **new standalone directory outside every Git checkout**:

```powershell
python -m src.research.campaign_connected_v1 rehearse --out C:/Users/runni/research-os-connected-example-001
python -m src.research.campaign_connected_v1 verify C:/Users/runni/research-os-connected-example-001/connected-checkpoint
```

The first command creates a synthetic Scout archive and campaign branch, writes
unmistakably fictional scope/stop-attestation/claims/inspection fixtures, and runs
native Source Retrieval with a fixed in-memory transport. The only two transport
operations are fictional robots.txt and the fictional register; neither performs DNS,
HTTP, sockets or a process launch. There is no runtime/URL/provider selection.

It then uses the native custody import, verifies its completion, exports those same
bytes through Quarry, and supplies **that export** to the existing offline operator.
The operator performs deterministic Jev navigation and its existing Discovery preview
checklist. All phases run under the existing audit boundary. Native custody's temporary
staging is routed within the rehearsal root rather than permitting writes across TEMP;
this fixture command is serial and is not safe for concurrent use in one interpreter.

`connected-checkpoint/checkpoint.json` contains the reconstructed lineage, native
operator completion and checklist. `seal.json` pins its exact byte SHA-256. `verify`
checks the seal and re-derives the native chain without invoking any native activity.
Changed inputs, code, completion or artifacts require reconciliation; nothing is
repaired, redispatched, imported again or overwritten. These hashes establish record
consistency on a trusted local filesystem, not human identity or source truth.

Expected outcome: `CONNECTED_CUSTODY_TO_ANVIL_HUMAN_GATES_REMAIN`, with native
`ANVIL_CHECKS: BLOCKED`. The fictional original supplies text, not an admitted predictor
observation or independent outcome. All six M judgments remain `NOT_REVIEWED`, software
does not certify M, and `research_outcome` remains null. Synthetic READY fixture records
are explicitly identified by the native operator and are never real human approvals.
Missing READY still prevents candidate drafting even if custody and Jev complete.

## Exact lineage contract

`CAMPAIGN_CONNECTED_ANVIL_CHECKPOINT_V001` is an immutable **derived checkpoint**.
It is not a new authoritative campaign ledger, source result or custody record.

The selection names exactly seven things: `campaign` root, `branch`, `source_activity`,
exact `url`, `package`, `export`, and `operator_activity`. For already retained records,
save this small selection as JSON and run:

```powershell
python -m src.research.campaign_connected_v1 seal selection.json --out C:/Users/runni/new-connected-checkpoint
```

This only validates references and writes a new checkpoint. It does not run Source,
custody, Quarry, Jev or the operator. The selected operator activity is the subject of
the checkpoint; it is not designated the authoritative branch run. Existing ambiguous
branch summaries remain ambiguous. There is no timestamp or stage-order selection.

| Boundary | Required native identity and verification |
| --- | --- |
| Campaign → Source | Validated campaign/companion journals; existing attached source activity; exact campaign/branch, original Scout archive bytes, card ID/version/hash and Scout history; native request/result/journal/receipt bindings re-derived with `observe_source` |
| Source → custody | Current native `preflight`; receipt belongs to the attached result and exact URL; native body bytes/hash/size; original approved route/version; **native `status == CUSTODY_COMPLETE`** and a retained completion file |
| Custody completion | Exact claim and completion byte hashes; completion binds the original claim and canonical sealed-package manifest through the native validator; claim names this exact package; package retains receipt/result/claims |
| Custody → export | Native package/export validation; exported portable package equals the completed package (excluding its storage root); original body, retained provenance, supply and manifest agree; exact operator-derived Scout subject |
| Export → operator/Jev | Explicit completed operator reference for this branch; exactly one complete export with the same path and manifest byte hash; native Jev workspace re-derives from that exact export input; deterministic-only, no imported response |
| Operator → Anvil | Reuse `campaign_evidence_v1.checkpoint.operator_view`: exact native completion/report, admitted preview ledger hash, workflow bundle, replayed Discovery checklist and human blockers |

Quarry stores canonical registry JSON while Source preserves its original input bytes.
The integration compares validated registry values, retains the Source input's exact
byte hash separately, and binds Quarry's own manifest. It never rewrites either copy
or treats different serialisation as changed source authority.

The connected path currently requires a COMPLETE attempt and COMPLETE target transfer.
Native custody's separate support for retaining some partial/negative outcomes is
unchanged. Those outcomes remain native records and companion references; this command
refuses to describe them as a complete connected rehearsal. No missing completion is
inferred from an otherwise valid package. A separately created valid export cannot
replace the one actually consumed by the operator. Multi-export collections are outside
this bounded lineage version.

Coverage, limitations, missing fields, UNKNOWN publication authenticity/dataset
completeness and NOT_ESTABLISHED scientific meaning are retained. Reservations and
consumption are quoted from the attached source result; no aggregate charge is computed
and campaign allocations are never added to component reservations. No Forge batch cost
is copied or counted again.

## Interface reconciliation and boundaries

The implemented Source Retrieval and custody contracts govern, rather than the
historical design tab in `source_discovery_shared_interface_v001.md`. The integration
uses existing request/result identities and `QUARRY_SUPPLY_V002.system_retrieval`;
it does not implement reserved search, extraction, host-amendment or field-support
records. No files in Source, custody, Quarry, Jev, Scout, Discovery, the operator,
`campaign_v1` or the foundation companion are changed.

The synthetic command is the only effectful entry here and is fixed to fixtures.
It is not a production scheduling API. Native no-replay, claims, locks, stops, code
bindings and owner drift rules remain authoritative. Old runs created before Quarry
V002 retain their old implementation bindings and are never silently upgraded.

Before the first real owner-authorised investigation:

1. Review and merge this integration after validation against the actual merged
   custody implementation, including Windows/Linux CI at the exact PR head. Adopt
   the reviewed implementation bindings separately from any research authority.
2. Select the exact real card/version and decisive question. Obtain the owner's real
   bounded exact-URL scope, fresh implementation binding, component reservation and
   human-attested historical stop reconciliation. The synthetic fixtures supply none.
3. Have the designated human provide real custody claims and original/extraction
   inspection records. Caller/attester names are not authenticated identity. Native
   transport provenance and source authenticity limitations still apply.
4. Run any actual retrieval/custody only under a separate explicit owner instruction.
   Search-to-route admission and production campaign scheduling remain unimplemented.
5. Preserve current Scout READY for approved continuation, a real human crosswalk for
   any supplied Discovery ledger, field interpretation, M/H reviews and dispositions.
   An incubated card may receive separately authorised source investigation without
   being relabelled READY; this patch adds no permission or automatic transition.
6. Stop at Anvil with an actual measurement assessment or an honest blocker. No
   Crucible, predictive study, strategy, trading or downstream authority follows.
