# Alpha.10 prespecified comparison — domains.multifamily.v0.1

Frozen before any alpha.10 Perten predictions. Task admission, original specimen
and reference assumptions, all 359 development IDs/17 context blocks, 91 sealed
retained outcomes, target units and three exact alpha.9 outer designs are retained.
Historical PLS and fixed Ridge remain distinct immutable reference experiments.
The new protocol/task links them by content and fold digests; membership is chosen
from alpha.9 qualification evidence, without new-estimator scores.

The configuration in configs/pilots/multifamily-alpha10-v1.json fixes:

* Methods Ridge, centered X/Y and unscaled X: alpha 0.0001, 0.01, 1, 100, 10000.
* One controlled preprocessing comparison: public Methods SNV then PLS 1–3.
  This is a fixed pipeline with inner-selected components, not a broad grid.
* nirs4all FastAOM hard chain: compact bank, depth 1, beam 12, raw/SNV bases,
  rank cap 32, at most eight finalists, per-base four/per-family two; latent
  component candidates 1–3. Fixed latent Ridge lambda 0.01.
* Secondary sparse MKR: same bank/bases/rank/screen, at most three active chains,
  fixed lambda 1 and a single external configuration. Run only if controlled
  qualification succeeds. Otherwise publish its exact unavailable reason.

FastAOM is the published nirs4all 1.4.10 Python/NumPy/SciPy implementation,
audited at 1aefd473a0ebeef28adc0d808c4a4b0c9c45fa9f. Its fast-source files match
the wheel exactly. It is an explicitly requested optional upstream estimator;
Domains copies no algorithm. It is distinct from Methods' native FastAOM
branch-CV facades. The actual constructor is FastAOMPLSRidge(FastAOMConfig(...)).
TabPFN is deferred. PCR is deferred in favor of the requested adaptive family.

All new families use identical three-fold inner group designs inside each exact
outer train population, with fresh fitted state per candidate/fold and one
DAG-selected refit. Native DAG-ML selects minimum mean validation RMSE using its
deterministic tie rule. Candidate budgets differ and will be reported. No outer
validation or retained X/Y enters screening, basis/preprocessor fitting, candidate
selection or refit. Internal FastAOM cv_n_components is forbidden: its shuffled
KFold cannot preserve dependency components. Singleton lambda grids disable
rowwise LOOCV/GCV-based parameter selection; those internal diagnostics are not
validation evidence. Hard-chain supervised operator extraction is part of fitting
on the current training subset. Rank truncation currently follows a full thin
NumPy SVD, so rank cap is not a computational SVD budget. Depth 1 bounds actual
enumeration; beam pruning alone occurs after enumeration and is not such a bound.

Expected behavior before tests: identical population/fold digests across models;
inner-training artifact/prediction state invariant to inner-validation Y changes;
held-out spectra cannot change fitted training state; predictions on one held-out
spectrum cannot depend on other held-out spectra. Changing content, configuration,
protocol, implementation or provider invalidates reuse. A native candidate error
fails its declared experiment, with an explicit receipt, without an adaptive retry
or a reduced grid. Fixed and tuned Ridge cannot share an experiment identity.

Analytical/native scalar tolerance remains absolute 1e-10. FastAOM controlled
prediction and serialization parity use absolute 1e-9, relative 1e-9; native
same-input Perten replay is exact, FastAOM repeat fits use 1e-9. All values must
be finite. Components, fold membership and fingerprints use exact equality.
Controlled mechanism tests use native metrics on constructed OOF predictions;
they qualify paired interaction assembly, not a duplicated fitting algorithm.

Interactions are (RMSE_A_stress − RMSE_A_reference) minus the corresponding
B degradation on the same physical IDs. One paired draw resamples the same
original context blocks for all four prediction vectors. Use 100 requested
whole-component draws; intervals need 100 successes and ten original components.
These condition on frozen fitted OOF predictions. Model-refit/repeated-design
uncertainty is unavailable. Population-of-new-cereal uncertainty is unavailable
with only two cereal closure units. Report actual memberships and diversity;
359 pooled predictions do not supply 359 group-transfer experiments.

Retain the 38-ID/two-block size-control limitation. An exact whole-component
subset-feasibility audit may enumerate sizes without outcomes, without selecting
more favorable evaluation subsets. Target-range diagnostics remain post-prediction.
No low-dependence label follows from a favorable estimator or powerless stress.

Run serially under the existing cumulative campaign journal, with the owner-
approved workspace ceiling 12,531,500,737 bytes; other reviewed caps remain
512 MiB campaign/256 MiB per task/4 MiB evidence per task/2 GiB free per volume.
New protocol task IDs are legitimate separate experiments and preserve their
alpha.9 parent identity. No historical cleanup, migration or upstream edit.
