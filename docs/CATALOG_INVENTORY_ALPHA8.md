# P0 catalog inventory ? alpha.8

Pinned catalog: `e68d1befb6cb8245799e83d4b4e4c41e66287689`; Datasets API/schema 0.3.11.

| Measure | Count |
|---|---:|
| datasets | 164 |
| declared_targets | 1936 |
| pending_metadata_eligible_P1 | 33 |
| primary_source_numeric_target_templates | 1667 |
| sources | 171 |

42 public / 122 private. The 33 coarse P1 metadata candidates remain unqualified.
1,667 counts primary source ? numeric target templates; representations, split designs,
reference policies and content revisions create additional tasks. Not all targets have
scientific meaning, usable units, completeness or rights for this benchmark.

The JSON records each descriptor digest, revision, source/axis/sample counts, reported
sample repetitions, declared targets, card missingness/units, metadata support, split
semantics, tier/license, raw/content hashes where provided and exact absent/unverified fields.
No X/Y arrays, source acquisition, credentials or PLS execution are used. Card counts
are reported declarations and have not been requalified as Domains independent units.

164 entries have enough declared dimensions for a dense float32 lower bound: 1,651,192,668 bytes across their sources.
This is not a canonical/download forecast: compression, raw archives, axes, metadata,
Y multiplicity and possible origin overlaps are excluded. Actual input sizes remain
unknown until provider manifests or on-demand measured acquisition.

| Largest declared entry | Dense X float32 bytes | Numeric task templates |
|---|---:|---:|
| ossl_kellogg_visnir_soil_all_y | 368,719,376 | 52 |
| ossl_lucas_mir_soil_all_y | 273,350,700 | 52 |
| chembl_ir_raman_multiblock | 204,800,000 | 14 |
| ossl_lucas_visnir_soil_all_y | 172,913,200 | 52 |
| flanagan_api_compounds_raman | 45,995,040 | 0 |
| openspecy_ftir | 39,660,000 | 0 |
| openspecy_raman | 39,660,000 | 0 |
| grapevine_leaftraits_multisensor_nir | 22,943,844 | 120 |
| ecosis_uw_bnl_nasa_hyspiri_airborne_campaign_leaf_and_canopy_s_reflectance_nirs | 20,778,660 | 0 |
| ecosis_fresh_leaf_spectra_to_estimate_leaf_morphology_and_bioc_reflectance_nirs | 20,468,916 | 0 |

Full-bank scenarios must add distinct provider input bytes to fixed tools/builds and
retained per-task evidence, plus maximum concurrent scratch. For all 1,667 primary
templates at an illustrative 0.1?4 MiB/task, retained evidence alone would be about
167?6,668 MiB; this is a conditional capacity scenario, not an admission or cost claim.
Additional splits/representations increase it; most entries are not yet eligible.
Runtime cannot be extrapolated from the small EcoSIS/mixed executions to 50k-row tasks.

Observed overlaps needing explicit keyed provenance review include CORN instruments,
Shootout instruments, CA2023 preparations and named CABO/source variants. Name similarity
does not prove sample equivalence; no cross-dataset source/spectrum deduplication occurs.
See ALPHA8_MULTIDATASET_PROTOCOL.md and audit/alpha8-admission.json for the bounded
real-case screen. Source cards are never silently converted into benchmark contracts.
