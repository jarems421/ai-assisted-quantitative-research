# V003 analytical generator correction 001

The original protocol/code froze at `0a7f790`, and its first complete results remain unchanged in `phase3e_inference_calibration_v003.json` and the private content-hashed archive. No real returns entered this review.

The frozen AR generator used innovation factor sqrt((1−rho)/(1+rho)). For an AR(1), long-run variance is innovation variance/(1−rho)^2. The original factor therefore made the declared 2.5-point annual noise approximately 2.887 points at rho=0.5 and 12.563 points at rho=0.98 in the long-run limit. Finite groups differ further. This was an implementation mismatch with the declared noise scale, not a result warranting a different inference method.

Correction 001 multiplies AR innovations by sqrt(1−rho²), making their total factor exactly 1−rho. The same estimators, three stage candidates, joint structures, effects, noise sensitivity, 600 replications, seed3003004, confidence procedure and fixed gates are retained. IID and all non-AR scenarios use identical random draws and outputs. Zero-effect AR rejection/coverage is invariant to this common scale correction; alternatives/interval widths change as required by the corrected declared noise. No output is removed.

The corrected generator and this receipt are committed before its one rerun. Corrected results get a distinct filename and freeze receipt; original code/results are never overwritten. This is a transparent bug correction, not a new search family, post-result noise choice or weaker statistical threshold. Both runs must be disclosed. Any further scientific revision requires a new reviewed protocol.
