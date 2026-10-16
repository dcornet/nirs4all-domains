# Frozen structural protocol — domains.structure.v0.1

Declared before implementation, synthetic qualification and real clustering.
Canonical alpha.4 reports and predictive outputs remain separate and unchanged.
Criteria are exploratory operational rules, not a universal taxonomy or risk score.

## Population and frozen settings

Use the existing admissible technical-mean builder: one row per physical sample,
homogeneous contexts, reference guards and explicit exclusions. Train only, sorted
physical IDs. Dependency components retain physical/sample/individual/reference/
group links. Identical acquisition duplication adds no clustering vote.

Reuse Methods PCA: center train, no scaling/whitening, smallest prefix reaching
95% full trace, cap 20. Record fit IDs/X hash, mean/loadings/scores, retained
variance, variance objective reached, provider/ABI and solver limitations.
Public ABI 2.19 HDBSCAN: Euclidean, alpha=1; min_samples counts the point itself.
Native stable MST ties remain order-sensitive; canonical sorting fixes input
order, without claiming intrinsic order invariance. Labels are exchangeable IDs.

Primary: min_cluster_size=8, min_samples=4, EOM, allow_single_cluster=false.
Sensitivity: (5,4,EOM), (12,4,EOM), (8,8,EOM), (8,4,leaf), single cluster false.
No winner selection. 100 seeded ChaCha8 draws: ceil(80% of whole train components)
without replacement, keeping all selected samples and refitting PCA/HDBSCAN.
The same subsets apply to every setting; every setting has its own reference
and full stability experiment. Retain failures without redrawing.

## Comparisons and support

Intersect physical IDs exactly and sort them before public native ARI. Including
noise treats -1 as a category. Excluding noise uses only IDs clustered in both
fits. Each ARI requires >=20 common IDs, >=50% of reference samples, >=2 classes
and a nonsingleton in each partition, plus >=10 common dependency components.
Otherwise report insufficient with exact
IDs/reason. Native undefined ARI is null with a reason, never a favorable default.
Universal noise and trivial clusters cannot establish robust grouping.

Report noise fraction/agreement, cluster counts, memberships, component subsets
and failures for every attempted draw. All-pair co-membership support divides
same-nonnoise-cluster counts by successful draws containing both samples. Missing
pair exposure is unavailable, not zero. Retain exposures, per-sample inclusion,
per-cluster median within-cluster pair support and native summary quantiles.
These are conditional frequencies, not calibrated membership probabilities.

## Classification rules frozen before outcomes

Require >=30 samples, >=20 components, >=20 draws, >=90% successful fits in every
setting. Robust requires >=2 reference clusters, noise <=0.40, >=90% eligible
including-noise ARIs, median ARI >=0.90, nearest-rank p10 ARI >=0.80, p10 noise
agreement >=0.90, every cluster's median pair support >=0.80, and >=10 successful
inclusions per sample. Every setting must pass these gates, and every sensitivity
reference must agree with primary at ARI >=0.80 and noise agreement >=0.90.

Nontrivial partitions with adequate execution/overlap but failing robust gates
are `fragile_structure`. Inadequate execution, degenerate PCA or overlap gives
`insufficient_information`. All-noise alone is insufficient. A limited
`continuum` compatibility label additionally requires one PC reaching 95%, >=50
samples, strictly positive consecutive score gaps with max/median <=3 and
q75/q25 <=1.5 (Methods summaries), and fewer than two clusters in every reference
and successful replicate. It describes approximately regular 1D organization
at examined scales, not proof of the absence of structure. Report all gates.

## Native comparison and test limits

Optional native fit is descriptive only. For equal multiplicity m, freeze
min_cluster_size=m*physical setting and min_samples=1+m*(physical min_samples-1).
This aligns nominal density masses, not exact weighted-HDBSCAN equivalence.
Unequal multiplicities make comparison unavailable. Consensus requires all
acquisitions of a physical sample to share a label, including unanimous noise.
Exclude mixed assignments explicitly; compare common consensus IDs through ARI.
Stability uses physical means exclusively, never independent acquisition votes.

No public held-out HDBSCAN assignment was found in audited headers/catalog/
bindings. Test labels are unavailable; PCA projection is not cluster prediction.
No train+test fit. Native infinite hierarchy lambdas/undefined outlier scores
become JSON null with per-field reasons; no NaN/Inf enters exported JSON.

## Controlled expectations

Separated 3-group clouds: recover known memberships and high stability; label
renaming and canonical input reordering invariant. Unequal density/size: report
recovery and sensitivity without requiring every generating group. Smooth
manifold/diffuse cloud: no robust claim from trivial/noise partitions. Small-N:
explicit insufficient. Instrument-generated structure and X groups independent
of Y: detect X organization without predictive-reliance/causal claims. Rank
deficiency/duplicates: bounded deterministic success or explicit failure, no
jitter/deletion. Additional gates: matched/partial-overlap IDs, whole components,
no retained X/Y dependence, duplicate-repeat vote invariance, real native outputs.

Implementation-review clarification before final qualification: custom cluster
sizes must permit at least two clusters in every reference and resampled population
before the continuum gate can pass. Otherwise all-noise is forced by configuration
and cannot distinguish the competing interpretations. This additional conservative
guard does not change the frozen default grid or any observed default classification;
initial outputs are preserved. A controlled impossible-scale case tests the guard.
