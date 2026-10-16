# Scientific protocols — domains.canonical.v0.2

This is a descriptive pre-training audit, not a test of predictive degradation or
a calibration model. The independent unit, source axis and partitions are explicit.
All results remain exploratory, including outputs from Preflight alpha.

Dataset conversion protocol `datasets.task.v0.3` can explicitly map native labels
to train, test or exclude. Excluded acquisitions are not analyzed or assigned a
new partition; their native counts and IDs remain in provenance. Unknown labels
are errors. Optional target units pass through to Preflight and post-evaluation
summaries. A requested target absent from canonical data fails conversion.

1. Validate task version, context, IDs, physical dependency split separation and
   budgets. Delegate matrix/axis and transitive physical/individual identities to
   Preflight. Reference-only dependencies and anomalies block X-Y, retaining X.
   Refuse missing partitions rather than manufacture a reference split.
2. Construct a Preflight input with native X, acquisition IDs and train targets.
   Do not expose Y_test to that input. Preserve Preflight's complete report and
   availability states rather than relabel unavailable diagnostics as computed.
3. Require at least three train representation rows, one test row and complete finite
   X. Native geometry requires one acquisition per physical sample. Optional
   `technical_mean` uses Methods summary means under the strict eligibility and
   exclusion rules in [UNITS_REFERENCES.md](UNITS_REFERENCES.md). Publish native,
   homogeneous-context and linked cross-context membership, known references,
   dependency components and the exact coverage population. No implicit imputation
   or averaging across contexts. Report observations, physical samples and groups;
   `n_effective=null` because no effective-size estimator is calculated.
4. Call Methods for centered train PCA with up to min(p, n_train-1, configured cap)
   components; default maximum 20, allowed maximum 50. Retain the smallest prefix
   reaching the configured fraction of **full** trace. If the cap does not reach
   it, record `requested_variance_reached=false`. No whitening or autoscaling.
5. Apply the train mean/loadings to train and test. Keep squared reconstruction
   errors so a shift orthogonal to retained PCs is observable. Full covariance
   moments yield participation ratio trace²/trace(C²), not a truncated estimate.
6. Use Methods neighbors with entire independent groups excluded. Train-to-train
   nearest distances define reference coverage; test-to-train uses that same
   reference. Report both arrays with observation IDs. No admissible neighbor
   yields `insufficient_data`.
7. Upper fences use train q75 + 1.5 IQR via Methods summaries. The reconstruction
   fence adds 1e-12*(1 + squared train-mean norm + full trace) for numerical
   roundoff. Coverage flags test observations exceeding either fence. These are
   scale-dependent **heuristics**, not hypothesis tests, prediction intervals or
   support estimators. An observation can be inside these fences and still be
   poorly supported. No inferred core/boundary class is advertised.
8. Report Euclidean centroid distance and ratio of summed retained-score sample
   variances (test/train). Fewer than two test rows makes dispersion insufficient.
   Scores share the train-fitted coordinate system. No covariance-shape or robust
   Mahalanobis diagnostic is claimed.

Methods automatically selects compact, Gram or deterministic approximate SVD
depending on matrix shape and requested truncation (`pca_helper.c`, `svd.c`). The
ABI does not return the selected solver. The fitted record therefore marks this
automatic selection explicitly; only the small analytical fixtures were locally
qualified. Full covariance moments remain exact. The task seed is retained for
future stochastic protocols; it does not control this seedless PCA ABI.

PCA/summary/neighbors are upstream calculations. Applying fitted loadings,
assembling train-reference thresholds and comparing domain summaries are local
task protocols, not an alternative generic numerical library.

Pre-training ignores Y_test in numerical selection, thresholds, recommendations,
Preflight inputs and the sanitized task fingerprint. The Python public `y()`
accessor may materialize all sample rows in memory; conversion reads target cells
only for permitted partitions. Stronger storage-level isolation needs a Datasets
partition-aware target accessor. This distinction is recorded in provenance.

Post-evaluation sets `test_target_accessed=true` when the optional target audit is
attempted, even if no test values are available. It summarizes numeric targets or
categorical counts. Repeated acquisitions sharing a known reference contribute
one outcome; ambiguous repeated outcomes without reference IDs remain not
identifiable. Reference contradictions, sharing across physical objects/partitions,
nonexact status and unit anomalies block X-Y. Only allowed values are inspected.
Any strategy change afterwards
requires another independent evaluation. No concept-shift conclusion follows
from a target summary alone.

The synthetic reference expectations were fixed before running the tests:

| Scenario | Expected behavior now |
|---|---|
| Identical empirical train/test X | Center distance 0, dispersion ratio 1, outside fraction 0; exact duplicates still reported, as they should be |
| Known translation along signal | Large center displacement; all deliberately distant test rows outside; train state unchanged |
| Variance multiplied by 4 | Dispersion ratio 4 in common coordinates |
| Test far outside train | Outside fraction 1, affected observation IDs retained |
| Orthogonal translation | Reconstruction residual flags shift missed by a retained-score-only audit |
| Two separated groups / continuum | Geometry computed, clustering explicitly unavailable; no invented cluster count |
| Instrument perfectly confounded with Y | Conditional attribution explicitly unavailable, no causal claim |
| Technical repeats | Native measurement delegated; optional qualified mean has one physical-sample vote and explicit membership/exclusions |
| Cross-partition exact spectra | Preflight reports 8 cross-physical pairs; no automatic deletion |
| Y independent / strongly predictable | Nested probe unavailable for both; no train-performance calibrability estimate |
| Target shift without X shift | Pre-training report invariant; post audit declares access and shifted Y summary |
| Insufficient rows / target absent | Explicit insufficient_data / unavailable rather than a numeric default |
| Missing X | No implicit imputation; geometry unavailable |

Leakage tests also alter all Y_test values/categories, move X_test far away,
reverse row order, share physical/individual/reference/group IDs across
partitions and omit partition fields. Nested folds are **not implemented**, so
the MVP cannot claim tested leakage-safe OOF model selection. Fixtures for those
future capabilities assert unavailability and keep that qualification gate open.

The schema is structural; semantic invariants are additionally enforced by Rust
validation and `scripts/check_report.py`. Noncomputed metrics require null value
and a reason. Confidence is a qualitative evidence label, not a probability.
Scientific coverage findings remain low-confidence until calibrated against a
broader corpus. No global score or automatic sample exclusion is produced.
