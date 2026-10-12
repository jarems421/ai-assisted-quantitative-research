# New experiment specification

Current direction: [governing roadmap](../../docs/acceleration/master_plan.md). Phase 3D adds a separate proof-manifest schema without migrating old freezes. EXP005 remains absent and cannot be created/frozen by compiler demonstrations. Existing sequential stages and owner-only Test/paper confirmations remain binding.

Copy `spec.example.json` or use `python -m src.research propose EXP002` to create a **local DRAFT**. Replace all synthetic/TODO content before audit or freeze. The example and EXP999 test fixture are infrastructure demonstrations, not proposed market strategies.

`spec.schema.json` requires the hypothesis, rationale, directional claim, falsifiers, confounders, point-in-time universe and data availability, explicit benchmarks, complexity/trial ceilings, ordered windows, costs, execution assumptions, parameter grid, frozen selection/eligibility rules, breadth, robustness/stress plans, multiplicity control, approvals, sealed ranges, and model contamination note.

Document the usable timestamp for each signal: SEC Form 4 filing acceptance/publication (not trade date); 13F filing availability (not quarter-end); congressional disclosure publication (not transaction date); earnings release time; fundamentals' original filing/revision availability; economic release vintage; and custom indicators' publication timestamp. Missing evidence must remain `point_in_time_verified: false`, which blocks freeze. A boolean assertion is an audit responsibility, not an automatic proof that a vendor implements point-in-time joins.

Inner Validation stays inside Development. Outer Validation and historical Test cannot overlap Development or each other. Candidate-formation corpus evidence must end by the research cutoff. Historical lockboxes are `workflow_held_out`, while forward paper evidence after freeze is `genuinely_forward_unseen`.

Do not repurpose EXP001 or amend a frozen specification. New hypotheses after out-of-sample feedback require a new experiment ID and a counted trial family.
