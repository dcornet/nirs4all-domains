# Alpha.9 real-data qualification report

## A — Admission audit

**One genuinely new real non-leaf task is admitted and scientifically executed:**
Perten cereals X/Moisture. The 42 public catalog entries (33 coarse P1 candidates)
and four additional private entries have explicit review records. Numeric
identifiers do not become continuous chemical outcomes. Protein and botanical
alternatives are deferred before prediction inspection; no favorable-score
replacement is performed. Full-bank qualification is incomplete.

## B — Rights and provenance

The official Zenodo API declares CC-BY-4.0/open access for Perten; its archive
checksum matches local bytes. All four rights dimensions are allowed with source
attribution, overriding stale catalog inference for this local task. Original CSV
IDs establish 450 distinct specimens; local repeated row counters are irrelevant.
The unkeyed local Y is ignored, with a tested original-ID adapter supplying
references. Assay event IDs, precision, harvest/farm links and unambiguous moisture
basis remain unknown. No raw spectra are published.

Cartilage's original Figshare revised MAT/CC0 route is resolved. Its local
positional converter is not verified against original location/reference keys;
five joints/44 regions/869 locations and donor links require closure. The software
500-row guard is separate from scientific support. Previously reported poor
prediction is retained without inventing an alignment error or silently calling
the dataset a positive benchmark.

## C — New real scientific evidence

Perten preserves all 450 specimens and 141 channels: 359 development records in
17 conservative instrument-model/country/year blocks; 91 retained outcomes in
five blocks remain sealed. Native input QC finds no missing spectral cells or
exact cross-physical/cross-partition duplicates. Train PCA retains two PCs and
99.4187% variance; heuristic retained-X coverage flags 19/91. Exact effective
dimension is 1.16423. Country/cereal/instrument eta-squared values are .34455 /
.04537 / .11695, with whole-block uncertainty and source-meaning limitations.

Context-safe PLS RMSE is 2.38729 versus null 3.35315; R²=.48376. Cereal-only RMSE
3.96845 is worse than null; cereal-plus-residual gives 2.83506. Cereal closure
holdout raises spectral RMSE to 5.08562, instrument-model holdout to 3.49175.
Paired degradation intervals are [1.73698, 3.75934] and [.30939, 1.81983]. Units
are source moisture percentage points, without wet/dry conversion. Only two
cereal closure units remain. A size control covers only 38 IDs/two blocks, so it
does not identify a size-adjusted all-359 effect. Post-prediction target
extrapolation affects 14/359, 18/359 and 21/359 respectively.

HDBSCAN stability is unavailable below its prespecified 20-component gate.
All three global and three within-cereal interventions remain unavailable under
whole-vector size/composition/reference/power gates; zero effective attempts
establish neither independence nor zero effect. These are complete availability
findings, not fabricated numerical results. See ALPHA9_NONLEAF_PILOT.md.

## D — Transfer evidence

No new paired-source task is qualified. CORN's original spectral/property objects
have empty row labels and row-axis keys. The owner explicitly keeps CORN pending
without rights justification. Shootout needs original reference/pair/partition
equivalence and resolution of the official 654/local 655 discrepancy; UCPH needs
specimen/assay keys beyond batch/replicate. Different axes remain explicit; row
position cannot supply correspondence. Minimal requests are in
ALPHA9_PAIRED_SOURCE_PILOT.md. Perten instrument-model holdout is a different-
specimen context challenge, not paired-instrument transfer.

## E — Registry and frozen suites

Task ID: `0991a012c4244761e04beae32405424fe152b835bd653aeddd67571844b96ec6`.
Evidence ID: `e9a5d4cb6f112424e806e27280ac12306a5694f3695adbc01f78dac08776896b`.
The immutable Perten comparison suite was frozen before Ridge evaluation.
The structure-challenge suite contains Perten plus frozen alpha.8 EcoSIS;
the low-dependence-candidate suite remains empty. Source/protocol/content/fold/
provider changes invalidate reuse. The Datasets integration is an external
sidecar, without upstream edits.

