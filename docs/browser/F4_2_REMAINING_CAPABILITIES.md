# F4.2 remaining capabilities

F4.2 adds a train-fitted descriptive projection and a separate indexed-fold PCA monitor. Local compiled native/WASM and focused Chromium checks are recorded in [F4_2_VALIDATION.md](F4_2_VALIDATION.md) and [F4_2_NATIVE_WASM_PARITY.md](F4_2_NATIVE_WASM_PARITY.md). Hosted CI, final-head reruns and PDF review are still pending; local evidence must not be presented as those closures.

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
| Complete browser/platform/PDF qualification | Local Chromium focused checks passed. Firefox, hosted Windows/Ubuntu, exact delivery-head full gates and selected A4/Letter PDF structural/human review remain pending. |
| Upstream Methods/Preflight changes | None proposed as implemented work. Numerical kernels remain in the two existing crates; Python is transport/batch only. |

No displayed distance, threshold count, exceedance fraction or monitor output is a leakage probability, non-calibrability score, predictive failure probability, or generalization certificate. See [F4.2 scientific protocol](F4_2_SCIENTIFIC_PROTOCOL.md) for estimands, budgets, access contract and tolerance policy.
