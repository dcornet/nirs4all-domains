# Alpha.13 — domains.stability_power.v0.1

Prospective calibration protocol, separate from the frozen alpha.12 protocol.
No alpha.12 classifications, thresholds, generators, hypotheses or results change.
Read the resource plan; numerical/resampling stages require their budget admission.

## Analytical design and oracle expectations

Uniform fixed-size sampling without replacement selects m of G whole components
independently in each draw, with m=ceil(fraction*G). For two observations in the
same component, joint inclusion is m/G; in distinct components it is
m(m-1)/(G(G-1)). Multiply by B for expected joint exposure. The latter becomes
the alpha.12 formula only for singleton observation components. Unequal component
sizes change selected observation counts and the mixture of within-component
pairs, not these per-pair probabilities. Report row-support eligibility separately.
Exact small design enumeration validates these rational expressions. Missing or
degenerate fits can reduce effective exposure; their mechanism is not assumed
ignorable. An unconditional expectation cannot certify every pair's support.

Methods 1.3.6 exposes summary/ARI kernels but no qualified public binomial-tail
or hypergeometric-distribution role was found in its audited public headers and
catalog. Domains will not add a general probability/CDF library or numerical
fallback. Use exact finite identity enumeration for small fixtures and prespecified
identity-only design simulation for realistic sizes, with native summaries of
observed exposure/support. Simulation rates are conditional on those designs,
not biological probabilities or real-bank prevalence. No fabricated tail interval.

Separate two calibration truths. Perfectly preserved oracle partitions and
deliberately permuted draw assignments define operational stable/unstable controls
for the decision layer; native ARI still supplies comparisons. Measure false
robust, false fragile and inconclusive decisions against these declared truths.
Known latent clouds give a separate partition-recovery comparison. Native
HDBSCAN reproducibility on a continuous/noise X generator is not automatically a
false robust decision: reproducibility does not imply discrete biological groups.

## Panels, support and revised design selection

Compare the unchanged alpha.12 proportional bounded panel to a prospective
balanced, exposure-aware panel. Allocate up to 32 distinct within-reference pairs
per nonnoise reference cluster, or every pair of a smaller cluster. Between
clusters allocate up to eight pairs for each of at most 64 hash-selected cluster
pairs. Cap the combined panel at 4096 pairs; if all reference clusters cannot
receive their allocation, return insufficient information without dropping groups.
Candidate sampling uses observation IDs and frozen seeds, not draw fit labels.

For each cluster, inspect a deterministic bounded uniform candidate pool (all
pairs for at most 64 members, otherwise up to 4096 distinct pairs). Exposure is
computed from the planned whole-component subsets before any resampled fit.
At least 95% of these candidates must have ten planned joint exposures, at least
ten pairs must be available per reference cluster, and at least 90% of planned
draws must satisfy the existing shared-row support. Select panel pairs among
adequately exposed candidates by a prespecified hash order. Retain rejected
candidate counts, complete population/cluster sizes and selection conditioning;
panel support is conditional, not an unbiased all-pair census or interval.

Identity-only simulation compares B=20,40,60,80 at fractions .6/.8, with 128
independent declared perturbation seeds on prespecified singleton, unequal-
component, small-fragment and repeated-acquisition fixtures. Prefer the smallest
B whose full feasibility rate is at least .95 for every scientifically eligible
fixture. Report exact simulation denominators and native Monte Carlo summaries;
.95 is an operational calibration target, not a confidence guarantee. Intrinsically
ineligible designs (too few units, excessive shared-row failures, one/no groups)
remain explicit and cannot determine a favorable draw-count choice. No selection
using Y, prediction error or real-data resampling outcomes.

After calibration freeze a distinct `domains.stability_power.v0.2` revised-design
contract, its source hashes and draw count before new real resampling. If no
candidate qualifies, retain the failure rather than relaxing quality thresholds.
Real tasks receive an exact planned-exposure feasibility check before fitting.

Quality thresholds remain alpha.12's: N>=30, G>=20, >=90% completed/eligible ARIs,
median ARI>=.9, nearest-rank p10>=.8, noise-agreement p10>=.9, reference noise<=.4,
at least two groups, ten adequately exposed pairs per cluster and median
within-cluster co-membership>=.8. All-noise has no eligible partition ARI and
cannot become robust or safe. All-combination support still requires both
representations, both fractions/settings and parameter ARI>=.8. New design
feasibility strengthens support; it does not weaken scientific quality gates.

## Controlled X qualification

Reuse all 16 alpha.12 generators unchanged for reference geometry. Deep native
resampling is bounded to nine mechanisms: separated, thin_manifold, overlapping,
density_imbalance, satellites, high_dimensional_noise, snv_erased, snv_enhanced,
known_acquisitions. These cover separation/continuum/overlap, small fragments,
heterogeneous density, normalization effects and verified repeats. Use the
original N=120 and fixed X-generator seed; three perturbation seeds are repeated
designs on the same X, not three independent simulated populations. Fractions
.6/.8 and raw/SNV are fixed. Prefixes of the selected B compare the old 20-draw
support without duplicate fitting. No fit on a retained real test population.

The 16-mechanism reference pass can reuse exact matching prior compact results
where sufficient; a fresh reference needed for labels is explicitly counted.
Report raw/SNV group/noise changes, latent recovery only where meaningful,
conditional decision rates and irreducible ambiguity. Reproducibly fragmented
partitions retain their cluster/support distribution; no physical meaning follows.
Continuum certification stays unavailable without its own qualified protocol.

## Bounded real study and execution

After analytical/synthetic qualification, select three populations by X/identity
diversity only: Biotron's small observation-conditional population, Cartilage's
verified whole-location components, and one independent new material source.
Priority for the latter is original UCPH tablets, then original OHPL/Abisko soil,
then original beer, conditional on rights/identity/modality/cost admission. If none
is admitted, keep that slot unavailable rather than choose using Y/performance.
Freeze exact sources, content, IDs, components, references, panel and schedules
before their new resampling. No biological uncertainty from unknown identities;
Cartilage remains conditional on locations/joints, without donor/assay closure.

All numeric PCA/HDBSCAN/ARI/SNV/summary calculations reuse native Methods and
Preflight. Domains owns task-specific rational inclusion formulas, finite
identity counts, panel allocation, scopes and decisions. Use serial StageStore,
compact checksummed draw prefixes and atomic outputs. Never store X or PCA
scores per draw. Missing/failed/ineffective fits remain in their denominator.
Source/provider/controller/seed changes invalidate restart; corruption refuses
reuse. Native replay is exact on the same platform/provider; analytical native
scalars use abs1e-10, rational inclusion/enumeration and identity/hash joins exact.