```sh
python -m nirs4all_domains.bank query --registry docs/benchmarks/alpha9 --purpose structure_sensitive_challenge
python -m nirs4all_domains.bank freeze-suite --registry docs/benchmarks/alpha9 --purpose structure_sensitive_challenge --metrics configs/bank/taskwise-rmse-v1.json --out results/new-estimator-suite.json
python scripts/check_alpha9_registry.py
```

## F — Benchmark suitability

Perten is a **structure-sensitive challenge**, within documented identity limits.
Native fixed Ridge alpha=1 gives RMSE 2.61656 reference, 2.84675 cereal holdout
and 3.43364 instrument holdout. Its cereal degradation interval crosses zero,
while instrument degradation is .81708 [.43571, 1.03168]. PLS and Ridge differ
substantially on cereal stress. This limits PLS-only interpretation and does not
certify estimator-independent low dependence. Membership is unchanged after Ridge.
No raw RMSE averaging across moisture and EcoSIS LMA units occurs.

## G — Architecture and storage

The two crates and alpha.8 stages remain. New code is limited to admission,
verified identity transport, fixed-family native orchestration and compact
publication/validation. Datasets owns the one external canonical reproduction;
Methods owns all numerical kernels and DAG-ML owns native CV/refit. Existing raw
archive reuse is 499,245 bytes; new raw acquisition is zero.

The valid cache is 1,301,245 bytes; including the preserved first partial cache,
the external cache contains 1,650,665 bytes. Pilot files occupy about 12.69 MB.
Combined unique task evidence is **4,058,783 bytes**, below the 4,194,304-byte cap;
verified identical new exports share file identities. Main P1–P4 checkpoint reuse
is 4/4. All campaign reservations total 164,172,913 bytes, below 512 MiB and the
256 MiB task cap. Fixed Rust build/tooling growth dominates the 463.79 MB measured
workspace increase; the original workspace ceiling and 2 GiB volume reserves
remain satisfied. No historical artifact is deleted or migrated. Exact snapshots
and distinctions between logical/unique bytes are in audit/alpha9-storage.json.
The secondary planner's initial 12-fit estimate is corrected to 32 from the
eight frozen outer folds (three inner fits plus one refit each). Numerical
results and byte reservations are unchanged. Historical supplementary receipts
pin driver source `e711cc8`; the source is preserved in Git.

## H — Upstream needs

Prepared proposals request Perten metadata/rights/reference clarification,
original CORN/Shootout/UCPH key tables and permitted reuse scope, and a corrected
Cartilage source route/identity adapter. Methods/DAG already support the executed
PLS/Ridge protocols. No upstream repository is modified and no issue or message
is posted. See UPSTREAM_DEPENDENCIES.md.

## I — Validation

**128 tests pass locally: 35 Rust + 93 Python**, preserving all 105 alpha.8 tests.
fmt, Clippy with denied warnings, workspace/native gates, rustdoc, schema/report/
registry checks and isolated wheel import pass. The 69,575-byte wheel matches the
executed controller. All 133 protected historical files retain their hashes.
One 103-prediction PLS fold replays exactly; a complete second campaign is not
claimed. Native rank failures, retained-label isolation and deterministic
content-bound reuse are executable gates. Actual Windows/Ubuntu CI and source
commit references are recorded in VALIDATION.md and audit/github-ci-alpha9.json.
[Windows and Ubuntu CI completed successfully](https://github.com/dcornet/nirs4all-domains/actions/runs/39020893216)
on scientific source `e711cc8a0900f1adb7c64d139694faab82790cd1`; both actual logs
report 93 Python tests and all native Rust/report/registry gates pass.

## J — Bounded alpha.10

Resolve one paired-source original key table/reuse scope and qualify the original
Cartilage location/region/joint/donor/reference adapter. Measure scalable native
costs on the full admissible population, without truncation. Freeze task/split/
membership before performance, then compare a small prespecified set of native
families and fold-local preprocessing chains with matched component uncertainty.
Clarify Perten moisture basis and assay/harvest dependencies. Keep structural
challenge and within-population improvement suites distinct; do not launch a
high-cost full-bank campaign or infer a universal shortcut probability.
