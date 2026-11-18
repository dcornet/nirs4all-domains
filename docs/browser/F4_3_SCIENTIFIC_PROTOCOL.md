# F4.3 prospective preprocessing-sensitivity protocol

Protocol `domains.browser_preprocessing_sensitivity.v1`, frozen on 2026-11-18
before implementation and comparative fixture execution. Preliminary source
inspection and small exploratory owner-API probes are discovery evidence, not
the prospective qualification below. Methods 1.3.13 / ABI 2.20 owns all kernels;
Preflight 0.1.6 and historical protocols remain unchanged.

## Questions and estimands

Robustness is conditional persistence of a **specified observation**, population,
representation panel and diagnostic. It is not one quality score. Separately
report PCA component/eigenvalue descriptions, original-representation and PCA
neighbor retention, density partitions/noise, component-wise factor associations,
and optional train-reference/test-query diagnostics. Contradictions and missing
results remain visible. Persistence does not establish chemistry, independence,
predictive utility or a causal mechanism; disappearance does not identify noise.

The primary population is every declared train acquisition. Fully unpartitioned
sources may use every acquisition in a separately labelled full-source
descriptive analysis. Mixed assigned/unpartitioned populations and predict
values are refused. Preserve original ordered keys, source/content identities,
axes and every observation. No Y is admitted. M access is an explicit grant for
selected train factors and documentary dependency/exclusion fields only.

## Prospective panel and AOM

Raw is mandatory and first. A versioned, attributed descriptor bank adapts the
ordered AOM compact-no-finite-difference/Gaussian bank and raw/SNV/MSC bases at
`GBeurier/nirs4all-aom@157954dc8c4fbf06e45ed7b421b8a02b007d8331`.
It adds explicitly identified Methods scaling candidates. The balanced starting
panel contains raw, SNV, MSC, linear detrend, SG smoothing, SG first/second
derivatives, Gaussian smoothing, StandardScale, L2 Normalize, and two declared
SNV-then-SG chains. A quadratic detrend and explicit crop are selectable
variants. There is no Cartesian enumeration or outcome-based ranking.

Starting SG parameters are window 11, polynomial order 2, derivative 0/1/2,
delta 1, mirror boundary, cval 0; Gaussian uses sigma 1, order 0, reflect,
cval 0, truncate 4. SNV uses mean/std correction and ddof 0. Detrend uses
polynomial order 1 (optional 2). StandardScale enables mean/std; Normalize
uses its default fitted column-L2 norms from reference rows, replayed on heldout
rows (not a row-wise norm). Every effective parameter is recorded.
The descriptor mapping does not assert equivalence to AOM's numerical operators
or boundary conventions. All numerical calls use the qualified Methods runtime;
the inspected AOM browser's Methods 1.0.18 bundle is not imported.

The panel, diagnostics, parameters, correlation method and factor IDs are fixed
before execution and content-hashed. Editing them creates a new plan/result;
subsequent changes informed by prior results are exploratory revisions, not
independent confirmation. Supervised AOM selection with Y_train is a separate
future protocol with per-target validity/validation; it is not enabled here.

## Fit, axes and two-stage access

Every preprocessing stage uses the public estimator fit/transform lifecycle,
including width-state operators. Fit sees reference X only. Learned MSC,
column means/scales and any other fitted state never see test. Record actual
serialized-state fingerprints, transform inputs/outputs and cleanup. Matrices
and fitted-state bytes stay inside the worker/provider and are not report data.

The first action is reference-only. An optional second test audit requires the
exact frozen reference result and plan/source fingerprints. Reproduce reference
transformations and require their fingerprints to agree before any numerical
test transform. Apply the same exported/restored owner states to test, never a
new test fit. A changed source, axis, order, plan or cache fingerprint cannot
reuse the old result. Test inspection is recorded and may invalidate subsequent
selection claims. No automatic next-stage computation occurs.

Shape-preserving operations preserve the original feature positions. SG delta 1
is an index-coordinate derivative, including on irregular wavelength axes; it
is never labelled a physical wavelength derivative. Crop is only an explicit
half-open original-column interval [start,end), retaining its exact original
axis slice and lineage. No intersection, sorting, interpolation or imputation
is implicit. Resampling/other unqualified operators remain unavailable.

## Reuse and comparison

Each transformed X is an explicitly named **derived spectral source**, with
its own matrix/axis/plan fingerprints and a link to the original source. Existing
F4.0 structure, F4.1 descriptive factors and F4.2 support protocols operate on
that declared derived source. Their inner raw-input label is relative to that
source, not a claim that preprocessing did not occur. Original F4.0/F4.1/F4.2
results are never overwritten, relabelled or used as another representation's fit.

