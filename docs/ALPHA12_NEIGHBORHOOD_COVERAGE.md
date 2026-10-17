# Alpha.12 full-axis neighborhood coverage

There are **22 complete-source censuses and 17 prespecified query samples** among
39 eligible catalog sources, for each of raw and SNV. This extends the alpha.11
12 complete-source cases. Every reference population and wavelength axis is
retained. The other three of 42 entries have rights or modality/cost blockers.
The [matrix](benchmarks/alpha12/structural-matrix.json) and
[coverage table](benchmarks/alpha12/COVERAGE.md) retain exact denominators.

Methods' public Preflight nearest-neighbor provider supplies exact Euclidean
neighbors, excluding each observation's own identity. Query blocks change
transport memory, not the reference population. The upstream C engine retains
k candidates rather than a full distance matrix; exact work still scales with
query count × reference count × bands. Domains does not implement a kNN engine.
The qualified path is exact; no approximate-neighbor quality claim is made.

The frozen limits are 750 million distance products per space and 250 million
per public call. Larger source censuses use up to 128 deterministically sampled
query IDs (seed 12017), each searched against the complete reference population.
These are sampled-query descriptions, never complete-source kNN characterization.
The source-specific query design, call count and product cost are in every profile.
Matrix/PCA admission has separate limits and never silently thins rows.

At k=1,4,8, reports preserve neighbor identity/rank agreement and distance
summaries. Within-source normalization is `distance/sqrt(full covariance trace)`
for that representation. Relative radii are 1e-6, .001, .01, .05, .1, .25 and .5.
They are descriptive scale probes, not physical duplicate thresholds. Original
distances and trace remain available separately, with heterogeneous amplitudes
and units explicitly precluding a universal raw-distance ranking.

Partial-query proximity fractions retain 100 query-bootstrap sensitivity draws.
They do not give biological confidence intervals, a formally calibrated finite-
population interval, or quantile precision. Query-distance quantile uncertainty
is explicitly unavailable. Source-level summaries keep census and query modes
separate; the bank is not a probability sample of independent studies.

Projection/full-axis comparisons use the same queries and native exact neighbors
in each space. Nearest identities can differ, so a projected/full nearest-distance
ratio is not a matched-pair reconstruction error. High retained PCA variance
alone does not guarantee preservation of all local neighborhoods.

## Precise upstream proposals, not upstream changes

1. Methods: expose bounded exact-neighbor query blocks with stable identity tie
   policy, scratch-memory estimate, cancel/resume and operation-cost reporting in
   the public role/ABI. Retain complete references and test against exact small
   analytical cases. Existing blocking reduces memory but cannot remove all-pairs
   runtime complexity.
2. Methods: if an ANN public role is exposed, qualify recall@k, exact-rank changes,
   distance error and proximity-fraction error against exact representative
   sources, with a prespecified accuracy/cost policy. No assertion is made that
   no upstream approximate algorithm exists anywhere; none is qualified here.
3. Methods: a public streamed exact full covariance-squared trace would permit
   participation-ratio dimension without storing dense moments. Keep unavailable
   exact moments separate from useful truncated PCA geometry.
4. Preflight: publish executable intrinsic full-axis support/continuum contracts
   with sampling semantics and source-unit caveats. Domains retains task-relative
   split and later predictive interpretations.

No issue was posted and no upstream repository was modified.
