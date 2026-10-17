# Alpha.12 cross-dataset results

The [42-entry matrix](benchmarks/alpha12/structural-matrix.json),
[CSV](benchmarks/alpha12/structural-matrix.csv) and
[figure](benchmarks/alpha12/figures/representation-sensitivity.svg) describe source
views. They do not estimate structural prevalence across independent NIRS studies.
Source hashes, catalog versions, axes, identities, status/reasons, providers,
costs and historical split-support links remain attached to each row.

| Descriptor | Raw | SNV | Denominator |
|---|---:|---:|---|
| First-PC variance fraction, median | .6821 | .7410 | 39 source views each |
| Retained PCA variance, median | .999662 | .998666 | 39 each, at most 20 PCs |
| Retained PCA variance, minimum | .902412 | .860757 | 39 each |
| Exact participation-ratio dimension, median | 1.7535 | 1.8066 | 12 each; 27 unavailable each |
| Primary HDBSCAN groups, median (range) | 2 (0–32) | 2 (0–37) | 39 each |
| Primary noise fraction, median | .1102 | .1433 | 39 each |
| Nearest-distance CV, median: query census | .5007 | .4489 | 22 each |
| Nearest-distance CV, median: query sample | .4487 | .3525 | 17 each |

Participation ratio uses exact full moments only. Truncated PCA never substitutes
for the missing squared-eigenvalue sum. High variance concentration and local
density variation support continuous geometry descriptors without asserting a
discrete explanation, qualified continuum taxonomy or nuisance mechanism.

Raw/SNV primary partition ARI has median .2390 among 37 eligible nontrivial
comparisons (39 paired profiles, two ARIs unavailable). Mean k=8 neighbor-set
overlap has source median .3305 across all 39. These changes show representation
sensitivity. They do not show that SNV removes nuisance effects or improves
chemistry or prediction. [Resampling evidence](ALPHA12_STRUCTURAL_STABILITY.md)
supports only four of 56 individual combinations; none meets all combinations.

## Population and metadata denominators

The cohort contains 38 vegetation views, one Cartilage view, two blocked mosquito
entries and one ineligible simulated molecular entry. Family summaries cannot
support comparative prevalence with only one qualified nonvegetation source.
The hierarchy has 42 primary records and 43 declared catalog source blocks;
ChEMBL declares two modalities. Seventy cited-reference groups are bibliographic
provenance, not 70 independently observed studies.

Four entries retain historical physical-ownership admissions; two namespaces
(Cartilage locations and original litter bags) have directly rechecked original
keys here. Unknown overlap is retained for other preparations/revisions/views.
The independent-population/study count and study-level distribution remain
not identifiable. Shared citations or package IDs indicate possible relationships,
not proven shared specimens. Distinct files do not prove independence.

Thirty-seven sources have at least one variable declared metadata factor,
versus 35 in alpha.11. Profile-level records retain missingness, level support,
high-cardinality flags, native ARI including noise and factor–PC1..3 associations.
Only Cartilage joint/bone semantics are independently flagged verified in this
new agreement layer; other factor semantics remain declared or historically
scoped. Observation weighting can overrepresent repeated acquisitions. Low ARI
cannot establish absence of a continuous association. X-only numerical input is
target/metadata-free; this campaign's driver used available declared metadata
for corroboration, not admission based on factor values or Y.

## Same-object paired preparation

Original litter CSV IDs yield 321 matched intact/ground objects from parents
322/321, preserving the unmatched intact `GEN_1_BEPA_7` in its full-source profile.
The new X-only contrast materializes only ID and wavelength fields; target
columns exist in the cached CSV bytes but are excluded from field projection.
Separately fitted descriptive geometries have primary ARI .09585 raw and
−.01407 SNV, and mean k=8 overlap .13980 raw / .24494 SNV. This is same-object
preparation sensitivity, not new-object generalization or a new train-fitted
transfer test. The separately retained alpha.11 support probe keeps its original
training state and post-response explanatory qualification.

## Source admission

Official public EcoSIS metadata now resolves Belgian dunes (ODbL) and Alberta
potted leaves (CC BY-SA); both use existing cached spectra and attributed
nonreconstructive summaries. Their exact package IDs, author attribution,
URLs and metadata hashes are in [input-freeze](benchmarks/alpha12/input-freeze.json).
The initial read-only re-audit's `rights_promoted:false` records that initial
stage; the later freeze records the actual admissions. No spectral acquisition
or raw redistribution occurred. Drydown's earlier PDDL correction stays visible.

Two malaria entries remain unavailable because custom terms are inaccessible.
ChEMBL remains ineligible: simulated MIR/Raman is outside this physical NIRS
cohort and full-population work exceeds the bound. Raman part1 v3 has verified
CC BY 4.0; that does not resolve all metadata/other-modality scopes or make it a
physical NIRS source. These are distinct blockers, retained in the denominator.

The [hypothesis register](ALPHA12_HYPOTHESIS_REGISTER.md) and
[future outcome definitions](ALPHA12_FUTURE_OUTCOME_CONTRACT.md) are frozen
without new supervised responses. EcoSIS, Perten and litter are already explored;
untouched confirmation must separate original studies or verified populations.
