# Source admissions and source-population overlap

Selection preceded new predictive scores. The existing 164-entry inventory was
recounted from Datasets e68d1bef: **42 public entries**. These are catalog views,
not 42 independent studies. [Machine source review](benchmarks/alpha11/source-review.json)
and [coverage](benchmarks/alpha11/COVERAGE.md) retain every entry and blocker.

| Candidate | Original provenance and material | Decision |
|---|---|---|
| Cedar Creek/Minneapolis litter | Kothari, Hobbie and Cavender-Bares; [original data](https://doi.org/10.5061/dryad.hdr7sqvrk), EcoSIS cc-by. Senesced material, intact and ground preparation | New conditional grouped task and paired preparation challenge; 322 intact, 321 ground, 2001 channels |
| Brookhaven eight-crop leaves | Ely et al.; [paper](https://doi.org/10.1093/jxb/erz061), EcoSIS ODC-By. Different study, source population and nitrogen target from CA2023 | Original-keyed descriptive XY admitted; leaf-to-plant/assay ownership blocks models |
| Garrett soil | [Original Figshare v2](https://doi.org/10.6084/m9.figshare.20506587.v2), CC BY 4.0, forest trial soil profiles | Pending: original MIR versus catalog VISNIR correspondence needs exact OSSL/sample/archive evidence |
| Cartilage | Original revised CC0 MAT, already verified in alpha.10 | X-only and joint-label agreement now computed; donor/assay map still blocks predictive admission |
| CORN / Shootout / UCPH | Original-source blockers preserved | No new fitting or assumed permission; owner explicitly keeps CORN pending |

The litter [publication](https://shankothari.github.io/Documents/Kotharietal2024CJFR.pdf)
identifies 2018 collection, composite tissue samples, dry-combustion nitrogen on
oven-dried material, and omission of one birch sample from ground measurements
because tissue was insufficient. The original missing key is `GEN_1_BEPA_7`.
Publication year 2024 is not silently used as collection year. Repeated material
from one trap, tree or plot is not an independent biological replication.

Original `ID = plot_individual_species_number` joins both litter preparations;
the target is in the same keyed original row. Thirty-one declared plot/context
blocks include one conservative GEN block and one MPLS block. GEN collection
origin and shared assay batches remain unidentified. Physical sample keys are
verified; a count of independent biological populations is unavailable.

For crops, 184 original spectral leaf IDs join 187 original trait rows by
`sample_id`, with exact keyed float32 X parity. Three trait-only keys and one
missing nitrogen outcome are explicit. The 183 finite pairs support descriptive
association. They are not 183 verified independent plants. No model is fitted.

Known overlap prevents inflated coverage: CA2023 preparations, CABO revisions
and absorbance/transmittance, herbarium preparations, Alberta leaf/canopy and
NASA/Puerto Rico modalities can share populations. The Dryad litter mirror and
EcoSIS resource describe the same study. Different targets, preparation, source
package or DOI do not establish scientific independence.

Five public X0 stages remain unavailable: two EcoSIS original metadata endpoints
return HTTP 403; malaria's two entries point to inaccessible custom reuse terms;
ChEMBL combines unresolved metadata ShareAlike scope with dimensions beyond the
complete-population budget. Its simulated molecular IR/Raman is not a new physical
NIRS population. PDDL drydown rights were separately audited after the first
pass omitted that license; the original first-pass record is preserved.

Prepared requests, not sent:

- Cartilage: `sample_id -> donor_id, joint_id, region_id, assay_event_id,
  assay_batch_id`, reference precision, and a keyed full-axis Datasets adapter.
- CORN: original physical/reference keys across m5/mp5/mp6 and propvals, plus
  permitted analysis and statistics-publication scope; no re-request to the owner.
- Shootout: reconcile original 655 with announced 654 and supply original
  physical/assay/partition maps across both instruments. Empty MAT row keys and
  equal dimensions cannot establish correspondence.
- UCPH: physical tablet/assay keys across NIR/NIT/Raman, batch relationships and
  reuse scope. Batch/replicate labels alone are insufficient.
- Litter: GEN trap/collection-to-plot/tree links, composite memberships and assay
  events/batches; crops: leaf-to-plant/time/assay map; Garrett: exact modality and
  OSSL-to-original profile/horizon/laboratory mappings.

The first litter integrity audit also inspected retained paired reference values.
That source-audit access flag was incorrect. The corrected adapter compares
development values and retained keys only; [the explicit correction and real
24-label adversary](benchmarks/alpha11/source-isolation.json) preserve all earlier
outputs. No retained outcome entered model fitting, hyperparameter selection or
performance scoring; sanitized numerical inputs and folds are exactly unchanged.
