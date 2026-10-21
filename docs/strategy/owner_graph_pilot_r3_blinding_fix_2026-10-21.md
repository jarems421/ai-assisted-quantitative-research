# GRAPH PILOT R3 — FIX BLINDED ADJUDICATION EXPORT BEFORE OWNER REVIEW

I have reviewed the P3 and P4 adjudication sheets.

**Do not unseal the keys, write owner adjudications, make M/H decisions or run the final comparison.**

There is a concrete blinding defect.

The supposedly arm-hidden P3 export contains identifiers including `OBS-G-7`, `REL-G-1` and `CAND-G-1`, and the endpoint text refers to `CAND-G-1`.

These reveal the graph-assisted arm despite the report stating that mechanical scans found no arm leaks.

## Required actions

1. Reproduce the defect directly from the committed `blind.json` files and trace it to the endpoint renderer.
2. Preserve the original sheets, exports, sealed keys and hashes unchanged. Record that the original presentation was compromised.
3. Implement a corrected adjudicator-facing presentation that replaces arm-identifying record IDs and embedded references with stable, opaque aliases.
4. Preserve the actual evidence, meaning, relationships, dates, sources and hashes. Do not fabricate or selectively omit information to improve an arm's apparent results.
5. Keep the existing sealed mapping and original adjudication IDs where possible. If the tooling needs changes, make them explicit, versioned and auditable. Never silently overwrite a sealed artifact.
6. Add recursive tests for nested endpoint IDs, record text, candidate references, campaign IDs, and any other arm-identifying strings.
7. Test for leakage across the full exported JSON and human-readable sheets, not just their top-level keys.
8. Document that the original export was disclosed before the correction. Reformatting it cannot undo an adjudicator's prior exposure to arm labels.
9. Prefer an independent adjudicator who has not seen the original sheets. If the owner proceeds, label the review as potentially unblinded and restrict interpretation accordingly.
10. Separately flag post-2025 evidence and outcome-before-freeze exposure for later M/H review. Do not retroactively change candidate freeze times or dismiss evidence contamination.

Produce corrected review materials and exact instructions for performing the human adjudications.

Do not restart campaigns, alter scientific records, expand acquisition budgets, or merge arm branches.

Run focused tests and relevant regression tests. Commit the tooling correction and document all remaining limitations.

**The goal is an honest, auditable descriptive evaluation—not a claim of successful blinding that the exported records contradict.**
