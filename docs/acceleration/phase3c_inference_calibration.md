# Phase 3C: synthetic inference calibration

**BLOCKED.** The predeclared Phase 3B noncircular null-centered bootstrap fails the synthetic size criterion. No real market or strategy returns entered calibration. No method was replaced or tuned to rescue the outcome.

Protocolv 002:200 replications/family,10,000 draws/replication, fixed seed 3003001, two funded windows756 sessions each, primary 252-session blocks, fixed 126/504 sensitivities; pooled-mean centering preserves window contrasts, blocks stay within windows. Null-family acceptance requires Wilson95% upper bound for raw one-sidedalpha0.05 rejection<=0.10. This protocol was privately hashed before execution. Positive/negative cases assess known effects; their rejection rate is not Type-I error. Earlier primary-only prototype receipts remain private and unchanged.

| Synthetic family | Raw null/effect rejection | Wilson 95% | 126 / 504 block rejection | Sample gate pass |
| --- | --- | --- | --- | --- |
| iid_null | 12.5% | 0.086–0.178 | 0.085 / 0.225 | 1.000 |
| positive | 99.0% | 0.964–0.997 | 0.985 / 1.000 | 1.000 |
| negative | 0.0% | 0.000–0.019 | 0.000 / 0.000 | 1.000 |
| ar1 | 15.5% | 0.111–0.212 | 0.110 / 0.300 | 1.000 |
| persistent | 19.5% | 0.146–0.255 | 0.170 / 0.310 | 0.645 |
| annual_shock | 19.5% | 0.146–0.255 | 0.205 / 0.290 | 0.995 |
| overlap | 15.5% | 0.111–0.212 | 0.100 / 0.285 | 0.995 |
| window_shift | 15.0% | 0.107–0.206 | 0.080 / 0.230 | 1.000 |
| heteroskedastic | 17.5% | 0.129–0.234 | 0.130 / 0.315 | 1.000 |

Annual reporting shocks, persistent AR(1),21-day overlapping-like dependence, heteroskedasticity and offsetting window shifts exercise the proposed assumptions. Bartlett HAC lags252/504, effective-size floor20 and six annual-block equivalents are diagnostics, not a power certificate. Four declared effects use conservative missing/failed p=1 and Holm; fully correlated four-effect family rates are retained in canonical evidence, with unknown general joint calibration explicitly unresolved. Unit tests additionally reject zero variance, missing/nonfinite NAV-derived inputs, misaligned/overlapping windows, few blocks and missing family effects.

Code success is not statistical certification. Primary null rejection exceeds the predeclared allowance across several families, including IID; the sample gate/adjustment does not license replacing the primary method with a better-looking block length. Recommend a separately reviewed **pre-performance** inferential revision (for example finite-sample/studentized or longer-window design), with a new fixed synthetic calibration protocol. Do not implement/adopt that alternative automatically. Preserve this negative result and all search accounting; EXP005 cannot freeze under this inference contract.
