# Alpha.13 preparation and bounded execution checkpoint

This preserves the 2026-10-17 preparation checkpoint. On 2026-10-18 the owner
approved +512 MiB, calibration completed at 6,498 PCA fits, and all 720 real
resampling fits completed. Two new X-only views and exact tablet correspondence
are published. Current completion/verification is recorded in ALPHA13_RELEASE_REPORT.md.

Original status on 2026-10-17: **incomplete; workspace-ceiling approval pending**.
Baseline HEAD remains `ebb1b9b8a45d01618931d846d059641701cac7da`.
No alpha.13 release commit, push, wheel qualification or CI success is claimed.

Completed evidence:

- All 164 catalog entries reviewed through metadata only; original public source
  leads for tablets, soil, beer and wheat documented. No new real spectra or
  targets acquired. No new confirmation study admitted.
- Exact whole-component joint-exposure expectations and prespecified identity
  simulation select 60 draws as the smallest tested feasible candidate. This is
  conditional design calibration, not a probability guarantee.
- The oracle decision controls yield no false robust/fragile decisions in the
  tested cases. The 12 stable setting cases are inconclusive at B=20 and resolved
  at B=60. These dependent setting cases are not independent populations.
- Nine-mechanism native calibration is partially complete: 4,334 unique PCA fits
  and 8,668 HDBSCAN attempts; 2,164 PCA fits remain. The next batch was refused
  before fitting. Completed stages and exact compatible prefixes are preserved.
- A distinct native stream transport has exact full-output parity on 33 paired
  fixtures plus a paired recovery request. Its engineering fits are separately
  counted. It changes startup overhead, not numerical methods or quality gates.
- H1–H5 operational descriptor families, outcomes, controls and falsification
  conditions frozen. Historical studies remain discovery cases. Unknown or
  shared populations cannot inflate confirmation support.
- All 235 Python tests pass, including the original 190. Rustfmt, whitespace,
  report JSON invariants and the alpha.12 result verifier pass. The 511 protected
  local files and 347 historical repository artifacts retain their bytes, with
  recorded pre-existing newline variants handled explicitly.

Still required, in order:

1. Obtain the workspace-ceiling decision in `ALPHA13_RESOURCE_PLAN.md`. The
   current ceiling remains 13,873,678,017 bytes; the requested +512 MiB ceiling
   would be 14,410,548,929 bytes. Other scheduler/campaign limits do not change.
2. Resume `scripts/continue_alpha13_calibration.py run` through
   `scripts/measure_alpha13_phase.py` with a new phase name. Preserve frozen
   protocol, generator, power module, original controller and qualified stream
   hashes. Cache reuse retains the actual original executable attribution.
3. Finish controlled qualification and no-refit latent recovery where meaningful;
   freeze the revised design before its first new real resampling fit.
4. Acquire only admitted original X/axis/identity projections; audit modality,
   original keys, rights and cost. Extend raw/SNV evidence and execute the bounded
   prespecified real stability cohort under exact task contracts.
5. Resolve study/reference feasibility. A PLS/Ridge pilot needs its own exact
   admission, roles, folds, controls and power gates; no pilot is mandatory when
   those gates cannot be met. No contrary or null case may be dropped.
6. Complete current-version clippy/Rust/ignored gates, rustdoc, packaging, full
   artifact verification, release reporting, commit/push and actual Windows and
   Ubuntu CI. The preparation checker intentionally reports incomplete evidence.

No historical cleanup, cache migration or implicit ceiling increase occurred.
The source code version is alpha.13; installed editable bridge metadata still
reports alpha.12. See `ALPHA13_EXECUTION_NOTES.md` and the interim validation JSON
for actual execution scope and the unavailable separate native-process peak.