- Reuse the existing fixed structure bundle: preflightPca (up to 20 resolved
  components), k=min(8,n-1) exact neighbors with unchanged declared exclusions,
  and HDBSCAN min_cluster_size=8/min_samples=4/EOM/no-single-cluster on those
  scores. The user explicitly selects this bundle; small/constant/budget/domain
  refusals remain local. Do not retune density settings by representation.
- PCA coordinates are not compared component by component. Signs, rotations,
  ranks and retained spaces may differ. Display per-representation evidence;
  a direct subspace-comparison metric is unavailable without a qualified owner
  API. PCA-neighbor comparisons concern each induced retained geometry only.
- Compare owner-returned neighbor identities on the same ordered population and
  exclusion policy. For each row record shared identity count, each returned
  neighbor count and shared/raw-neighbor count. These are elementary protocol
  counts/ratios, not a new neighbor search/Jaccard kernel. Empty neighborhoods
  have an explicit unavailable fraction. Methods summary describes available
  row fractions, with their denominator and unavailable rows retained. Do not
  compare absolute distances across different representations/scales.
- Methods adjusted Rand index uses only observations assigned in **both** fits;
  retain the joint count, all noise/transition counts and complete populations.
  Owner undefined/trivial cases stay unavailable. Methods cluster Jaccard uses
  original full label vectors, explicitly ignoring negative/unassigned labels;
  retain pairwise intersections/sizes. Do not select a favorable matching or
  replace all-noise/trivial cases by perfect agreement.
- F4.1 associations use the same keyed train factors, missingness rules, units
  and descriptive inference mode for each source's recorded resolved scores.
  Component eta-squared is not a fraction of total spectral variance. Neither
  a changing PC basis nor representation selection establishes an independent
  association. Individual M/color export permissions remain separate.
- Raw exact-duplicate integrity is separate original-source evidence; transformed
  coincidences never establish physical identities. Optional F4.2 monitoring
  retains its indexed-fold and dependence qualifications, independent of PCA
  projection and raw-neighbor support.

## Bounded execution and cache qualification

At most 16 representations and three stages per chain; process sequentially.
Keep the existing 2,000-observation, 1,000,000-cell/input, 32 MiB JSON and
25,000,000-product numerical gates. A conservative aggregate panel cost and
transformed-matrix/state-memory admission precede execution. No subsampling or
unrequested scientific operation is a budget remedy. Every requested entry has
a status/reason, even after a local failure. Worker termination cancels execution;
epoch/content guards reject obsolete results after replacement/reset.

Exact repeated stage/prefix reuse is permitted only for identical owner version,
input matrix/axis, reference keys, operator/parameters and fitted state. It must
match uncached sequential Methods execution under the frozen tolerance. This
is a Domains execution optimization, distinct from AOM's full-chain cache and
from unqualified algebraic shortcuts. Do not claim acceleration without measured
call reduction, fixed-panel end-to-end timing and bounded memory. Disable reuse
when identity/state validation fails; never accept an external stale cache.

## Pre-test expectations and limits

Use deterministic public/synthetic inputs only: constructed offsets, positive
multipliers, slopes/baselines, low/high-frequency disturbances and peaks; crossed
instrument/lot/independent/confounded factors; repeated acquisitions; reference
and principal/residual query shifts; constant/extreme inputs, invalid/irregular
axes, crop, local owner failure, unauthorized Y/test fit, wrong fingerprints,
sign/degenerate PCA and all-noise partitions. Known perturbations validate
software sensitivity, not real-source causal attribution.

Independent small analytical expectations include SNV offset/positive-scale
invariance where defined, population-variance StandardScale with constant-feature
handling and held-out values, polynomial SG interior behavior (boundaries tested
separately), explicit crop coordinates, and ARI label-permutation invariance
only where the owner defines it. Actual native/WASM comparisons retain absolute
and relative tolerance 1e-10; degenerate PCA comparisons use invariant geometry
or explicit unavailable comparisons, never an arbitrary coordinate oracle.

Reports preserve every requested representation, unfavorable/unavailable case,
original numerical evidence, source/axis/fitting lineage and caveat. No universal
calibrability verdict, causal-noise diagnosis, predictive/leakage probability or
best-preprocessing recommendation is produced. Full JSON/HTML/Markdown and
selectable uncapped A4/Letter annexes follow existing report conventions.
