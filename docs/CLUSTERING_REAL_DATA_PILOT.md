# Structural qualification — alpha.5

Executed on 2026-10-16 with Methods 1.3.6 / ABI 2.19.0. The
[frozen protocol](CLUSTERING_STABILITY_PROTOCOL.md) defines the operational
criteria before real outcomes. Results are in
[audit/structure-alpha5-qualification.json](audit/structure-alpha5-qualification.json).
Full JSON/Markdown, labels, strengths, outliers, hierarchies, fitted states,
component membership and all attempted fits remain under ignored
`results/structure-alpha5-final/`. Initial outputs are preserved separately.

## Design and controlled evidence

Existing admissible means provide one vote per physical sample. PCA centers train
only, without whitening/scaling, retains 95% full trace with cap 20. Primary
HDBSCAN uses min_cluster_size=8, min_samples=4, EOM, single cluster false.
Sensitivities are (5,4,EOM), (12,4,EOM), (8,8,EOM), (8,4,leaf). Each uses 100
paired ceil(80%) whole-component subsets without replacement. PCA refits once
per draw; all settings receive its same scores. No X_test/Y_test or target-driven
cluster selection occurs. Failures are retained without redrawing.

ARI uses exactly intersected physical IDs, including noise and separately
excluding noise. Eligibility requires >=20 common samples, >=50% of reference
samples, >=10 common components and nontrivial partitions. Co-membership support
conditions on joint inclusion. Unknown/trivial ARI is never replaced with 1.

| Controlled input | Result at frozen settings | Scientific evidence |
|---|---|---|
| Three separated clouds, 72 samples / 36 components | robust_structure | Three correct groups, zero noise, every setting's 100 ARIs exactly 1; membership supports 1 |
| Unequal density/size, 76 / 38 | fragile_structure | Primary three groups; larger minimum size yields two groups in 70/100 draws, median ARI 0.853 |
| Smooth one-dimensional manifold, 80 / 40 | fragile_structure | Primary median ARI 0.294; changing cuts/noise do not establish robust discrete groups |
| Diffuse cloud, 80 / 40 | insufficient_information | Noise/unstable or trivial assignments do not yield favorable ARI defaults |
| Too few components, 12 / 6 | insufficient_information | No clustering attempted; explicit population requirement |
| Instrument-generated groups | robust_structure in X | Predictive-reliance/causal evidence remains unavailable |
| Identical rows / zero covariance | insufficient_information | Explicit degenerate PCA; no jitter, deletion or fabricated clusters |
| Groups with independent Y | robust_structure in X | No target association or predictive shortcut claim |

The smooth manifold illustrates why finding clusters once does not prove
discreteness. No real or controlled default result is labeled continuum: the
conservative positive geometric gate is not met across the full experiment.
The continuum category is an operational compatibility rule, not a universally
qualified taxonomy. A separate impossible-scale control prevents manufacturing
continuum evidence by setting cluster sizes too large to permit two clusters.

Native tests additionally cover label permutation, exact/partial matching,
noise masks, zero-information ARI, infinite hierarchy diagnostics, canonical row
order, component transitivity, failed draws, duplicate-repeat vote invariance,
retained X/Y mutation, and unanimous/mixed acquisition consensus. These are
actual native executions; upstream parity suites were inspected, not rerun.

## EcoSIS freeze-dried development population

Reuse the original primary split, [verified source and identity rules](REPEATED_DATA_PILOT.md):
65 eligible physical means, 45 plot/reference dependency components and 2151
bands. Each draw selects 36 whole components. Four PCs retain 97.347519% of full
trace, reaching the requested objective. Original assay precision, biological
independence and replicate subtype remain conditional/unknown.

| HDBSCAN setting | Reference clusters / members | Noise | Draw cluster counts | Eligible ARI incl. / excl. | Median eligible ARI incl. |
|---|---|---:|---|---|---:|
| 8 / 4 / EOM, primary | 0 | 65/65 | 95 zero, 5 two | 0 / 0 | unavailable |
| 5 / 4 / EOM | 3; sizes 5, 7, 10 | 43/65 (66.15%) | 39 zero, 61 two | 61 / 0 | 0.702269 |
| 12 / 4 / EOM | 0 | 65/65 | 100 zero | 0 / 0 | unavailable |
| 8 / 8 / EOM | 0 | 65/65 | 100 zero | 0 / 0 | unavailable |
| 8 / 4 / leaf | 0 | 65/65 | 95 zero, 5 two | 0 / 0 | unavailable |

