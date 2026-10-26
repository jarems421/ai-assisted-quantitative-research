# Campaign evidence and Anvil checkpoint V001

This read-only integration references existing Source Retrieval attempts and
existing Campaign V001 operator activities. It performs no retrieval, model call,
source planning, source-request export, human approval, ledger write or scientific
promotion. Its synthetic rehearsal stops at Anvil's existing gates.

Reviewed base: `e607e3f`, merged main containing PRs #43, #44 and #45. Claude's
Quarry SUPPLY V002 and custody bridge are independent work and are not implemented
or emulated here.

## Compatibility and ownership

Campaign V001's implementation hash covers every Python file in `campaign_v1/`
and the native operator binding. Even adding a file there would change existing
campaign identities and refuse mutations. Instead, this versioned companion lives
in `src/research/campaign_evidence_v1/` and stores only metadata references under
`<base>/campaign-evidence-v1/<campaign>/`:

- Immutable `companion.json` binds the exact original campaign manifest bytes,
  creation event, campaign ID/path and current companion/campaign/source verifier
  implementations. It grants no authority.
- Append-only, hash-chained `events.jsonl` has `CREATED` and `SOURCE_ATTACHED`
  events, using Source Retrieval's existing generic journal/fsync primitives.
- An exclusive `companion.lock` protects writers. A leftover lock or incomplete
  journal is refused, never stolen, deleted automatically or repaired.

The original campaign manifest, vocabulary, journal and reporting are unchanged.
It still owns branch/card identity, eligibility, native operator references and
shared Forge batch accounting. The companion cannot add branches, authorise work,
select a successor among multiple operator runs, or become a scientific ledger.
Source Retrieval owns its native results/receipts; Discovery owns its checklist
and human review semantics. All bindings assume a trusted local filesystem and
reviewed Python, not authenticated execution, human identity or hostile tamper
resistance. No signed human trust is created.

## Exact native source reference

`CAMPAIGN_SOURCE_ACTIVITY_REFERENCE_V001` is a reference record, **not** a new
source request/result or custody handoff schema. Every admitted reference has:

| Fields | Meaning |
|---|---|
| `schema`, `campaign_id`, `branch_id` | Reference version and exact native campaign branch |
| `hypothesis` | Original Scout archive path, archive journal SHA-256, card ID/version/canonical card SHA-256, current Scout journal head |
| `source_base`, `request_id`, `attempt_id` | Native source records base and exact identities |
| `request_sha256`, `result_sha256` | Exact native file byte hashes, including whitespace |
| `implementation_sha256` | Source Retrieval implementation recorded by the native claim/refusal; must equal the current pinned verifier implementation |
| `scope_sha256`, `reservation_ref` | Native scope hash and exact request hash/field identifying `resources.reservation`; no new reservation or approval |
| `status` | Native NOT_STARTED, COMPLETE, STOPPED, UNAVAILABLE, PARTIAL or UNKNOWN, kept distinct |
| `journal` | Exact journal byte hash, event count/head, incomplete-tail indicator and last original recorded timestamp |
| `finalisation_sha256` | Exact native finalisation hash, or null; never fabricated by attachment |
| `receipts` | Verified native receipt paths/hashes, body hashes, original times, coverage, termination and limitations; originals and receipts are not copied |
| `authorises` | Always empty |

**Archive hash admission rule:** Source V001's `archive_sha256` field does not
define a directory hashing algorithm. This consumer requires it to be SHA-256 of
the exact `scout.jsonl` bytes in the registered original archive. It is explicitly
not a directory-tree digest or a hash of a re-serialised card. Existing requests
using another meaning are refused; no native request is rewritten. The native
Scout replay also checks the admitted prefix and exact latest card version/hash.
Later original-journal changes make an old source binding stale. Legitimate
working-copy human progress remains separately owned by the operator.

Attachment calls native `source_v1.retrieve.verify`, which re-derives the result
from the journal, receipts, retained bodies and recorded inputs. It then obtains
native verified receipt references and repeats verification/anchor checks. It
never trusts `result.json` alone or constructs a receipt from it. A result is
admitted only when anchored and actually written. Pending/interrupted attempts
need native owner reconciliation first; this module never finalises them.
Verified interrupted finalisations can remain UNKNOWN, with locks retained.
Historical unbound/pre-claim results lacking an implementation identity are
refused rather than assigned the current identity.

Activity IDs must be distinct from original campaign operator activity IDs.
Attempt and request IDs cannot be attached twice under new activity IDs or copied
bases. Exact reattachment adds nothing. Changed native bytes or code are refused;
old events remain retained. Other branches continue to report independently.
If original Campaign V001 later introduces a colliding operator activity ID, the
checkpoint flags the collision; it never rewrites either ledger.

Native verification establishes record consistency, **not** original authenticity,
terms/access permission, human identity or independently observed execution.
Owner scope hashes are references, not campaign-created approvals. A downloaded
document never establishes Scout READY, a Discovery candidate, a confirmed field,
M/H, or research progress. An INCUBATE branch may reference a separately scoped
native activity, while its approved Scout continuation remains blocked at READY.

## Commands

The native campaign, branch and completed activity must already exist:

