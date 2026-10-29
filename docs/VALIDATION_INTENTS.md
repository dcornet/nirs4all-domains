# Deployment-aware validation interpretation

Status: v1 interpretation API/CLI implemented as an optional linked annotation;
see [public usage and schema](VALIDATION_INTERPRETATION_API.md). It is not an
automatic split selector. The scenarios below define its scientific limits.
The appropriate evaluation depends on what the deployed model must predict.
KFold, SPXY, GroupKFold and LOGO are not universally ordered by quality.

## Intended-use scenarios

| Use | Prediction question | Possible evaluation | Supported interpretation | Stronger unsupported claim |
|---|---|---|---|---|
| Within-experiment proof of concept | Is there exploitable X–Y information inside the observed population? | Representative/within-population evaluation, controlling known repeats and shared references | Prediction within observed support | Independent experiment, new instrument or external-population transfer |
| Stable known operational context | Can genuinely new specimens or acquisitions be predicted in an already represented instrument/process/population/regime? | Specimen-, acquisition-session-, batch- or time-aware holdout matched to actual deployment | Operational prediction within that defined domain, conditional on verified dependencies | Transfer to an untested instrument, campaign or experiment |
| Outside the experimental context | Can prediction work for unseen genotypes, treatments, sites, campaigns, instruments, labs or experiments? | Exclude the relevant factor, use genuinely independent sources, or a justified external-domain design | Transfer only to the tested type and range of novelty | Universal domain transfer or new-experiment generalization from an unrelated internal group holdout |

New acquisitions from known specimens and new specimens are different populations.
Their admissible unit/dependency assumptions must be stated; repeated spectra
or shared assay references cannot silently count as independent specimens.
Temporal holdout requires the actual temporal deployment direction, not a
category relabeled as time. Missing metadata limits the relevant interpretation.

Leave-one-genotype-out does not automatically test a new experiment.
Leave-one-block-out does not automatically test a new instrument. An entire
original experiment held out is scientifically different from removing a group
inside one experiment. GroupKFold is justified by the intended novelty and
dependence, not by a column's categorical data type. True LOGO, GroupKFold and a
few selected context holdouts have different estimands and must retain their names.

SPXY uses development X/Y for representative calibration selection. An untouched
external/outer evaluation population, including its Y, must stay outside split
selection, preprocessing, tuning and generator fitting for a prospective claim.
An all-development-Y retrospective partition can be described as such; it is
not an untouched external evaluation. Indivisible sample/reference components
remain separated in every candidate design.

## Groups, X structures and support

Documented factors can be hierarchical, crossed or partially nested: for example,
genotype crossed with treatment inside blocks, repeated years, sessions and
instruments. Record the actual relationships and unknowns rather than forcing
them into one tree or treating every factor as an indivisible biological identity.

Distinguish physical/dependency units, declared experimental/context metadata and
X-derived structures. Report association, disagreement and unknown correspondence.
LOCO-X is an exploratory geometric support test; it is not experimental LOGO.
Complete-X cluster construction is explicitly transductive and never uses held-out
Y to choose clustering or representation. Its use as a proxy for an instrument,
site or experimental shift requires evidence of that correspondence.

Report support as measured, with uncertainty: overlap, extrapolation and
unknown/partial support are properties relative to the specified representation
and reference population. Being inside a one-PC range is not proof of general
support; a heuristic fence is not a calibrated probability. An unseen factor can
remain spectrally in-support, and a known factor can contain out-of-support X.
Do not equate categorical novelty and measured geometric novelty.

## Optional interpretation record

An interpretation references an existing result instead of replacing its schema:

| Information | Required meaning |
|---|---|
| Intended use | One specified question, or unknown with conditional alternatives |
| Target prediction population | New acquisitions/specimens/context/experiment, with source and target when applicable |
| Dependency-unit evidence | Physical, specimen/reference/session links, their provenance and unknowns |
| Evaluation split family | Actual KFold/representative/SPXY/LOGO/GroupKFold/LOCO-X/external design and membership reference |
| Unseen context | Exact factor/levels or experiment excluded; unknown where unsupported |
| Support | In-support/out-of-support/partial/unknown relative to a stated representation and diagnostic |
| Group basis | Physical/dependency evidence, declared metadata, X-derived, mixed or unavailable; retain crossed-factor relationships |
| Transduction | What complete/held-out X entered construction; Y remains protected |
| Limitations | Missing dependence, support, target or source evidence and uncertainty scope |
| Supported claim | Specific observation or prediction interpretation supported by the actual evidence |
| Stronger unsupported claim | Explicitly untested specimen/domain/experiment transfer or mechanism |

X-only results may have no target or estimator. Unknown fields retain explicit
reason/value states; do not invent intended use, groups, independent database
count or a deployment-quality label. This annotation is not a required
field of existing reports.

For example, the same within-population score with unknown intended use can have
three conditional readings: proof-of-concept evidence within observed support;
operational relevance only if new-unit and dependency assumptions are supported;
and no demonstrated external-context transfer. Domains should present these
alternatives rather than pronounce the split correct or incorrect universally.

## V1 interpretation expectations

The annotation preserves old schemas/defaults and works without
Y or predictions. Changing the claimed deployment from known instrument to new
instrument must change the supported interpretation, not recompute or reinterpret
the old score as evidence of the new deployment. A categorical genotype column
must not trigger automatic GroupKFold; X clusters must not be labeled physical
batches. Unknown intent must retain alternatives, and crossed metadata must not
be silently converted to a hierarchy. These are interpretation/compatibility
expectations, not newly executed numerical protocols. The
[pre-test implementation plan](VALIDATION_INTERPRETATION_V1_PLAN.md) and
[API contract](VALIDATION_INTERPRETATION_API.md) record the executed scope.
