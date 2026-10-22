# Graph Pilot R4: roles and operational runbook (version 001)

> **DRAFT FOR OWNER REGISTRATION — NOT ACTIVE — NO EXPERIMENTAL AUTHORITY.** Nothing here authorises a source request, packet, arm session, review or report. It binds only if the R4 activation document names it by hash. R4 is NOT_RUN.

Companion documents:

- [Reviewer guide](graph_pilot_r4_reviewer_guide_v001.md)
- [Source plan](graph_pilot_r4_source_plan_v001.md)
- [Activation template](graph_pilot_r4_activation_template_v001.md)
- [Readiness](graph_pilot_r4_operational_readiness_v001.md)
- Protocol: [R4 draft](graph_pilot_r4_protocol_proposed.md)
- Engineering: [Phase A v003/v004](graph_pilot_r4_readiness_v004.md), [Phase B v003](graph_pilot_r4_phase_b_v003.md)

Every command below exists in the merged code at `9ac56d3`; this runbook adds no tooling.

## 1. Roles and boundaries

| Role | Duties | May access | Must never |
|---|---|---|---|
| **Research owner** | Registers the activation (all owner fields); confirms open access and terms (E2); writes the hypothesis-first mechanism statement; decides stops, deviations, M/H reviews and dispositions after unsealing | Everything, but see the restriction to the right | Adjudicate, operate an arm, or read `key.json`, alias keys, arm ledgers or reviewer logs before both seals are committed. This is procedural: the owner *can* read every file |
| **Arm operator** (one per session, or the same person throughout) | Prepares and verifies the environment; runs source preflight and packet formation; starts and stops each arm session and writes its START and STOP attestations personally; supervises the arm analyst for procedure and safety only (section 1.1) | Packet bundle, the fetch tool, and during a session only the procedural and safety information in section 1.1 | Read a packet's substantive arm outputs before both arms of that packet have finished (section 1.1); review any item of a packet they operated; show arm records to reviewers; attest a session they did not personally start or stop |
| **Arm analyst** (see decision D1) | Runs one campaign under the fixed arm instructions (appendix) | Only its own worktree, the frozen packet and the catalogue | See the other arm, another packet or any earlier pilot ledger |
| **Blinding preparer** (the owner, or a technical assistant who never reviews) | Runs `blind`, `realias`, `leak-scan` and `sheet`; builds the evidence pack and the reviewer bundles; keeps `key.json` private | A packet's arm outputs and key, only after both of its arms have finished | Review; tell a reviewer anything about arms; operate or supervise any campaign that has not yet finished (as in revision 2, the preparer is neither arm) |
| **Reviewer R1** and **reviewer R2** (two different humans) | Judge every item independently from the reviewer bundle only; write both logs; seal personally; hand over the seal first, the logs later | Reviewer bundle, evidence pack, reviewer guide | See arm records, keys or exports other than `blind_v2.json`; see or discuss the other reviewer's work; use AI assessments; fetch sources (unless authorised) |
| **Technical assistant** (for example an AI coding assistant) | Run validators and checks on request; prepare drafts of records for a human to approve | Only as the owner directs, logged | Write, edit or seal any judgment, exposure declaration, attestation, M/H review, disposition or deviation; act under a human's name. The code refuses assistant names, but cannot detect an assistant using a human's name |

### 1.1 Cross-arm isolation (from revision 2, restored)

As the [pre-registration](graph_pilot_preregistration.md) requires, **the operator does not read a packet's arm ledgers, connection logs, suggestion exports, session transcripts or other session output until both arms of that packet have finished.** This applies when the same human operates both arms, and it applies to the owner.

- **What the operator may see during a session:** elapsed time against the ceilings; the arm's account totals (starts, searches, bytes); validator pass or fail; tool refusals; and critical-stop signals.
- **What the operator may answer:** procedural and safety questions only. Both arms of a packet get the same procedural answers.
- **What the operator never does:** relay, summarise or hint at any record, source, connection, suggestion or finding from one arm to another arm or packet.
- **If substantive content is seen anyway** (for example a permission prompt quoting a record), the operator records a deviation at once, naming the arm, what was seen and when. The operator does not use it, and the pilot continues only if the owner judges it was not a critical stop.

