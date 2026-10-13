# Item 2.02 freeze closure: availability stop

**AVAILABILITY_BLOCKED. EXP006 was not created or frozen; Development did not run.** As of 2026-10-13, starting from `8e8ad0c7f676d916832bfaae4e0fb1ff17adf492`. The [owner instruction](owner_item202_closure_2026-10-13.md), sections 3 and 24, requires stopping when the filing-date-only availability semantic cannot be supported. This is a scientific timing stop, not economic falsification or a new architecture phase.

The owner approved one Item 2.02 predictive feature, Development 2015-01-01–2020-12-31, unopened historical confirmation 2021-01-01–2026-09-30, a 20-session horizon, 10 bps per side, future doubled-cost/+1-session robustness, a 12-evaluation ceiling, estimated paired net mean at least 0.50 percentage point and a positive two-sided 95% lower endpoint against zero. These approvals are retained in the [closure receipt](exp006_closure_receipt.json). They were not rescinded or tuned; performance authorization remains conditional on a scientifically certified freeze.

## The exact rule and documented exception

Owner-approved conditional rule: **first regular NYSE open strictly after the SEC filing-date calendar date; never execute on that date**. It is modeled conservative eligibility, not observed first-public time. [Availability contract](exp006_availability_contract.json): OWNER_APPROVED_CONDITIONAL; NOT_ACTIVATED; source-semantic gate FAILED.

The SEC's [filing-date adjustment guidance](https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/request-filing-date-adjustment) permits moving the official date back to an earlier attempted transmission while leaving acceptance time unchanged. The [2006 regulatory overview](https://www.sec.gov/info/edgar/regoverview.htm), section B.5 and Common Filing Concerns, already describes Rule 13 adjustments for technical delays and Exchange Act reports. The newer guidance is not assumed to be a contemporaneous Development receipt; the earlier document establishes that this exception mechanism predates Development. Both current response bodies were archived unchanged with hashes, retrieval times and source locators. No observed adjusted 8-K count is claimed.

Consequently, the required universal chronology implication is unsupported: an adjusted official filing date may precede successful acceptance. A next open calculated from that date alone can then precede acceptance. The documentation does not quantify how often this occurs in the proposed census or establish any accession's exact first-public time.

Synthetic counterexample only: filing date Monday 2015-01-05; delayed acceptance Wednesday 2015-01-07 at 16:00 UTC; the date-only rule gives Tuesday 2015-01-06 at 14:30 UTC. The proposed execution would precede acceptance. This illustrates the permitted mechanism; it is not a fabricated real filing. Calendar tests also cover weekends, holidays, DST, strict date exclusion and insufficient coverage. No production eligibility view exists.

No replacement rule, acceptance maximum, extra waiting period or adjusted-filing exclusion was silently adopted. Old v002/v003 approvals, scopes and inactive states remain unchanged. Economic event date, filing date, acceptance, modeled eligibility and retrieval remain distinct; observed public availability is UNKNOWN. A separately reviewed source-chronology remedy would be needed to change this failed contract.

## Scope retained at the upstream stop

| Required output | Disposition |
| --- | --- |
| Full 2015–2020 census; 8-K / 8-K/A / CIK / Item 2.02 / unknown counts | NOT_ACQUIRED; counts unavailable, not zero |
| Existing Q1 2020 prototype | Unchanged: 17,631 8-K; 493 8-K/A; 5,519 filer CIKs; twelve sampled originals, three Item 2.02 declarations; no full-population label count |
| Identity mapped/unresolved/ended classes and terminal resolution | DEFERRED_AVAILABILITY_STOP; counts unknown, no survivor filtering or terminal exclusion |
| Market provider/API, coverage and corporate-action certificate | NOT_TESTED; no provider or price request; previous bounded QA is not promoted |
| Benchmark matching rule/rate | NOT_FROZEN_NOT_MEASURED; industry/size/momentum/calendar concepts retained |
| Inference methods/calibration/power/effective geometry | NOT_RUN; no method selected and no synthetic success claimed |
| Scientific Proof v2 / canonical EXP006 specification / freeze commit | NOT_RUN / ABSENT / NONE; old design-only compilation remains historical |
| Performance trials / historical confirmation accesses | 0 / 0; ceiling remains 12 |

Two new SEC documentation starts, two HTTP 200 responses, zero retries; no new filing source, identity or market requests. One browser discovery call containing two documentation queries is separately recorded; its underlying fetch count is unavailable. Git/push/hosted-CI operations are engineering delivery, not scientific source calls. No purchase or upgrade occurred; account-wide debit remains unknown. Original response bytes and contact-redacted receipts stay ignored. Local import-path/configuration and editing failures occurred before any request reservation, are retained in the setup log, and consumed no source starts or performance trials.

## Reproduction, preservation and stop

Validation: 338 local tests; 110 public tests; zero skipped. [Validation receipt](exp006_closure_validation.json). Public regeneration/check reads tracked receipts only; private audit verifies the two archived bodies without requests:

```sh
python -m src.research.item202_closure --check
python -m src.research.item202_closure --audit --check
python -m src.research.public_checks
python -m unittest discover -s tests -v
```

Prior source/controller/Proof/execution code, integration reports/candidate, original archives, dependency pins, frozen experiments, processed metrics and pause state remain unchanged. Public tests use synthetic fixtures with private reads and external network blocked. Unrelated local files remain untouched. EXP004 stays paused; EXP005 abandoned/absent. No EXP006 directory/state/job/trial, post-event return, confirmation opening, Nexus/Aurora, graph, optimizer or paper/live action occurred.

**Stopped under owner sections 3 and 24.** The next substantive decision is whether to commission a separately bounded review of an acceptance/public-availability-aware source chronology contract for this same candidate. Nothing downstream runs automatically, and the already adopted feature/horizon/cost/materiality parameters do not need renewed approval merely because this gate failed.
