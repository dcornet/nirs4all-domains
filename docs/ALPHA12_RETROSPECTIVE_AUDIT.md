# Read-only diagnosis of alpha.11 X-only evidence

The pinned baseline is e8385bf4aa3125d6f6ffadd5e63d080d14a02b44. This audit
reuses all 37 computed X-only profiles, including the separately corrected PDDL
record. No PCA, clustering or model fit is repeated. Native Methods summary
statistics are applied to existing descriptive quantities only. Exact per-source
values and fixed N strata are in [retrospective.json](benchmarks/alpha12/retrospective.json).

Parameter ARI is defined for 36 profiles: median .85884, q25 .18130, q75 .99776,
range -.15366 to 1. Parameter agreement is not resampling stability. Six of 37
primary partitions exceed 40% noise; one exceeds 80% and is all-noise. Thirty-six
multi-group partitions cannot be interpreted as stable discrete populations.

There is no monotone entry-level increase in typical group counts with N: the
fixed N strata have median counts 2, 3.5, 3, 2 and 2, for respectively 10, 6, 11,
6 and 4 entries. Median groups per 100 observations decline from 1.66 in the
smallest stratum to .080 in the largest. This reflects size-scaled descriptors
and heterogeneous, overlapping sources, not a causal effect of sample count.
Small-source fragmentation must additionally be checked under controlled N
changes. Exact cluster supports and sub-1%-population fragments are retained,
without calling every small cluster an artifact.

The 20-component PCA fraction has median .999655 and minimum .902412; retained
variance alone does not prove nearest-neighbor identity preservation. Existing
raw/PCA distance summaries do not identify omitted-axis discrepancies for the
same neighbor pairs. New matched query/neighbor identities are necessary.
Full moments are unavailable on some sources and cannot be recovered from
the truncated spectrum. Original-unit traces are never pooled across sources.

Axis units, amplitude conventions, identity tiers and declared physical
evidence remain source-specific. Observation identity is not biological
independence. Cartilage locations, crop leaves and litter bags do not establish
donor, plant or tree independence. Source views, preparations and revisions have
documented or unknown overlap; equal sizes or similar names do not establish
paired populations. A provenance hierarchy is required before study-level
aggregation. Fixed scalar thresholds must not turn missing evidence into low
structural susceptibility.

The retrospective product analysis predicts full-axis eligibility 12/37 at
250M products, 14/37 at 500M, 22/37 at 750M and 24/37 at 1B. These are cost
predictions rather than newly executed neighborhoods. The native search keeps
k candidates, while Preflight additionally caps each call at 250M products.
New deterministic query batching can preserve every reference row and satisfy
that public-provider cap; total work remains explicitly bounded and unchanged
in asymptotic complexity.

The original 224 protected artifacts verify exactly. An extended 371-file map
also freezes alpha.11 evidence, audits and release documents. Historical reports
are not updated in place. The two now-accessible EcoSIS source endpoints are
recorded as new alpha.12 evidence, leaving alpha.11's unavailable outcomes intact.