Every setting completes 100/100 fits, without solver/runtime failures. Noise is
a native result, not a failed fit. The smaller-cluster setting has persistence
0.00421, 0.02153 and 0.03505; median within-reference-cluster co-membership
supports are 0.46338, 0.40909 and 0.40323. These are descriptive persistence/
frequency measures, not probabilities. Its eligible including-noise ARIs range
0.30280–0.93157; the 61-value summary conditions on eligible nontrivial comparisons.
The other 39 draws are not assigned favorable scores. Excluding-noise common
populations never pass the frozen overlap/component gates.

**Classification: insufficient_information.** The primary partition is trivial;
the permissive sensitivity has too much noise and too few eligible stable
comparisons to support robust/fragile inference under the frozen overlap gates.
Four retained PCs and sensitivity-generated cuts do not supply the positive
regular-1D evidence required for continuum. This is not a claim that these leaves
have no structure at any scale, nor a reason to alter settings after inspecting
test data. The existing grouped LMA PLS result remains a separate X–Y result.

The optional native comparison keeps all 390 train acquisitions, four PCs and
97.304310% retained variance. Frozen multiplicity scaling gives min_cluster_size
48, min_samples 19. Native HDBSCAN also returns all noise; all 65 sample consensus
labels are unanimous, with no mixed exclusions. Noise agreement is 1, while ARI
is unavailable because both partitions are trivial. This agreement establishes
no meaningful stable grouping. Native exact full moments remain unavailable,
without blocking scores/clustering. Stability votes still use physical means.

## Shootout transfer check

The existing X1 development population has 155 source-row physical aliases and
155 declared components, conditional on its original identity assumptions.
Historical test/validation partitions are not fitted. Four PCs retain 95.472431%
of full trace; every draw includes 124 components/rows. All five settings complete
100/100 fits without failures.

Primary clustering has sizes 10, 92, 11 and 42 noise rows (27.10%). Replicates
yield 0/2/3/4/5 clusters in 1/64/28/6/1 draws. Including-noise ARI is eligible
in 99 draws: median 0.533087, IQR [0.186307, 0.667827], range [-0.112536, 0.890818].
Excluding-noise ARI is eligible in only 52 draws: median 0.920419. That conditional
high value cannot replace the broader instability. Median noise agreement is
0.862903; median cluster pair supports are 0.85484, 0.76645 and 0.62712.

Sensitivity reference cluster counts are 2, 0, 3 and 4, with noise 3.23%, 100%,
60.65% and 63.87%. **Classification: fragile_structure.** Membership and noise
vary materially with subsampling/settings. No clusters are attributed to an
instrument, chemistry, assay confounding or predictive shortcut. The singleton
native comparison is an identity operation (ARI 1), not independent replication.

## Reproducibility and boundaries

Both real structural reports replay byte-for-byte. All 16 held alpha.4 report,
predictive and train-refit baseline files keep their original hashes. Primary
EcoSIS canonical fitted states and all four coverage scalars are exactly unchanged
in new alpha.5 outputs. No previous report is overwritten. Task/config/provider
hashes, source provenance and exact selected populations are retained.

Reproduce with explicit existing task paths and a new destination:

```powershell
. .\scripts\dev-env.ps1
.venv\Scripts\python.exe scripts/run_structure_pilot.py `
  --binary target/debug/n4domains.exe --methods-library $env:N4DOMAINS_METHODS_LIBRARY `
  --config configs/pilots/structure-v1.json `
  --ecosis-task $ecosisTask --baseline-root $alpha4EcoSISResults `
  --shootout-task $shootoutTask --out results/structure-new-run
```

The frozen tasks come from the alpha.4 preparation in REPEATED_DATA_PILOT.md and
REAL_DATA_PILOT.md. The runner is transport only. Test PCA projection remains
available through the canonical workflow, but held-out HDBSCAN labels and
predictive reliance on discovered groups remain unavailable. Alpha.6 experiments
are specified in STRUCTURAL_SHORTCUT_RISK.md, without changing the existing PLS
engine or claiming causal chemical attribution.
