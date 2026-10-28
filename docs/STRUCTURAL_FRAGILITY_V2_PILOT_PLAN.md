# Proposed database-diverse fragility pilot

Proposal: `domains.structural_fragility.pilot.v2-draft1`, 2026-10-28.
**Not an execution authorization or a preregistered confirmatory analysis.**
This assignment performs documentation/schema/repository checks only, zero real
fits and zero new campaign reservations. No ceiling is raised. The owner budget
rule is unchanged; budget headroom alone does not authorize these proposed fits.

## Stage 0: existing evidence and database map

Use the [v2 design](STRUCTURAL_FRAGILITY_RESEARCH_V2.md) and existing study import.
Inspect at most 12 candidate original-database records using existing catalog
references/metadata, without raw acquisition or renewed unresolved owner enquiries.
Target up to six mapped databases spanning at least three material/measurement
families if eligible, preserving views, publication relationships, known overlaps
and unknown dependencies. Do not collapse EcoSIS into one unit or infer a database
from a catalog entry. A mapped record is not automatically an independent database.

Reuse all 137 available X profiles and existing PLS/Ridge reference outcomes where
content, target, representation, population, split and parameter identities match.
The existing five-context and five-plot designs are candidates, not ten independent
databases. Their observed outcomes imply exploratory reuse and preclude untouched
confirmation. The existing public confrontation covers 35 views, not 35 independent
databases. Do not fit again merely to reproduce available baseline predictions.

No TabICL result manifest was found in tracked evidence at `de803ef`. If compatible
evidence becomes accessible, bind its source/content, target, representation,
folds, retained-label isolation and model configuration before reuse. Do not install
or fit TabICL in this assignment, and do not substitute TabPFN or historical FastAOM
under its name. An unavailable optional model does not block PLS/Ridge work.

## Stage 1: real-target paired feasibility

Retain all genuine quantitative targets in each selected database, with at most
32 database/source/target tasks in the initial fit envelope. Select databases by
metadata/X diversity and feasibility, not predictive scores. If their complete
target/view set would exceed the bound, defer the entire additional database or
reprice before execution; do not choose its best targets. Shared-specimen views
remain nested/paired and cannot increase macro weight. Single-target illustrations
use a frozen semantic priority and stay separate from all-target synthesis.

Freeze eligible development observations, indivisible dependency components,
context evidence, missing-target policies, model parameters and common evaluation
IDs. Retain the fixed raw centered/unscaled PLS min(3,p,min_train_n-1), Ridge alpha=1
and training-only mean unless a separately qualified design explicitly changes
them. Existing reference predictions can be reused only on identical memberships.

At most three outer evaluation folds/contexts and four training regimes per task:
known-context size-control, context-excluded, representative SPXY, and its
size-controlled sampling comparator. Distinguish contrast A (protocol gap) from B
(known/unseen context), including available size-control pairs. True LOGO is used
only when every eligible context is held out within the fold bound; otherwise
prespecify three-fold GroupKFold or a labeled selected-context stress design.
Never truncate LOGO and keep its name. Known-context fits still exclude every
evaluation specimen/reference component.

SPXY is conditional on a qualified public provider and exact development-only
selection with untouched outer Y. No qualified SPXY execution is recorded here;
if that seam is missing, keep A unavailable, document the upstream request and
continue B. Do not copy a SPXY kernel into Domains. Group membership must be
supported; use labeled transductive LOCO-X or continuous-region stress when
appropriate, preserving all-noise and inapplicable cases. Spectral pseudo-groups
are not physical batches. Size-matched random pseudo-groups are an optional
replacement within the four-regime bound, not an unpriced extra arm.

Worst-case new real-model fits, without reuse:
`32 tasks * 4 regimes * 3 folds * 2 models = 768`.
The two-regime B-only fallback is at most 384. Mean baselines add no model fits.
Raw/SNV matched stress evidence is reused where valid; new SNV refits are outside
this first fitting envelope and require a separately priced extension.

## Stage 2: controlled targets on a diverse X subset

Before outcomes, choose at most three of the mapped database X populations by
material/X diversity and metadata support. Use only admitted development data;
do not decode or reuse sealed real test labels. Choose groups before synthetic Y:
verified/declared contexts where possible, otherwise explicitly engineered X
partitions. Continuous/noise-only cases do not force a cluster-based program.

Reuse qualified partition memberships where retained. If membership materialization
is necessary, separately cap it at six native PCA and twelve HDBSCAN calls across
the three paired raw/SNV X populations, using frozen descriptor parameters and
original identities. Do not overwrite or refit stored descriptor evidence to
improve outcomes. These calls expose membership for a new consumer, not new
descriptor selection. Reuse available stability evidence; a case needing a fresh
B60 program is deferred from LOCO-X rather than expanding this pilot silently.
No per-random-target PCA or clustering refit is included; Y-dependent SPXY
selection still regenerates per realization. Additional train-PCA support fits
outside existing compatible diagnostics require separate pricing.

Per eligible database:

