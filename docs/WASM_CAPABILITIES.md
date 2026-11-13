# Browser capability boundary

This matrix describes the demo's product surface, not a scientific
qualification grant. “Runnable in browser” means the live WASM path can call a
real Methods provider under fixed scope and budget. It does not mean the
method is validated for every dataset or interpretation. The labels below are
documentation categories; runtime evidence keeps its own status, reason and
value fields.

| Capability | Demo status | Evidence boundary |
|---|---|---|
| Raw-X PCA scores and eigenvalues | `runnable_in_browser` | Methods PCA on the complete imported population, up to 20 resolved components; descriptive and transductive. |
| Raw-X full spectral moments | `runnable_in_browser` | Returned by the live PCA provider; no truncated-PCA substitute is inferred. |
| Raw-space nearest-neighbor support | `runnable_in_browser` | Exact full-reference query, up to 8 neighbors; excludes self or matching declared group. |
| PCA-space nearest-neighbor support | `runnable_in_browser` | Exact full-reference query over resolved PCA scores; same declared-group caveat. |
| Single HDBSCAN density fit | `runnable_in_browser` | One frozen EOM setting (min cluster size 8, min samples 4); labels and strengths are descriptive. |
| D1-D6.1 saved companion reading | `saved_evidence_only` | Read the packaged public tablet report and exact saved companions; no new fit or recomputation. |
| Metadata-factor associations | `requires_metadata` | Live protocol does not pass metadata to the provider. Missing factor evidence stays unavailable. |
| Physical specimen / reference support | `requires_metadata` | Requires verified physical and reference identities; observation IDs and groups do not establish them. |
| Reference-population comparisons | `requires_reference_population` | Requires an explicitly admitted compatible reference population and identity closure. |
| Resampling robustness | `not_qualified` | Requires a scoped protocol, admissible units and new execution; one fit cannot stand in for resampling. |
| SNV paired-representation analysis | `not_qualified` | The owner has an SNV API, but no paired browser protocol is qualified here. This is a protocol gap, not an invented missing Methods capability. |
| Predictive performance, transfer, or causal attribution | `not_qualified` | No target, training/evaluation split, predictive fit, transfer test or causal design is accepted. |

The current native runtime publishes `pca`, `summary`, `nearest_neighbors`
and `hdbscan` provider capabilities. The browser binding calls these public
Methods APIs through the Preflight contract. Capability presence is distinct
from qualification, so unsupported provider calls, budget refusal, numerical
errors, zero variance and malformed responses remain unavailable/error states
with null values and explicit reasons.

An actual absent provider operation is `requires_unsupported_provider`; this
category is never inferred merely because the present demo has not qualified a
protocol. Complete future-population support requires a reference and new evidence.

The live protocol does not perform full D1 parity, D2 validation intent
annotation, D3 predictive comparison, D4 standalone companion validation, D5
utility analysis, D6 verification readiness, or D6.1 decision summary. Those
remain saved-evidence consumers where an exact compatible public companion is
provided; the tablet example packages its D1-D6.1 public reading and shows
unknown physical independence. It is not regenerated from live X. Existing
standalone examples under [`examples/standalone`](examples/standalone/README.md)
retain separate source reports and companions rather than joining by a shared
dataset name.

## Fixed live scope and refusal limits

The [retained-partition safety amendment](WASM_PARTITION_GUARD.md) refuses
IO-declared test/prediction populations before this full-source route. No retained
population is fitted, dropped or relabeled; train-fitted browser support remains
unqualified. Complete unpartitioned sources retain descriptive/transductive scope.

The accepted request is one complete dense X source with unique observation
IDs, unchanged strictly monotonic axis and declared source content hash. It
has no Y, target, split, imputation, aggregation, source fusion, axis transform
or claimed physical independence. Complete unpartitioned source fits are
descriptive/transductive; declared evaluation partitions are refused as described
above. Optional group IDs only
exclude rows from neighbor references; their scientific meaning is unverified.

Limits: 32 MiB serialized request, 2,000 observations, 1,000,000 spectral
cells, and 25,000,000 products per bounded kernel. Work above a limit is
unavailable rather than subsampled. Density uses one fixed setting; there is
no parameter search or resampling fallback. Membership strength is not a
probability, a cluster is not a biological batch, and no cluster is not proof
of low risk. Readiness is declaration-only and never indicates execution.