## 2. Operational sequence

### Stage 0: offline environment preparation, then registration

**0a. Prepare the environment (operator, before registration; offline, no source request).**

1. **Checkout.** A dedicated full-history clone, checked out at the code commit to be pinned. No shallow clones, rebases or squash merges for the whole pilot.
2. **Python.** One Python environment. No installs, upgrades or removals from now until the final report. The pin records Python and dependency versions; any change refuses every pinned operation.
3. **Record** the pinned content digest and runtime with the existing code:

   ```
   python -c "import json; from src.research.graph import implementation as I; c=I.content(); print(json.dumps({'tree_digest': c['tree_digest'], 'runtime': c['runtime']}, sort_keys=True))"
   ```

   Also record the full package list (`python -m pip freeze`) and the checkout's commit.
4. **Offline self-tests:**
   - `python -m src.research.graph build --check`
   - `python -m src.research.graph pilot r4-dry-run --check`
   - `python -m src.research.graph pilot r4-phase-b-dry-run --check`
5. **Configuration.** Use the registered graph configuration, [V002](graph_pilot_r4_graph_configuration_v002.json): `GRAPH_OPERATORS_V1_1`, `GRAPH_CLASSIFICATION_V1_2` and generic register V001. V2 snapshots default to it. Never pass `--classification` unless the owner has registered a deviation.

**0b. Register (owner).**

1. **Activation.** Fill every owner field of the [activation template](graph_pilot_r4_activation_template_v001.md), copying the digest, runtime and code commit from 0a. Commit it as `docs/strategy/owner_graph_pilot_r4_<date>.md` to `main` before any request.
2. **The document does not contain its own commit SHA.** The activation commit is identified afterwards from Git history and recorded in the Stage 1 receipt:

   ```
   git log --diff-filter=A --format=%H -- docs/strategy/owner_graph_pilot_r4_<date>.md
   ```
3. **What it fixes:**
   - the code pin and the prepared runtime;
   - the source routes and reserves (from the [source plan](graph_pilot_r4_source_plan_v001.md));
   - the people;
   - the schedule;
   - the ceilings;
   - the consensus and blinding rules;
   - the hypothesis-first mechanism statement.

### Stage 1: frozen environment verification (operator, before any source request)

1. **Advance.** Move the prepared checkout forward to the activation commit, or to a later `main` commit, with no change to the Python environment. The activation document lies outside the pinned implementation boundary, so the digest is unaffected.
2. **Verify.** Re-run the 0a record command. The digest and runtime must equal the registered values exactly. Then re-run the three self-tests.
3. **Mismatch.** Any mismatch or failure means no source request. A changed environment needs a new owner registration; never re-pin silently.
4. **Receipt.** Write and commit a short activation receipt, `docs/strategy/graph_pilot_r4/activation_receipt.md`. It records:
   - the activation commit (from 0b.2);
   - the running commit;
   - the digest and runtime match;
   - the self-test results;
   - the time.

### Stage 2: source preflight and packet formation (operator)

1. **Probe.** For each method in order (observation, relationship, event), probe the registered environments in their fixed order. Each probe is one request:

   ```
   python docs/strategy/graph_pilot/fetch_one.py data/raw/graph_pilot_r4_<date>/<packet>/probe URL --purpose "..." --max-starts N --max-bytes 4194304
   ```

   No retries. A 403, 404, other denial, timeout or oversized response is a stop for that route.
