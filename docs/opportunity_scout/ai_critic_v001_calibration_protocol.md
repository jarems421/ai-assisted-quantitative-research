# AI Critic V001: prospective calibration and autonomy-admission protocol

> **PROPOSED, not registered.**
> - It binds only when the owner adopts it, ideally before the first HOLDOUT workspace is prepared.
> - Every number is a proposed target, not a validated threshold. Nothing here authorises a model call, a human recruitment, spending or AI routing.

It answers one question: when, if ever, may calibrated AI critics replace routine human review of ordinary Scout cards, without removing any consequential owner approval? Implementation: [AI Critic V001](ai_critic_v001.md).

## 1. Ground truth: independent human anchors

**Instrument.** `SCOUT_CRITIC_HUMAN_ANCHOR_V001` (`anchor-packet`, then `evaluate --anchors`). Each labeller answers four questions per card:

- research-worthy (yes/no/unsure);
- fatal defect (yes/no/unsure);
- which hard requirement it violates;
- the preferred disposition.

The packet:

- shows exactly the blinded input a critic saw;
- shows no AI, recommendation or Jev output, no lane, no generator and no archive id;
- has its key seal the hash of every reviewer-facing field;
- accepts `HUMAN` anchors only in real workspaces, and refuses assistant or model names. AI opinions are never relabelled as human.

**Ordering.**

1. Freeze labels before any critic output for those cards is read by the labeller.
2. Commit the private anchor file under `.research/` (never the remote) before importing critic answers.

Ordering is procedural and recorded, not cryptographically enforced.

**Human–human baseline.** Two independent labellers on at least a random 30% of cards, selected by `queue --seed` before labelling. Low human agreement on a context means that context cannot support any automation claim.

**Treatment of unsure and disputed labels.**

- A card's consensus label counts only when every decisive anchor agrees.
- `unsure`-only and `DISPUTED` cards stay outside recall and precision denominators.
- They are always reported (`labels_disputed_or_unsure`). They are never recoded.

## 2. Splits: never tune and evaluate on the same cards

| Split | Use | Rule |
|---|---|---|
| Synthetic benchmark | Regression of software behaviour | Public and author-written; never evidence of model quality |
| `TUNING` workspaces | Iterate critic texts and policy | Any change to a text, schema, policy or model is a **new version** (V002…), never an edit |
| `HOLDOUT` workspace | The only basis for admission | Prepared after the version is frozen, from cards generated after the freeze; never used to change anything |

If a holdout result leads to any change, the holdout is spent: a new version needs a new holdout.

## 3. Metrics (`evaluate`), reported separately per generation context

Contexts are reported separately and never pooled for claims:

- `FORGE`;
- `EVIDENCE_LED` (Radar);
- `OTHER` (Gap, Plain).

| Metric | Definition |
|---|---|
| Research-worthy retained recall | Anchors say research-worthy; recommendation is not `REJECT_RECOMMENDED` |
| Research-worthy advanced recall | Same population; recommendation is `READY_CANDIDATE` or `ESCALATE` |
| False-rejection rate | Research-worthy anchors with `REJECT_RECOMMENDED` |
| Fatal-defect detection | Anchors say fatal; `REJECT_RECOMMENDED`, or `ESCALATE` under a fatal rule (R3) |
| False-acceptance rate | Anchors say not research-worthy or fatal; `READY_CANDIDATE` |
| Alleged-fatal precision | Cards with any critic fatal claim whose decisive anchors say fatal |
| Abstention and escalation | UNKNOWN rate per critic and dimension; `ESCALATE` share; invalid or refused answer rate |
| Inter-critic agreement | Scientific versus economic, per dimension both judged; agreement and Cohen's kappa |
| Human anchor agreement | Recommendation versus the anchors' preferred disposition; human–human agreement and kappa |
| Stability | `NEUTRAL_PADDING` variants keep the recommendation; `CONFIDENT_FRAMING` variants never improve it |
| Diversity retention | Distinct mechanism families and sectors among all, retained and READY/escalated cards |
| Cost and latency | Tokens, cost and latency per attempt; a total with any unknown part is `UNKNOWN`, never a partial sum |
| Useful candidates per effort | READY candidates confirmed research-worthy by anchors, per human labelling hour (`UNKNOWN` when minutes are incomplete) |

Every rate is reported as k/n with a Wilson 95% interval. Recall targets use the exact one-sided Clopper–Pearson 95% lower bound.

## 4. Sample size before any conclusion

Per context, to claim a one-sided 95% lower bound of at least 0.95 (`sample-size`):

| Misses observed | Independently labelled positives needed |
|---|---|
| 0 | 59 |
| 1 | 93 |
| 2 | 124 |

