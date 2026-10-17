# Alpha.12 execution transport

The two prespecified sentinel sources use individual draw StageStore records.
Native callback duration is measured separately from full scheduler elapsed
time. Repeated workspace inventory/identity verification can dominate small
native fits. The running sentinel experiment is allowed to finish unchanged.

For the five remaining already selected cases, a bounded 20-draw callback may
use one existing StageStore reservation/serial lease per representation/fraction.
The X protocol, exact component subsets, seed, PCA/HDBSCAN settings, providers
and quality gates do not change. The transport contract is separately versioned
`domains.alpha12.batched_resume.v0.1`, with the same frozen input identity.

Each completed draw is atomically checksummed in its attempt scratch directory.
A failed batch retains its completed prefix. A retry validates exact source,
provider, selected-index and controller fingerprints, rejects conflicting or
corrupted checkpoints, and executes only missing draws. Failed-attempt byte
reservations remain charged. No historical scratch or source is removed.

Release validation retained one failed test attempt: a new 512×1024 analytic
neighbor batching fixture was exactly rank one while requesting 20 PCA
components, and FlexiblePCA returned status 8. The neighbor property was never
reached. The fixture now adds known coordinate impulses, retaining its full
shape and an analytically derived nearest distance `sqrt(2+1/256)` at abs1e-10,
while supplying sufficient rank to exercise the intended public-call boundary.
The focused native check passes. No real profile, scientific threshold or
provider/controller implementation changed; the full Python gate is repeated.

Each 20-draw stage reserves 640 KiB scratch plus 640 KiB essential evidence.
All task/campaign/evidence/volume limits and serial execution remain unchanged.
Before admitting the remaining cases, complete both sentinel sources and record
measured callback time, current workspace, cumulative reservations and estimated
remaining costs. This is a cost-based scheduling decision, not a source or
threshold selection based on observed stability. No active fit is canceled.
