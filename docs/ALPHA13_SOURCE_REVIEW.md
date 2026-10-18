# Alpha.13 source review: metadata stage

The portable `source-diversity-inventory.json` reviews all 164 pinned catalog
entries: 42 public and 122 private. This is an inventory of source views, not
164 independent studies. Only catalog descriptors and original public metadata
pages were read. No private spectra, reference cells or retained test outcomes
were opened. The new real-spectrum acquisition count is zero at this stage.

Catalog tier and original rights are separate. Four dimensions remain explicit:
source access, local analysis, derived-statistics publication and raw-data
redistribution. Public availability or a software-package license alone does not
establish every dimension for every third-party source. The earlier owner decision
leaves CORN pending; a mirror does not remove that blocker.

| Candidate | Material and original-study evidence | Source/identity admission still required |
|---|---|---|
| UCPH tablet NIR | Pharmaceutical development data; Dyrby and colleagues, Applied Spectroscopy 56(5), 579–585 (2002), identified by the original UCPH page. Catalog view: 310 × 404, transmittance, cm^-1. Official archive listing: 3,822,359 bytes. | Acquire the original archive under the storage gate; isolate the physical NIR view and original axes/keys without target reads. Equal row counts cannot join spectra, batch, replication and assay records. |
| Abisko soil | UCPH identifies Rinnan and Rinnan, Soil Biology & Biochemistry 39, 1664–1673 (2007), with 108 subsamples from 36 plots and two horizons. The OHPL soil view refers to this collection. | Verify the original plot-to-subsample keys and spectral view/axis. The 36 declared plots cannot become verified resampling components by assigning successive rows to triplets. Original and package views are not two independent studies. |
| OHPL beer | Package dataset documentation identifies the 60-sample beer example of Norgaard and colleagues, Applied Spectroscopy 54(3), 413–419 (2000): 576 bands, 1100–2250 nm. | Resolve original-source correspondence and rights, then obtain a selective X/axis/ID projection. The documented object includes training and test targets; decoding the complete object is not an admissible X-only shortcut. |
| OHPL wheat | Package documentation identifies Kalivas, Chemometrics and Intelligent Laboratory Systems 37(2), 255–259 (1997): 100 wheat observations, 701 bands, 1100–2500 nm. | Audit the underlying experimental collection and physical/reference keys. A paper describing datasets is not by itself proof of independence from every other cereal collection. Avoid materializing protein/moisture cells for X-only admission. |

The UCPH [dataset index](https://ucphchemometrics.com/datasets/) gives broad public
use permission for its downloadable material. The corresponding original
[tablet](https://ucphchemometrics.com/tablet/) and
[soil](https://ucphchemometrics.com/soilnir/) pages identify their studies. That
permission is scoped to verified original material; correspondence to an existing
canonical private-tier view still needs auditing. Raw redistribution is not
requested. OHPL's [dataset documentation](https://github.com/nanxstats/OHPL/tree/master/man)
provides a provenance lead and GPL package context; it does not replace missing
original specimen or assay evidence. Exact cached-page hashes accompany the
machine-readable inventory.

OSSL MIR and VIS-NIR entries remain distinct, even where a catalog modality
conflicts with its source name. Soil horizons and library revisions are views,
not automatically new populations. No complete soil-library download is planned.

No new candidate is yet an admitted confirmation study. Historical EcoSIS/CA2023,
Perten and litter cases retain discovery roles. The frozen H1–H5 contract records
zero admitted confirmation studies and an insufficient-information power state.
These are preparation-stage blockers awaiting source review, not a final finding
that independent validation or a bounded pilot is impossible.
