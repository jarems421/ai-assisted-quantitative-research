# Phase 3D inference redesign and finite-sample power

The revised [protocol](phase3d_inference_protocol_v002.json) and candidate code were frozen at 0c683a1/87593c0 before evaluation. The old protocols/results remain unchanged. This revision starts from 252×mean aligned daily net candidate-minus-momentum return differences. Cross-sectional dependence is aggregated inside the paired portfolio tape; repeated issuers, annual reporting shocks and rebalancing can still produce serial dependence. Monthly paired means model 21-session intervals; two 36-month funded windows avoid crossing funding boundaries. Real unequal-month weights are not implemented or certified by this synthetic comparison.

We retained four one-sided Holm hypotheses at 0.05. Cost/delay effects are robustness claims about one mechanism, but the prior design required formal support for each. Deleting them merely to improve power would weaken that promise. Positivity and the 2-point economic materiality rule remain separate; no outcome is rescued by a one-endpoint hierarchy.

Methods: Bartlett HAC 12 with intercept finite-sample correction and asymptotic normal reference, and within-window circular 12-month studentized bootstrap-t with the same HAC standard error, 1999 draws and seed 3003003. A fixed annual bandwidth reflects filing persistence, not a search-selected interval. Only 36 months/window makes its finite-sample approximation fragile. [Official HAC documentation](https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_hac.html) assumes consecutive equally spaced time periods; [block-bootstrap coverage research](https://arxiv.org/abs/0804.4361) explains why studentization is substantive, not an automatic validity guarantee. The implementation is a small transparent intercept kernel, not a new econometrics framework or an asserted reproduction of every paper method.

| World / independent four-effect family | HAC raw / any Holm rejection / coverage | Bootstrap-t raw / any Holm rejection / coverage |
| --- | --- | --- |
| iid | 13.5% / 16.0% / 87.5% | 15.0% / 18.0% / 85.0% |
| ar05 | 7.0% / 10.0% / 90.5% | 6.0% / 10.0% / 88.5% |
| persistent095 | 8.5% / 16.5% / 86.5% | 9.0% / 13.5% / 85.5% |
| annual_common | 10.0% / 25.5% / 82.5% | 8.0% / 24.0% / 88.0% |
| heteroskedastic | 6.0% / 8.0% / 94.5% | 13.5% / 28.0% / 80.0% |
| skewed | 7.0% / 12.0% / 89.0% | 11.0% / 15.5% / 90.5% |
| heavy_tail | 9.5% / 11.5% / 88.5% | 11.0% / 17.5% / 85.5% |
| overlap | 12.0% / 17.0% / 90.0% | 11.0% / 22.0% / 89.5% |
| rebalance_shock | 7.5% / 12.5% / 90.0% | 8.0% / 16.0% / 88.5% |
| regime_shift | 0.0% / 0.0% / 100.0% | 12.0% / 20.5% / 87.0% |
| positive02 | 11.5% / 23.5% / 88.0% | 10.0% / 23.5% / 84.5% |
| positive05 | 23.5% / 42.0% / 91.5% | 21.5% / 43.0% / 91.5% |
| positive10 | 58.5% / 85.0% / 91.5% | 56.5% / 82.5% / 89.0% |
| positive25 | 99.5% / 100.0% / 90.5% | 98.0% / 100.0% / 88.5% |
| negative10 | 1.0% / 1.0% / 90.0% | 1.0% / 1.0% / 87.0% |

Raw rejection and any-family Holm rejection estimate size/FWER only in null worlds; in positive alternatives they describe rejection power. Coverage targets the known mean in each world. Regime shift is a stress diagnostic, not a common-mean coverage certificate.

| Annual effect (points) | HAC primary Holm power range | Bootstrap-t primary Holm power range |
| --- | --- | --- |
| 2 | 4.5%–4.5% | 5.5%–6.0% |
| 5 | 11.0%–15.0% | 9.5%–15.5% |
| 10 | 36.0%–50.5% | 35.0%–49.5% |
| 25 | 94.5%–99.5% | 89.5%–97.0% |

Power ranges cover all three joint structures, with uncertainty intervals retained in JSON. Both methods failed size, coverage, the +10-point screen and the +2-point materiality gate. No tested effect is a certified detectable-effect threshold because calibration failed. Interval widths and effective-month diagnostics describe these synthetic samples only.

Each world has 200 replications; three joint structures—independent, fully correlated and mixed common shocks—test FWER. Full Wilson intervals, failures, effective-month diagnostics and annual interval widths are in [calibration](phase3d_inference_calibration_v002.json). Known alternatives at 2/5/10/25 annual percentage points report detectable effects under a fixed synthetic daily noise scale 0.01, not estimated real power. Mean-CI coverage and family-power are distinct. Both interval and p-value approximations must pass their fixed gates; no primary/stress failure is omitted.

Old sign designs cannot satisfy Holm: 1/64>0.0125 and 1/4>0.0125. The new HAC reference is continuous; bootstrap minimum p = 1/2000=0.0005, so both can resolve the threshold. [Resolution artifact](phase3d_inference_resolution.json) reports independent power gates and exact source/calendar geometry: 1763 sessions / 84 monthly decision slots in 2015–2021. The six-year confirmation toy has 72 monthly units/1512 daily units; these are counts, not 72 independent observations or a completed future calendar certificate. Eligible certified issuer count remains 0. Existing conditional Development/Validation/Test dates stay unchanged and unactivated.

Candidate decisions: `{'monthly_hac12': {'coverage_gate': False, 'power10_screen': False, 'power_at_materiality': False, 'selected': False, 'size_gate': False, 'statistical_assumptions_real': 'UNESTABLISHED'}, 'monthly_studentized_circular12': {'coverage_gate': False, 'power10_screen': False, 'power_at_materiality': False, 'selected': False, 'size_gate': False, 'statistical_assumptions_real': 'UNESTABLISHED'}}`. No method is selected or certified for real inference. Failure at the materiality floor indicates this noise/dependence scenario is underpowered; it does not estimate real strategy volatility or prove all possible sample designs fail. Another method, horizon, estimand or hierarchy needs a new reviewed pre-performance protocol, not a post-failure parameter tweak. The reusable compiler gate enforces minimum-p and separately supported power before any future research path can compile.