- 100 IID independent target realizations.
- 20 independent group-random realizations.
- 20 independent draws at each of lambda `{0, 0.1, 0.5}` for a useful spectral
  signal plus group effect and noise: 60 realizations.

Freeze independent random-stream seeds and coefficient vectors before response
evaluation. A candidate generator is a deterministic linear spectral signal with
coefficients bound to original feature order and scales determined on a separate
fixed development generator-calibration population; group effects have unit SD
and noise SD is 0.25 of the signal scale. No outer-target normalization or
score-selected coefficients. The final freeze must supply the actual coefficient
hash, population, seeds, units, qualified generator/statistical APIs and signal
scale; these are currently **unfrozen design choices**, not executed generators.
Lambda is a mechanism grid, not a minimum scientifically important effect.
Check useful signal at lambda=0 before interpreting weak injected contributions,
with a predeclared failure outcome rather than favorable-seed retries.

Each realization receives at most two known/unseen regimes, three folds and two
fixed models: `3 * (100+20+60) * 2 * 3 * 2 = 6,480` fits.
For the 100 IID realizations, add separate SPXY frozen-split and fully regenerated
Y-dependent selection arms, with untouched outer labels:
`3 * 100 * 2 * 3 * 2 = 3,600` additional fits. These arms are unavailable if the
provider/selection boundary is unqualified, rather than silently using fixed
real-Y partitions as a full-pipeline null.

The optional `Y_real + lambda * group_effect` experiment is outside this envelope.
Random pseudo-group controls can replace an eligible arm prospectively; any extra
arm must be repriced. All support, failures and missing mechanisms are reported.

## Hard ceilings, expected costs and stopping

| Proposed stage | New model fits maximum | Intended interpretation |
|---|---:|---|
| Real targets, all four regimes | 768 | Exploratory paired effects conditional on baseline skill |
| IID/group/weak-effect synthetic targets | 6,480 | Controlled mechanism and null-response pilot |
| Separate SPXY null arms | 3,600 | Conditional frozen split versus complete Y-dependent pipeline |
| Total model fits worst case | 10,848 | A cap, reduced by reuse, inapplicability or provider failure |

The separate membership-materialization allowance is at most six PCA and twelve
HDBSCAN calls, with zero new B60 runs; these are not hidden in the model-fit count.

At an explicitly provisional 0.25-1 second per fit, the total suggests 45-181
minutes of fit time, plus 15-60 minutes of transport, splitting, bounded X-group
qualification and summaries:
roughly 1-4 hours. This is a planning assumption, not a measured benchmark. Frozen
source shapes and an authorized timing smoke batch must replace it before rollout.
Hard stop: four cumulative worker hours or the priced fit maximum, whichever
comes first; preserve unfinished cases as resource-deferred. No automatic retries
or larger jobs to obtain statistical significance.

Proposed execution is sequential, at most 2 GiB process RAM, 256 MiB per-task disk,
4 MiB persistent evidence per staged task and 128 MiB additional combined local
storage. Shared results retain seeds, aggregate null distributions and necessary
paired real OOF receipts; no X copies per fold or permanent synthetic-Y matrix per
realization. Cap reservations at **32 MiB total**, including scratch and evidence.
Use at most eight staged allocations of 4 MiB; no per-fit reservation multiplication.
Retain the 2 GiB free-volume reserve on every participating volume.

The last verified journal leaves 41,471,022 bytes under the unchanged
1,805,306,368 reservation ceiling; 32 MiB would leave 7,916,590 bytes. Last measured
combined use was 19,074,429,261 under 20,289,597,121 bytes. These are historical
measurements, not current approval or free-space evidence. Re-measure participation,
workspace and volumes before proposing execution. This document consumes none
of those reservations. No acquisition, deletion, migration or upstream edit.

## Analysis freeze and release conditions

Before fitting, finalize database/overlap map, exact targets, generators/seeds,
group/partition rules, native provider evidence, membership-bound nulls, timing,
budget and owner execution authorization. Schema examples are illustrative only.
Existing native RMSE supplies the scalar log-ratio/contrast assembly in the task
protocol. Model fitting, hierarchical inference, interval and multiplicity kernels
require qualified public upstream capabilities, not copied numerical implementations.

Synthesize G with reference skill, paired common-null effects, support and
uncertainty. Give databases comparable influence, keeping target/view dependence
and higher overlap blocks. Freeze the primary multiplicity family and sensitivity
analyses before outcomes; report intervals and significance as unavailable where
independent support/provider qualification is insufficient. One hundred IID draws
give limited tail precision, especially under multiplicity: favorable-score
frequency is not automatically a nominal false-positive rate. Expand Monte Carlo
precision only through a separately bounded future proposal.

Keep small, zero, adverse and estimator-opposed effects. The pilot is exploratory
and mechanism-oriented; its reused databases cannot become independent confirmation.
No statistical significance or causal shortcut claim follows from this plan.
Six mapped databases, with unresolved overlap, do not supply adequate independent
support for a large descriptor-by-model-by-target interaction model. The pilot
estimates feasibility and variation; a later database-level power/precision plan
must justify detection of weak effects without counting targets or random draws
as new databases.
