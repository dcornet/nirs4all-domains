# Cartilage original-source admission: identities resolved, donor support pending

The revised [Figshare v2 data](https://doi.org/10.6084/m9.figshare.7803845.v2)
were acquired through Datasets 0.3.11 `retrieve_raw`, under declared CC0 rights.
The 26,657,431-byte MAT matches official MD5
`0c43074bc039fcd93a38999a9af76d26`; SHA-256 is
`5842fcacbdfed21572689a07196ba7c73f3011b3c0c081c5fa70218431285456`.
The Springer supplementary ZIP is metadata, not this original matrix.

Each MAT structure element directly binds `sample_id`, joint, area-of-interest,
measurement point, wavelength, raw spectra and reference fields. The adapter
checks encoded sample keys against all three identity fields. It preserves
**869 locations / 2,605 spectra / 812 channels / 44 joint-scoped regions / five
joints**. Acquisition IDs name original within-location MAT spectrum membership,
without inventing independent specimen identities. Replicates share their location
reference. Region names alone are reused across joints and must be jointly scoped.
The revised file supplies three spectra for 867 locations and two for two
locations; no missing third spectrum is manufactured.

All 869 original location spectral multisets match the derived X exactly after
float32 transport. The comparison joins X observation key → M observation key →
original MAT sample key, then compares within-location spectra independently of
row order. Derived wavelength labels match original values rounded to two decimals;
the full-precision original axis remains the source contract. This is spectral
membership evidence, not proof of target-table equivalence: derived Y has no
observation/location key. Positional X/Y reconstruction is refused. Original MAT
reference ownership supplies a separate keyed reference adapter.

OCT non-calcified thickness has 869 finite values: mean 0.88781 mm, SD 0.23840,
range 0.32–1.81. Optical axial resolution is not an independent assay-error SD.
Logical location/reference keys do not establish original assay events. No donor
field or joint-to-animal map is supplied. Transitive closure of documented region,
joint and reference identities gives five **declared** components; the independent
animal count remains unidentified. Five joints are not asserted to be five donors.

The previous 500-row deep guard is a software/resource boundary. Full-population
float64 means occupy 5,645,024 bytes; all acquisitions occupy 16,922,080 bytes.
A five-outer/three-inner/three-candidate model design would require 50 model fits;
an 869-square dense kernel requires 6,041,288 bytes. These dimension-based costs
do not qualify a complete scalable workflow. A controlled native Ridge gate uses
all 869 × 812 synthetic cells and checks all predictions without truncation; no
Cartilage reference is used in that test. Runtime for a complete real nested
study remains unmeasured, and the old CLI guard is preserved.

Observation: original keyed spectral membership and reference ownership can be
verified, while biological transfer support and derived Y equivalence remain
unresolved. Confidence: high for checked file/key/float32 correspondence, limited
for experimental independence. Consequence: predictive task admission remains
`not_identifiable`; **no Cartilage predictive fit is run**. Action: obtain the
joint-to-animal and assay-event map, publish a corrected keyed Datasets adapter,
then freeze a full-population, group-safe resource-bounded protocol.

Previously weak prediction is retained as an unresolved observation. Mapping,
reference precision/reuse, biological dependence, target range, representation,
split difficulty and model misspecification remain separate hypotheses. Neither
a data error nor weak intrinsic chemical information is inferred from poor scores.
The [paper](https://doi.org/10.1038/s41597-019-0170-y) and
[original example code](https://github.com/uef-bbc/sarin-scientific-data-2019/tree/10e3d789d374f630199199cfc4a0f6954286b02b)
support the structure audit; their ordinary CV example is not a grouped Domains
qualification. See [machine evidence](benchmarks/alpha10/cartilage-admission.json).
