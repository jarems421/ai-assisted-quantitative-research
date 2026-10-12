# SEC decision eligibility v001 — PROPOSED, NOT APPROVED

**No real policy is approved or activated.** Policy hash: `f215bf4bdf0beffbccc94c11ec58724116154f5d74e660cf8d033cf845a0b231`.

09:30 America/New_York on the second exchange session strictly after max(acceptance wall-clock date, official SEC filing date). Calendar: Existing frozen offline NYSE full-day session calendar; metadata only, no market observations. Scope: 2015–2020. Frozen calendar source hash: `865db45d2e13abbb7be1ce4be1cc80818a3c68fd7bcd030ff5fe0c8fbf0b9218`.

Start from the later of the original acceptance wall-clock date and independently recorded official SEC filing date. Skip weekends and full-day exchange holidays, wait through one complete later session, then use the following session’s 09:30 New York open. The open uses seasonal EST/EDT via IANA America/New_York; early closes affect neither the selected open nor the whole-session count. Unsupported dates, incomplete calendars, invalid/ambiguous wall times and contradictory chronology yield BLOCKED, not a guessed date.

| Accession | Official SEC filing date | Illustrative proposed eligibility (UTC) | Activation |
| --- | --- | --- | --- |
| 0000320193-19-000119 | 2019-10-31 | 2019-11-04T14:30:00+00:00 | NOT APPROVED |
| 0000320193-20-000096 | 2020-10-30 | 2020-11-03T14:30:00+00:00 | NOT APPROVED |
| 0001326801-20-000013 | 2020-01-30 | 2020-02-03T14:30:00+00:00 | NOT APPROVED |

Rationale: the SEC’s access guidance describes next-business-day dissemination for some late submissions; the website FAQ explicitly gives no guaranteed posting lag. A full subsequent-session buffer is a conservative modeling choice, not evidence of an exact first-public timestamp or a guaranteed upper bound. The two October dates remain illustrative while UTC acceptance interpretation is unresolved. Documentation reviewed in 2026 is not a contemporaneous dissemination receipt.

[SEC access guidance](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data), [SEC website timing FAQ](https://www.sec.gov/about/webmaster-frequently-asked-questions). Source retrieval dates and byte hashes are in the canonical evidence.

## Conditions for any later activation

- Explicit owner artifact matching policy and interpretation snapshot hashes.
- Certified acceptance conversion and consistent SEC filing date.
- Complete supported session calendar.
- Certified historical class binding for every contributor.
- Explicit acknowledgement of modeled public-availability uncertainty; required source evidence complete and no contradictions; all contributing versions pass.

The implementation has no approval writer or automatic promotion command. A trusted owner receipt must separately bind the exact policy, interpretation snapshot and authority-artifact hash. Synthetic receipts test this contract; they approve no real policy. Every contributor must satisfy certified acceptance, source lineage, declared bound and no contrary public evidence. New sources/restatements receive new snapshots and new approval scope. A later metadata change cannot alter an earlier pinned view.

Observed `public_available_at_utc` remains nullable and unchanged. An approved modeled bound would be a separate field/basis; local 2026 download/ingestion and historical reconstruction are separate clocks. This proposed policy does not certify identity or Nexus execution.
