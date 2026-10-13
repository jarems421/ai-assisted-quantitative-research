# External integration audit and implemented boundaries

| Repository | Audit SHA | License | Decision / runtime |
| --- | --- | --- | --- |
| [congressional-disclosures](https://github.com/austin-starks/congressional-disclosures/tree/2965e8796bd4cb9423a83b964a1f9dbd076a0ad6) | `2965e8796bd4cb9423a83b964a1f9dbd076a0ad6` | MIT | OPTIONAL_ADAPTER / False |
| [chrono-ta](https://github.com/austin-starks/chrono-ta/tree/39141072e3e262fbe8715675584f7453bd2bdb9a) | `39141072e3e262fbe8715675584f7453bd2bdb9a` | MIT | ADOPTED_SEMANTICS / False |
| [nexustrade-py](https://github.com/austin-starks/nexustrade-py/tree/e13a54517d063a924d5f50374de0a276c7e62007) | `e13a54517d063a924d5f50374de0a276c7e62007` | MIT | EXISTING_DEPENDENCY / True |
| [OpenBB](https://github.com/OpenBB-finance/OpenBB/tree/7c9d4221bdf66965e3f6c7f4dc6ee848073e5ae2) | `7c9d4221bdf66965e3f6c7f4dc6ee848073e5ae2` | Apache-2.0 | ADOPTED_INTERFACE_PATTERN / False |
| [FinRL](https://github.com/AI4Finance-Foundation/FinRL/tree/00f3596facd01cced5217d875d8c1fc413a31665) | `00f3596facd01cced5217d875d8c1fc413a31665` | MIT | DEFERRED_PHASE5 / False |
| [numpy](https://github.com/numpy/numpy/tree/a0e0f603ac3ad50443a6c33b7c39f150574429de) | `a0e0f603ac3ad50443a6c33b7c39f150574429de` | BSD-3-Clause | EXISTING_DEPENDENCY / True |
| [pandas](https://github.com/pandas-dev/pandas/tree/802a5b6c44cfdcf8be4547408412d5605dc0bf9c) | `802a5b6c44cfdcf8be4547408412d5605dc0bf9c` | BSD-3-Clause | REFERENCE_ONLY / False |
| [matplotlib](https://github.com/matplotlib/matplotlib/tree/24b0053e2c4f96ce54037138e79b84cb90f01e17) | `24b0053e2c4f96ce54037138e79b84cb90f01e17` | Matplotlib-license (PSF-based) | EXISTING_DEPENDENCY / True |
| [scikit-learn](https://github.com/scikit-learn/scikit-learn/tree/bebaf70573b6fe756bc93aca5534f3191c18c4eb) | `bebaf70573b6fe756bc93aca5534f3191c18c4eb` | BSD-3-Clause | REFERENCE_ONLY / False |

**congressional-disclosures**: Snapshot hash/schema/as-of adapter; upstream modeled EOD and version availableAt kept distinct. Event consolidation filters resolved members and can augment contributors retrospectively; no primary trust promotion.

**chrono-ta**: Explicit UTC buckets/elapsed expiry/state continuation; clean-room implementation rejects ordering/capacity instead of adaptive thinning. No crate dependency or bit parity claim.

**nexustrade-py**: Installed1.42.0 literal-byte offline prepare_web_pages only; upstream1.55.0 audited, not upgraded. No client/agent/host fetch or statistics-as-inference.

**OpenBB**: Normalize provider results while preserving query/upstream metadata and evidence tier; no full stack or evidence promotion.

**FinRL**: Train/test/env/risk contracts informative but download/reward/portfolio/trading paths outside current scope. README points to FinRL-Trading/FinRL-X; not installed.

**numpy**: Existing direct synthetic inference/proof fingerprint dependency now explicitly pinned2.2.6; no change to installed environment or canonical metrics.

**pandas**: Arrow/DuckDB suffice; DataFrame mutation/coercion cannot supply source vintage. Not added as direct dependency.

**matplotlib**: Keep3.11.2 presentation-only; no canonical performance processor change.

**scikit-learn**: TimeSeriesSplit/evaluation interface examined; no predictive model exists requiring runtime dependency or generic CV replacement of stage controls.

All audit clones/blobs remain ignored. Registry records file/license hashes and exact default branches. Read-only engineering GitHub operations are separate from research-source request budgets. No third-party implementation was vendored; interoperable adapters and temporal primitives are clean-room code. The installed Nexus helper retains its package license and exact1.42.0 version, not upstream HEAD behavior. OpenBB currently declares Apache2.0 at the audited commit; do not infer a historical/current license from old AGPL descriptions. FinRL successor guidance is a reference, not permission to fetch prices or trade.