2. **Assess.** Judge eligibility E1–E8 on that one response alone ([pre-registration](graph_pilot_preregistration.md#packet-eligibility-and-selection)).
3. **Select.** Select records mechanically: sort by record date, then identifier; take the first five, or all if only three or four qualify.
4. **Fallback.** If an environment fails, try the next registered one; when all fail, the packet is **NOT_FORMED**, and that is preserved.
5. **Hypothesis packet.** The hypothesis-first packet is the owner's committed mechanism statement and spends no source starts.
6. **Record and freeze.**
   - Record the packet ledger with the Discovery Lab CLI (`python -m src.research.discovery ...`) and copy the bundle.
   - Freeze from a clean checkout:

     ```
     python -m src.research.graph pilot snapshot docs/strategy/graph_pilot_r4/<P>/snapshot.json --packet <P> \
         --packet-ledger docs/strategy/graph_pilot_r4/<P>/packet.jsonl --bundle <bundle> \
         --arm-ledger S docs/strategy/graph_pilot_r4/<P>/S.jsonl DLC-GR4-<P>-S --arm-ledger G docs/strategy/graph_pilot_r4/<P>/G.jsonl DLC-GR4-<P>-G \
         --connection-log GRAPH_PILOT_CONNECTION_V2
     ```

   - Commit the snapshot before any arm starts. It pins the commit, the implementation content, the runtime, the operator version and the classification. `r4_configuration.conforms` must be `true`; a `false` snapshot is never a conforming packet.

### Stage 3: arm sessions (operator and analyst)

1. **Order:** P1 S then G; P2 G then S; P3 S then G; P4 G then S. One session per campaign.
2. **Start.** Immediately before a session, the operator personally runs:

   `python -m src.research.graph pilot session-attest docs/strategy/graph_pilot_r4/<P> --arm <A> --event START --by "<operator name>"`

   The attestation is written once and must be recorded before the arm's first record.
3. **Run the campaign** under the [appendix instructions](#appendix-arm-instructions-r4-draft), on branch `graph-pilot-r4/<P>-<A>`.
4. **Arm G captures every suggestion.** It saves the snapshot-mode `--json` output of every suggesting query (`suggestions`, `revisit`, `complements`, `shared`, `same-gap`, `next`) to `docs/strategy/graph_pilot_r4/<P>/suggestions-G/NNN-<command>.json` at query time.
5. **Logging.** Rows are V2 connection rows, written as each item is considered. A graph-originated row keeps its exact `SUG-` origin, operator, bases and class.
6. **Stop.** After the arm's last record, the operator personally runs `session-attest ... --event STOP`.
7. **Close checks.** The arm runs them; the operator sees only pass or fail and the account totals (section 1.1):
   - `python -m src.research.discovery validate <ledger>`
   - `python -m src.research.graph pilot account <snapshot> --arm <A>`
   - `python -m src.research.graph pilot effort docs/strategy/graph_pilot_r4/<P> --arm <A>`
   - `python -m src.research.graph pilot connections <log> --arm <A> --suggestions <exports...> --packet-snapshot <snapshot>`
8. **Commit** to the arm branch; do not merge. Candidates are frozen before any outcome is inspected; any post-outcome change is a new version.
9. **Cross-packet isolation.** Arm branches stay off `main` and out of every campaign's view until Stage 7. No later campaign, packet or reviewer may be given an arm branch, ledger, log or export. Branches in a shared repository can be read with git, so this is procedural, as the arm instructions state.

### Stage 4: blinding (blinding preparer)

Blinding of a packet starts only after both of its arms have finished.

1. **Blind:**

   ```
   python -m src.research.graph pilot blind <snapshot> --log S <S log> --log G <G log> --salt <16+ chars> --out <P>/blind.json --key <private>/key.json
   ```

   This validates every V2 row against the replayed suggestion export, refuses any mismatch, and seals the export and attestation hashes in the key. **Keep `key.json` outside the repository until both reviewers' seals are committed.**
2. **Alias:** `pilot realias <P>/blind.json --out <P>/blind_v2.json --alias-key <private>/alias.json`.
3. **Sheet:** `pilot sheet <P>/blind_v2.json --out <P>/adjudication_sheet_v2.md`.
4. **Leak scan:** `pilot leak-scan <P>/blind_v2.json <P>/adjudication_sheet_v2.md --own-from <P>/blind.json` must report **0 findings** for both files, or nothing is shown to anyone. `--own-from` is required: without it the scan cannot detect arm-own record ids, which was the R3 V001 failure.
5. **Evidence pack.** Copy each original cited in `blind_v2.json` into a folder of files named `<sha256>`. The files come from the packet bundle and the arms' receipted bodies. Verify every hash, and never copy arm paths or receipts.
6. **Reviewer bundle** for each reviewer: the pinned code checkout instructions, `snapshot.json`, `packet.jsonl`, `blind_v2.json`, the sheet, the evidence pack and the reviewer guide. No arm ledger, connection log, suggestion export, session attestation or key.

### Stage 5: independent review and sealing (R1, R2)

1. Each reviewer works alone, from their bundle, following the [reviewer guide](graph_pilot_r4_reviewer_guide_v001.md). They write `adjudications-R.jsonl` and `warning-usefulness-R.jsonl`. These are explicitly empty files for a zero-item packet.
2. Each reviewer runs `pilot adjudication-seal <bundle> --reviewer R --by "<name>" --saw-arm-info ... --operated-or-attested-arm ...`.
3. Each reviewer sends **only the seal file** to the operator. The logs stay with the reviewer.

### Stage 6: reveal (operator)

1. **Seals.** Commit both seal files, in one commit or two.
2. **Logs.** Only after both seals are committed, collect both reviewers' logs, byte-for-byte unchanged, and commit them in a later commit. Reveal order is VERIFIED only if each log first appears strictly after the other reviewer's seal commit, and every commit of each seal and log path holds exactly the sealed bytes. Re-committing a changed seal or log, committing a placeholder, or committing logs together with seals is VIOLATED.
3. **Agreement.** Run `pilot adjudication-agreement docs/strategy/graph_pilot_r4/<P>`. This gives agreement, consensus, item and reviewer exposure status, the reveal order and conformance. It reads the logs only, never the key.

### Stage 7: unblinding, sensitivity and report (owner)

1. **Wait for the whole pilot.** Stage 7 begins only after both of these are true:
   - every campaign of every formed packet has finished, or stopped and been preserved;
   - every formed packet has completed Stage 6: both seals, then both logs, committed.

   Until then:
   - no `key.json` is committed;
   - no arm branch is merged into `main` or exposed as research memory;
   - no arm ledger enters any campaign, packet or review.

   This preserves revision 2's rule that pilot records become research memory only after all campaigns and adjudications finish.
2. **Unblind.** Place each packet's `key.json` in its packet directory and commit it. Then merge every arm branch into `main` with a merge commit. Never squash, rebase, delete or rewrite an arm branch or any commit named in a receipt or seal, so full Git ancestry is preserved.
3. **Re-check reveal order.** Re-run `pilot adjudication-agreement` for every packet on the merged `main`. Reveal order must still be VERIFIED before the report runs; a change is a critical stop.
4. **Report.** Run `pilot report docs/strategy/graph_pilot_r4/P1 ... P4 --export blind_v2.json`. The report applies:
   - **the cohort boundary:** only R4-conforming packets are primary;
   - **the consensus rule:** both reviewers must agree;
   - **the effort-evidence gate:** self-reported minutes are primary; attested-session minutes are a sensitivity;
   - **the blinding sensitivity:** potentially unblinded packets are included and labelled, an exclusion sensitivity is run, and if the two disagree the result is INCONCLUSIVE;
   - **the minimum:** at least three comparable conforming pairs, or INCONCLUSIVE.
5. **Reported separately:**
   - review burden: every item reviewed, including discarded suggestions;
   - unknown-time counts;
   - excluded packets with their reasons and deviation records;
   - warning usefulness, kept apart from economic connections.
6. **Owner decisions after unsealing.** M/H reviews and dispositions under Measurement Gate M follow; they are never recorded for the owner.

## 3. Stops, incomplete packets and preserved failures

| Event | Handling |
|---|---|
| A route denial, timeout or oversized response | That route stops for the pilot; no retry or bypass; preserved with its receipt |
| All registered environments of a method fail | The packet is NOT_FORMED and preserved. The pilot continues with fewer pairs. No substitute is chosen after seeing content |
| An arm hits a ceiling or 120 minutes | The campaign ends where it is; it is preserved and reported |
| A non-conforming snapshot, missing or invalid seals, CONFLICTED or NOT_INDEPENDENT judgments, or a reveal-order violation | The packet is excluded from the primary comparison and listed with its reasons; owner deviation records are preserved and never re-admit it |
| A critical stop: cross-arm or cross-packet access (including operator exposure to substantive arm output that the owner judges material), an arm branch merged or a key committed before Stage 7, an unverified record presented as verified, a ledger mutation, a paid, authenticated or stopped route, a budget breach, market-data access, or an export shown before the leak scan passes | Halt the pilot and report to the owner. Nothing is deleted |

## 4. Procedural risks code cannot remove

1. **Private reviewer communication.** Seals, reveal order and exposure declarations are evidence, not proof. Mitigation: reviewers are recruited separately and instructed in writing; each signs the seal statement; the owner asks each, after unsealing, whether they had any contact.
2. **Exposure to arm keys.** `key.json`, alias keys and arm ledgers are ordinary files; anyone with access can read them. Mitigation: keep keys outside the repository until both seals are committed; restrict who holds the arm branches; declare any exposure.
3. **False human identity attestations.** A START or STOP attestation, a seal or a judgment under a human's name may in fact have been written by someone else or by an assistant. The code refuses assistant names, but cannot detect impersonation. Mitigation: named people only; a technical assistant never writes under a human's name; the owner records who held which role.
4. **History rewriting and clocks.** Git order is graph topology, not wall-clock proof; dates are self-declared. Mitigation: keep full history, use a synchronised clock, and allow no force-push.
5. **Arm analyst knowledge.** If arm analysts are AI sessions, their prior knowledge of public events is uncontrolled. Two arms share the same analyst type, so this affects both, but it is not removable.

## Appendix: arm instructions R4 (draft)

> Adapted from [R3 arm instructions](graph_pilot/arm_instructions_r3.md). Binding only when the activation document names the exact text. `{...}` fields are substituted by the operator and nothing else is added.

You are the **{ARM}** arm analyst for R4 packet **{PACKET}** ({METHOD}). Your authority is `{ACTIVATION_DOC}`. Read it, `docs/strategy/graph_pilot_r4_protocol_proposed.md`, `docs/strategy/discovery_lab_guide.md` and `docs/strategy/measurement_gate_m.md` first.

- **Isolation.** Work only in your worktree on branch `graph-pilot-r4/{PACKET}-{ARM}`. Do not open any other arm's, packet's or earlier pilot's files. Do not list, check out, diff, log or read any other branch. Never name a tool or arm in a record's text. The operator answers procedural and safety questions only.
- **Start.** The operator has attested your session START. Verify the bundle: `python -m src.research.graph pilot verify docs/strategy/graph_pilot_r4/{PACKET}/snapshot.json --bundle {BUNDLE}`. Create campaign `DLC-GR4-{PACKET}-{ARM}` (fixture `LIVE`, the activation as authority, budget from the activation).
- **Budget** (hard; stop before any breach): {MINUTES} wall-clock minutes; {STARTS} source starts with `fetch_one.py` only; {SEARCHES} searches; {BYTES} response bytes. Unused budget does not carry over.
- **Sources.** Free, public, unauthenticated original-publisher records only. No keys, accounts, paid sources, mirrors, CAPTCHAs, prices, returns or trading data. Any denial stops that route; no retries. Every route listed as stopped in the activation stays stopped.
- **Recording.** Use Discovery Lab templates. Log every effort as it happens, with exactly one `[PILOT:CATEGORY]` tag. Keep the four clocks distinct. Unknowns stay `UNKNOWN`. Never assume identity from a name. Freeze each claim before inspecting any outcome; do not read outcome fields or outcome-bearing snippets before the freeze, and log any such exposure at once as a deviation. You may not record M/H reviews or dispositions.
- **Connection log.** Log every connection, warning or avoided repeat you consider, as you consider it, as a V2 row (`log_version: GRAPH_PILOT_CONNECTION_V2`) in `connections-{ARM}.jsonl`. {ARM_G_ONLY: Save the snapshot-mode `--json` output of every suggesting query to `suggestions-G/NNN-<command>.json` immediately. A graph-originated row keeps `origin_suggestion_id`, `origin_operator`, `origin_bases` and `connection_class` exactly as exported; a warning is logged as `METHODOLOGICAL_WARNING`, never as `CONNECTION`.}
- **Tools.** {TOOLS}. Every query passes `--snapshot docs/strategy/graph_pilot_r4/{PACKET}/snapshot.json --arm {ARM}`; never `--ledgers` or `--known-at`.
- **Close.** Run the validators listed in Stage 3 and commit to your branch. Do not push to `main` or commit anything under `data/raw`. The operator attests STOP. Report only the commit SHA, your start and end times, the account totals and any refusals, stops or violations.