```powershell
python -m src.research.campaign_evidence_v1 --base <base> create <campaign>
python -m src.research.campaign_evidence_v1 --base <base> check-source <campaign> <branch> --source-base <source-base> --attempt <attempt>
python -m src.research.campaign_evidence_v1 --base <base> attach-source <campaign> <branch> <activity> --source-base <source-base> --attempt <attempt>
python -m src.research.campaign_evidence_v1 --base <base> checkpoint <campaign>
python -m src.research.campaign_evidence_v1 --base <base> checkpoint <campaign> --out <base>/campaign-evidence-v1/<campaign>/checkpoint-001.json
```

`check-source` is read-only and shows native INTERRUPTED/RESULT_PENDING states
without attaching them. `attachment_eligible` is only a current reference-admission
diagnostic, never execution authority. No proposed request is registered or
authorised by this companion. Campaign's disabled source descriptor stays disabled.
Output snapshots are exclusive/create-only and confined to new `checkpoint-*.json`
children of the companion directory. Re-reading a checkpoint writes nothing.

Source V001's own base rules still apply: records inside this checkout must live
under `.research/`; another Git checkout is refused. Use an owner-supplied portable
copy in a standalone directory when appropriate, retaining bytes and IDs, and the
exact pinned source implementation. Code drift requires the pinned environment
or a separately identified new companion/code epoch; there is no drift override.
Native source hashes include line-ending bytes, so cross-platform verification
does not silently normalise a source implementation binding.

## What the Anvil checkpoint means

The deterministic JSON view includes each original campaign branch projection,
all individual operator states and all source references. Multiple native runs
remain `AMBIGUOUS_NATIVE_REFERENCE`; order, timestamps and apparent stage depth
never select an authoritative successor. Invalid/advanced references require
reconciliation through their existing native component, without replay.

For a valid operator reference, the checkpoint uses native completion/report
verification, revalidates each recorded Quarry export, verifies deterministic
Jev bundles without reading/importing responses, and replays the pinned Discovery
ledger through Discovery's existing checklist. The ledger must still match the
native workflow input hash; a changed ledger/export is refused. Preview records
stay SYNTHETIC. Supplied ledgers without a current handoff/crosswalk stay unlinked;
they are not presented as an admitted continuation or independently checked here.

The view separates registered hypotheses, native source outcomes, unregistered
proposals, retained bytes awaiting custody, validated independent Quarry exports,
Jev navigation, candidate/passport drafts, actual checklist blockers and native
human action groups. It preserves native statuses/limitations instead of inferring
progress. Field confirmation is not established by custody/navigation. Human M
judgments, where actually present, remain the native checklist's judgments; this
view never awards M. `research_outcome` remains null and downstream is NOT_AUTHORISED.

Campaign allocation and native source reservations/consumption are displayed
separately. No source costs are aggregated, reservations refunded, unknown usage
converted to zero, or shared Forge batch multiplied by branch count.

## Rehearsal foundation and the missing custody seam

```powershell
python -m src.research.campaign_evidence_v1 rehearse --out <new-standalone-directory>
```

This runs the existing operator's synthetic fixtures/stages for a ready fixture
and an unready fixture, attaches their completed native records, and attaches a
native, explicitly synthetic NOT_STARTED source refusal. No source claim, scope,
stop attestation or dispatch is made. The refusal is built from native record and
derivation primitives and then checked with the native verifier. Existing native
fixture reviews are SYNTHETIC_FIXTURE, not invented human approvals.

It writes `checkpoint.json` once and reports
`FOUNDATION_ONLY_CUSTODY_BRIDGE_NOT_CONNECTED`. The ready operator's *independent*
synthetic Quarry inputs demonstrate Jev/drafts/checklist blockers; they are never
labelled as evidence from the refused source attempt. A second branch waits at
READY. Existing inputs produce cached native one-shot results, never replayed
operations. The report demonstrates workflow/refusal handling, not source acquisition
or a fully connected source-to-Anvil success.
Projection of retained records is deterministic and clock-free. A fresh rehearsal
retains the native operator's actual timestamps and its selected output paths;
separate fresh runs are not claimed to have identical journal bytes or hashes.

Claude must supply a verified native custody receipt/API that binds the exact
source request/attempt/result, eligible receipt/body hashes and coverage to its
Quarry package/export manifest and exact Scout subject. Its schema/version,
verification function and immutable artifact roots remain to be reconciled. No
schema name or fake receipt is guessed here. A validated export alone does not
prove that lineage. Once agreed, the existing operator accepts verified exports
through `RESEARCH_OS_OPERATOR_EVIDENCE_V001.exports` (label + path); this PR neither
calls the new bridge nor changes its interface. Missing/incomplete custody remains
explicit and no downstream source handoff can be inferred.

## Verification

`python -m unittest tests.test_campaign_evidence_v1 -v` uses fictional records,
existing Source Retrieval fake transports and synthetic operator fixtures only.
Tests cover exact identities, immutable/idempotent references, negative statuses,
verified finalisations, tampering, ambiguity, stale/code drift, native Anvil waits,
crosswalk/M gaps, no INCUBATE promotion, and strict IO boundaries. Its inventory
entry runs under the restricted offline guard on Windows/Linux. No real owner
scope/attestation or human review is authored; synthetic test doubles cannot grant
LIVE authority. Frozen component implementations and historical records are unchanged.