This applies separately to research-worthy cards (retention) and to fatal-defect cards (detection). Below these counts the report says `INSUFFICIENT_SAMPLE` and draws no conclusion. Fatal defects may be rare among real cards. If so, fatal detection can only be established slowly; it is never borrowed from the synthetic benchmark.

**Proposed engineering targets, not calibrated:**

| Target | Bound |
|---|---|
| Research-worthy retention | 95% (lower bound) |
| Fatal-defect detection | 95% (lower bound) |
| False acceptance | 10% (upper bound) |
| Neutral-variant stability | 95% on at least 20 groups |
| Invalid-answer rate | 5% at most |
| Human–human baseline | At least 30 pairs |

## 5. Choosing a Jev role

The five uses are measured on the same blinded cards, with Jev answers frozen before comparison and human anchors as ground truth. AI critics are never the ground truth. Each use has a pre-declared decision statistic:

| Use | Statistic (with interval) | Worth adopting if |
|---|---|---|
| Early atomic screener | Sensitivity and specificity of a Jev problem flag for anchor-fatal or anchor-not-research-worthy cards | Skipping critics on Jev-clear cards loses no anchor-fatal card at the lower bound |
| Disagreement detector | P(anchors disagree with the AI recommendation, given Jev disagrees with a critic) versus the base rate | The lift lower bound exceeds 1 |
| Evidence-overstatement detector | Agreement with PR #21 human labels on `certainty_exceeds_evidence` (that packet, on a subset) | Decisive agreement exceeds the Layer A language flags' agreement |
| Falsifiability and mechanism checker | Agreement with anchors' fatal requirement on falsifiability and coherence | Better than the scientific critic alone on those cards |
| Selective escalation trigger | Anchor-confirmed errors captured per extra human minute when Jev flags trigger review | More errors captured per minute than random audits |

Declare the primary use before the run. Report all five. Jev stays shadow-only until a later version adopts one role by owner decision.

## 6. Human review: from universal to selective

| Phase | Human work | AI authority |
|---|---|---|
| V001 now: offline | Build anchors on synthetic fixtures only | None |
| Calibration (`CALIBRATION_ALL`, the only active queue) | Every card gets independent anchors; recommendations are compared afterwards | None |
| Shadow on new cards | Anchors on a random sample plus all escalations; AI recommendations are logged, not used | None |
| Proposed `AI_ROUTINE_TRIAGE_V002` (after admission) | READY candidates (unchanged human gate), escalations, rejection audits, random audits, consequential approvals | Routine `INCUBATE`/`REVISION_REQUIRED`/`REJECT_RECOMMENDED` dispositions stand without a human reading each card; every card is retained |
| Never automated | READY and handoff approval, Discovery Lab campaigns, acquisition, hosted disclosure, spending, Measurement Gate M and H | Human or owner only |

**Projected workload** comes from the `SELECTIVE_PROPOSED` queue's `projected_human_fraction`. The human items it counts are:

- READY candidates;
- escalations;
- every rejection (100% audit, flagged when support is correlated);
- 20% random audits of incubated and revised cards;
- possible valuable false negatives;
- candidates with significant or unknown research cost.

The queue is reproducible from a frozen recommendation file and a recorded seed. It stays `active: false` until the routing mode is admitted.

## 7. Admission of the future routing mode

`admission` (`SCOUT_CRITIC_AUTONOMY_ADMISSION_V001`) reports `eligible_for_owner_consideration` only when all of these hold:

1. **Evidence.**
   - Real cards with `HUMAN` anchors; never synthetic.
   - Evaluated on a `HOLDOUT` workspace.
   - The benchmark record still reproduces and its REFERENCE profile passes.
2. **Targets met per context.** In both `FORGE` and `EVIDENCE_LED`, the section 4 targets for retention, fatal detection and false acceptance are met at their bounds.
3. **Baselines and quality.**
   - At least 30 human–human pairs.
   - Neutral-variant stability shown on at least 20 groups.
   - Invalid-answer rate within target.

Even then it returns `activated: false`, because V001 contains no routing code. Activation would need all of the following:

- a new version implementing the mode;
- an explicit owner decision naming that version, its evidence and its suspension rule;
- continuing random audits.

Proposed suspension rule: any audit window whose false-rejection lower bound exceeds the target returns the system to `CALIBRATION_ALL`. A model, prompt, schema or reference-set change invalidates admission until a new holdout passes. Floating model aliases are never admitted.

## 8. Monitoring after any admission (design)

| Area | What to track |
|---|---|
| Quality | False-rejection and false-acceptance rates from audits, per context; escalation and abstention drift; human–human agreement on audited cards |
| Robustness | Invalid answers; injection flags; neutral-variant flips; correlated-support rejections |
| Scientific yield | Human READY rate, Discovery Lab acceptance and Measurement Gate outcomes for audited low-ranked cards against READY candidates, so the system can tell whether it filters junk or filters creativity |
