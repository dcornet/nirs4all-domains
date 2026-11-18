# F4.2 remaining capabilities

F4.2 adds a train-fitted descriptive projection and a separate indexed-fold PCA monitor. The local and hosted qualification records are in [F4_2_VALIDATION.md](F4_2_VALIDATION.md) and [F4_2_NATIVE_WASM_PARITY.md](F4_2_NATIVE_WASM_PARITY.md). Scientific, report-contract and browser workflows succeeded on executable SHA `4b9ee761e32e798fd8b4466b420a4ce479e561ab` on Windows/Ubuntu. The subsequent documentation synchronization must be checked separately; sampled PDF visual review and incomplete accessibility rules do not establish full certification.

## Supported boundary

- FlexiblePCA fits declared train X and transforms train/test X with the same actual Methods handle. Test values cannot affect the fit state. This is not prediction or model evaluation.
- `statsPcaMonitor` is a separate actual Methods call with its own status and reason. A monitor failure does not erase a valid projection.
- Existing F4.0 raw-space neighbor evidence and F4.1 source-score provenance remain separate. F4.2 does not reuse the F4.1 PCA basis or regenerate its scores.
- Y and predict rows are excluded from the scientific request. Original keys, order, axes and declared identity fields remain bound to the result.
- Fractions/counts of query threshold exceedances are descriptive counts per query acquisition; they are not probabilities of predictive failure or independent-unit coverage.

## Not qualified or not implemented

| Capability | Current boundary |
|---|---|
| FlexiblePCA eigenvalues, variance ratios and numerical rank | Not published in the public fitted state; reported unavailable with reasons. Summaries of returned scores do not resolve full-spectrum variance or rank. |
| Shared F4.1 PCA fit | Not reused. Train-fitted F4.2 projection has an independent fit identity and state receipt. |
| Empirical monitoring-limit qualification | Unknown/not qualified absent an admissible external record about independent units and the indexed-fold design. Unique row IDs or a negative duplicate audit do not establish physical/reference independence. A zero-component reference remains not qualified. |
| Physical or reference independence | Not inferred from technical keys, unique declared IDs, or context metadata. Preserve repeated/shared identity evidence. |
| Prediction, target scoring, transfer or causal inference | Not implemented; neither Y nor predict query values enter this protocol. |
| Real-study utility or deployment claims | Not established by deterministic synthetic fixtures or browser demonstrations. |
| Automatic repair of invalid monitor parameters | Not supported. Invalid fold/alpha values and owner refusals remain local to monitoring; no silent substitution or selection from test output. |
| GUI external-limit qualification | Not exposed. The external plan remains an advanced API capability and validation of its shape does not verify its source or scientific truth. The normal GUI remains descriptive. |
| Browser/platform/PDF qualification scope | Windows/Ubuntu scientific, report and Chromium/Firefox CI succeeded on executable SHA `4b9ee761…`; 97 browser checks per OS. A4/Letter all-page structural checks passed; visual inspection was sampled, automated accessibility checks had incomplete rules, and no WCAG, tagged-PDF, screen-reader or real-study utility certification is claimed. |
| Upstream Methods/Preflight changes | None proposed as implemented work. Numerical kernels remain in the two existing crates; Python is transport/batch only. |

No displayed distance, threshold count, exceedance fraction or monitor output is a leakage probability, non-calibrability score, predictive failure probability, or generalization certificate. See [F4.2 scientific protocol](F4_2_SCIENTIFIC_PROTOCOL.md) for estimands, budgets, access contract and tolerance policy.
