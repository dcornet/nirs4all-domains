# Alpha.9 admission and execution protocol

Protocol `domains.admission.v0.1`, frozen before prediction-performance inspection.
The alpha.8 architecture, all historical evidence and its scientific tolerances
remain in force. Admission uses source documentation, identity metadata and byte
costs; no predictor score is an admission input.

The first prespecified new task is **Perten cereals / X / Moisture**. The original
Zenodo record (DOI 10.5281/zenodo.15838136) declares open access and CC-BY-4.0 in
its live API. The held 499,245-byte archive has official MD5
`d7666419f0de9385b1fe1da517c2d478` and SHA-256
`aa90b0df79f8206a491851bb60c102e72c4256ea2744c8d5eb90029d7eab259f`.
The source contains 150 uniquely named specimens per cereal, 450 distinct IDs
overall. The XLSX sampling notes say there are no duplicates. `original_row_id`
is a converter's local row counter; it is not a physical identity.

Moisture is an oven reference in source percent moisture units. The spreadsheet's
"Reference for moisture: Dry Basis" comment also refers to protein, so the exact
wet/dry-basis interpretation remains ambiguous. No conversion or precision claim
will be made. Protein is a meaningful Kjeldahl target but is deferred, without
inspecting its predictive performance. A logical specimen/target record is not
an independently verified laboratory assay event.

Use all 450 specimens, all 141 original channels (950–1650 nm, 5 nm step), one
supplied spectrum per specimen. Instrument/country/year tuples form **22
conservative context blocks**, including missing-value tuples. These are explicit
experimental blocking units, not asserted original batches. Instrument denotes a
model, not a serial number; country may denote growing or measurement location.
Hold out ceil(20% of blocks), by seed-17 SHA-256 order, before reading outcomes.
No specimen is discarded to meet a software cap. Retained outcomes stay sealed.
Use the existing singleton-compatible technical-mean policy; no numerical average
is needed for one observation per specimen.

The first deep configuration uses three outer / three inner whole-block folds,
PLS components 1–3, cereal as the group baseline, cereal and instrument closure
holdouts, one size-control order, and three scheduled global/within-cereal
training interventions. Preserve unavailable designs when closure/cardinality
or the existing >=50% / >=6-block exchangeability gates fail. These are bounded
exploratory checks, without a permutation significance or causal interpretation.
Native rank errors remain explicit failed designs; no score-driven grid retry.
Use 100 whole-block frozen-OOF bootstrap draws; confidence intervals remain
unavailable below the existing ten-component / 100-success gates.

Expected scientific behavior: safe folds cannot split context blocks or specimen
references. A strong cereal baseline can reflect real chemical differences.
Holdout deterioration can reflect sample size, composition or target extrapolation.
Weak skill is a retained result. Missing groups, low-power interventions and PLS
success cannot establish low structural dependence. Train-fitted PCA/coverage and
metadata association are independent from deep predictive availability.

The public catalog is screened systematically for genuine quantitative targets;
numeric specimen codes are ineligible outcomes. Cartilage is reviewed against
the original paper and source identity adapter, retaining its previously reported
weak prediction concern. Five joints and 869 locations are different independence
counts. CORN and Shootout require original keyed source/reference equivalence and
separate access, analysis, publication and redistribution decisions. An unresolved
dimension remains unknown; a private catalog tier alone decides none of them.

The existing reviewed policy remains 256 MiB/task, 4 MiB evidence/task, 512 MiB
campaign, serial execution and a 2 GiB reserve on every volume. A fresh unique-file
measurement found 11,512,569,233 bytes, leaving 482,060,592 bytes under the original
11,994,629,825-byte workspace ceiling. No budget ceiling is increased. Reuse held
raw bytes read-only; Datasets writes a single canonical cache revision. Check
digests and costs before canonical preparation and before fitting. P0–P4 use the
existing journal. No source acquisition or restricted bytes enter hosted CI.

After task/split qualification and suite freezing, audit and execute a small
Methods/DAG-ML Ridge comparison if supported. Use exactly the frozen evaluation
IDs. Selection of tasks must not consume that estimator's scores. Ridge evidence
alone will not imply estimator-independent certification.

Tests precede real fits: permissions separated by dimension, original identity
evidence, identifier target rejection, reordered/unmatched paired keys, reference
contradictions/sharing, incompatible axes, held-out source isolation, closure,
rank errors, deterministic admission, unavailable interventions, exact reuse,
restart/isolation, compactness, sealed retained outcomes and synthetic exclusion.
Analytical native checks retain absolute tolerance 1e-10; same-input local replay
uses exact values/digests. Cross-platform numerical controls use stated finite
tolerances rather than frozen Windows artifact hashes.

## Source re-audit outcome

The final frozen admission is `2a2a882a254deae838dd0ca361d0b20b8c96ab7cdc2883d9db7dee5c0c8b858a`.
The local standardized Y table has no observation key. Its first provider
preparation emitted a warning and was preserved without fitting. The admitted
task uses the original specimen-keyed CSV reference adapter, verified before
prediction; it does not attach IDs to that unkeyed table by row position.

All 42 public entries and four additional private candidates have machine-readable
review decisions in audit/alpha9-source-admission.json. Perten is admitted;
Protein and botanical fallbacks are deferred before performance inspection.
Cartilage's original Figshare article 7803845 version 2 has CC0 data rights and
a 26,657,431-byte revised MAT file. The Springer supplementary ZIP is metadata,
not the original spectral/reference matrix. Local derived alignment, region/
joint/donor closure and full-population deep support still need qualification.
Previously reported weak prediction remains an unresolved scientific observation.
It is not labeled an alignment error or used to discard the dataset.

CORN's original MAT lacks row sample keys for all three sources and propvals.
The owner explicitly keeps it pending without rights justification. Shootout and
UCPH retain their specific original-key/reference/reuse questions. No restricted
real-data fit or raw redistribution is performed. The audit is a single-agent
corroboration of original source evidence, without a claim of independent human
review. The intended non-leaf expansion is achieved by Perten; paired transfer
remains incomplete for the documented reasons.
