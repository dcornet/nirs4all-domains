# Alpha.13 stability power and real conditional results

The protocol and quality thresholds were fixed before execution. The identity
design audit and controlled qualification precede the distinct
`domains.stability_power.v0.2` freeze, which precedes every revised real draw.
No predictive outcome selected a source, panel, representation or stopping rule.

## Exposure and controlled qualification

For fixed-size observation sampling, expected joint exposure is
`B*m*(m-1)/(N*(N-1))`. For uniform sampling of m complete components among G,
within-component pairs have inclusion probability `m/G`; pairs in different
components have `m*(m-1)/(G*(G-1))`. Unequal component sizes change the observation
mixture and selected row counts, rather than these per-pair probabilities.
Expectations do not guarantee adequate exposure for every selected pair.

The prespecified identity simulation tests B=20/40/60/80 with 128 designs per
fixture/fraction. **B=60** is the first candidate meeting the observed .95
feasibility target in every intrinsically eligible cell. At B60 the weakest cell
has 126/128 feasible designs. This is a finite simulation result, not a confidence
guarantee. Giant components, too few units, one group and all-noise retain their
intrinsic blockers. Balanced panels protect small fragments; no cluster is
dropped merely to satisfy the pair cap.

Nine deep frozen X mechanisms produce **6,498 unique PCA fits and 12,996 HDBSCAN
attempts**, with zero failed draws. All sixteen original mechanisms remain in the
protected alpha.12 reference evidence. Three perturbation seeds act on each fixed
generated X; they are not three independent generative populations.

| Controlled setting cases | Robust | Fragile | Insufficient |
|---|---:|---:|---:|
| First 20 draws, B60-selected panel | 24 | 35 | 157 |
| Full 60 draws | 46 | 72 | 98 |

The prefix comparison conditions on the same new panel, not the historical
alpha.12 panel. Native reproducibility on a continuous/noise mechanism does not
prove discrete physical populations. Latent-cloud ARI is reported only for
mechanisms with meaningful discrete generating labels; arbitrary index groups
on manifolds/noise/repeated-acquisition examples are not treated as truth.

For the separately defined decision-layer oracle, both B20 and B60 have zero
false robust and false fragile decisions among the tested 12 stable and 12
unstable setting cases. Stable inconclusive cases fall from **12/12 to 0/12**;
all 12 missing-comparison cases stay inconclusive. These settings are dependent,
and these rates do not estimate real NIRS prevalence or predictive fragility.

## Revised real experiment

All twelve source/representation/fraction conditions pass the prospective
planned-exposure check. **720 PCA refits / 1,440 HDBSCAN attempts** retain all
observations and bands, with verified Cartilage acquisitions drawn together.

| Source | Observations / resampling units | Revised robust / fragile / insufficient | All-combination result |
|---|---|---|---|
| Tablets | 310 / 310 observation units | 0 / 8 / 0 | Fragile |
| Cartilage | 2,605 / 869 verified location blocks | 4 / 4 / 0 | Fragile |
| Biotron | 87 / 87 observation units | 2 / 5 / 1 | Insufficient information |

Cartilage's four raw cases are fragile and four SNV cases robust. Its original
raw parameter agreement remains low, so selecting only SNV would hide an
important qualification limitation. Biotron raw/.6/min_cluster_size12 has
52 eligible nontrivial ARIs among 60 successful fits, below the required 90%;
its pair-exposure gate passes. More planned exposures cannot repair degenerate
partition comparisons. Thresholds are unchanged.

For comparison, alpha.12 retains Cartilage's 2 robust / 6 insufficient cases and
Biotron's 2 robust / 2 fragile / 4 insufficient cases, with insufficient overall
results for both. Those files and classifications were not rewritten. Seeds,
draw count and pair design differ, so this is a version comparison rather than
a pure treatment-effect estimate.

These are conditional algorithmic findings. The 869 locations lie in five joints;
donor/assay closure is unresolved. Unknown physical ownership in Biotron/tablets
prevents biological sampling claims. No source passes all combinations, and no
shortcut probability, causal fraction, continuum or safety certificate follows.

See [JSON results](benchmarks/alpha13/real-stability.json),
[CSV settings](benchmarks/alpha13/stability-matrix.csv),
[controlled qualification](benchmarks/alpha13/controlled-qualification.json) and
[figure](benchmarks/alpha13/figures/stability-support.svg).
