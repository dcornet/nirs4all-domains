# Units, references and representation protocol v0.2

Expected behavior fixed before the alpha.3 scientific tests:

| Controlled situation | Required result |
|---|---|
| Known technical acquisitions of one train sample | Native acquisitions retained; optional homogeneous mean has one physical-sample vote, regardless of repeat count |
| Sample or physical/individual/group dependency spans train and test | Invalid split; no PCA or averaging |
| Reference or reference group spans partitions | X remains analyzable; X-Y is blocked and validation components link both partitions |
| One physical sample on several instruments/campaigns | Separate linked context records; excluded from the pooled equal-physical-sample geometry |
| Biological, unknown or mixed repeat types | No automatic mean; explicit exclusion from the aggregated comparison |
| Contradictory reference values/units, composite or censored references | Native X retained; affected X-Y blocked; contradictory groups never averaged |
| Shuffled Y identifiers, same X/Y sizes | Values follow identifiers; missing or duplicate join keys fail conversion |
| Test X or hidden Y changes | Train PCA and thresholds unchanged; hidden Y changes leave the entire pre-training report unchanged |
| Missing identity/context/reference metadata | Required acquisition/physical IDs fail validation; optional context/reference absence is counted, never inferred |
| Native validation partition | Explicitly excluded before target access; IDs and denominator retained |

An observation is an acquisition. A sample ID is a supplied join key; physical
identity is separately supplied. Source is task-wide. Instrument, campaign, site
and lot are retained as metadata. A repeated group requires known instrument and
campaign, one sample key, and a single declared technical type (rescan,
repositioning or repreparation). Site and lot also separate contexts when supplied.
Missing context is allowed for singleton observations but cannot certify a mean.

`native` preserves the alpha.2 comparison policy: repeated physical units make
geometry not identifiable. `technical_mean` gives each eligible physical sample
one row with weight 1, calculated with the public Methods summary mean. It never
averages across partitions or contexts. Cross-context records are retained in
the representation inventory but excluded from this pooled geometry. This is a
conservative task comparison policy, not a paired multi-instrument protocol.

Dependency components connect declared sample, physical, individual, group,
reference and reference-group keys transitively. These are constraints for a
future grouped validation, not implemented CV folds or an effective-size estimate.
Reference-only links block X-Y evaluation across partitions without blocking X.
Counts distinguish known reference IDs from missing identities; zero known IDs
does not mean zero reference measurements. Shared references are counted once.

Reference values are checked only in allowed partitions. Pre-training never
inspects test values. Missing precision/status/units remains an explicit limit;
no tolerance, unit conversion or censoring model is invented. Exact contradictory
values use exact equality because no laboratory uncertainty is supplied.
Reference anomalies suppress the Preflight target input and X-Y metrics, leaving
its native spectral diagnostics available. Safe train descriptions carry at most
one value per declared reference (physical-sample fallback is only descriptive).

Preflight's published facade contains a private averaging step, but no public
representation result usable to project held-out X. Domains does not copy it.
Methods supplies the numerical mean; Domains owns eligibility, membership,
weighting and train/test projection. See UPSTREAM_DEPENDENCIES.md for the narrow
public seam proposed upstream.
