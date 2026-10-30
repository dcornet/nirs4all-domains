# Domains product roadmap

Domains provides reusable structural diagnostics and deployment-aware validation
interpretation. Product objectives D1–D5 remain stable; releases update qualified
capabilities, coverage, limitations and evidence. A research result is not a
product feature, and useful descriptive diagnostics do not require causal shortcut
confirmation. Status comes from [campaign evidence](campaign/status.json).

| Product milestone | Responsibilities | Completion evidence | Current next decision |
|---|---|---|---|
| D1 — Comprehensive structural evidence | Authorized X, populations, neighborhoods/proximity, known factors and qualified multi-scale geometry | Selected-branch persistence/support v1, original hierarchy linkage, adversarial/native qualification | Extend verified unit support or separately qualify resampling interpretation; keep continuous/noise cases |
| D2 — Validation interpretation | Intended use, target population, dependencies, group basis and spectral support | Optional v1 API/CLI annotation, supported/unsupported claims and adversarial compatibility checks | Gather consumer feedback on the v1 annotation; keep split choice conditional on intended use |
| D3 — Model-result contextualization | Compatible estimator/pipeline outcomes, evaluation populations and sensitivity | Optional v1 comparison API/CLI, exact target/units, ID matching, null/baseline context, public replay and adversarial tests | Gather consumer feedback; extend metric adapters only for a concrete report consumer |
| D4 — Usable integration | Stable reports/APIs and Datasets, Preflight, Methods, DAG/model interoperability | Existing schema compatibility, reproducible artifacts and actual tests/CI | Validate a pointer-based research import against current schemas; do not rebuild a framework |
| D5 — Evidence-supported guidance | Calibrated diagnostic interpretation and purpose-specific recommendations | Controlled tests, benefits/failures, stable providers and explicit scientific limits | Qualify one limited guidance rule for an explicit intended use; no universal risk score |

Current baseline: 164 entries / 171 views, 137 complete raw/SNV profiles, 43
source-permitted public profiles and 682 complete primary quantitative reference
tasks. These counts describe coverage and compatible research evidence, not
independent databases or validated product guidance. The first optional
[multi-scale descriptor](SELECTED_BRANCH_PERSISTENCE.md) now qualifies selected
branch persistence and support under one frozen native fit; broader descriptor
families remain planned. The v1 validation annotation adds symbolic interpretation of existing
evidence, with no numerical capability, synthetic spectra, estimator or causal
validation.

## Deployment changes interpretation

Within-experiment proof of concept, new specimens/acquisitions in a stable known
context, and new experimental contexts are distinct intended uses. KFold/SPXY and
group-exclusive designs can each be appropriate for different questions. An
unseen genotype, block or instrument is not an unseen whole experiment by default.
No split is selected merely because a metadata column is categorical. Unknown
intent produces multiple conditional interpretations, not a quality label.
See [validation intents](VALIDATION_INTENTS.md).

## Implemented first product improvement

The optional [validation-intent v1 API/CLI](VALIDATION_INTERPRETATION_API.md)
references existing report content without changing its schema or numerical
evidence. Three intended uses plus unknown intent produce conditional supported
and unsupported claims, dependency/factor evidence, group basis, support and
transductive status. The [public tablet example](examples/validation-intent/README.md)
and synthetic adversarial checks exercise the distinctions. No split selector,
fit, PCA, acquisition or native-kernel change is added. The staged
[implementation/resource plan](VALIDATION_INTERPRETATION_V1_PLAN.md) and
[release report](RELEASE_VALIDATION_INTENT_V1.md) record limits and execution.

The next D1 increment is implemented: [selected-branch persistence/support v1](SELECTED_BRANCH_PERSISTENCE.md),
an optional content-bound sidecar with a dedicated native hierarchy transport.
Its [public example](examples/multiscale/README.md) and
[release evidence](RELEASE_D1_PERSISTENCE_V1.md) distinguish within-fit persistence,
observation support, resampling robustness and unknown independence.

The bounded [D3 comparison v1](COMPARISON_INTERPRETATION_API.md) is implemented
and tested on synthetic/public fixtures. It reads existing results, distinguishes
ID matching from unequal/unknown populations, rejects target/unit mismatches,
retains separate null/skill definitions, and explains relative deterioration
against the reference baseline. The [tablet example](examples/comparison/README.md)
retains historical bytes and unknown physical dependencies. No real fit or
inferential test is added. D1 integration remains in owner-controlled
[PR #1](https://github.com/dcornet/nirs4all-domains/pull/1); it is not merged to main.

Next product priority is **D4**: integrate the optional D1–D3 companions with
one concrete existing report consumer, preserving source/pointer validation and
unknown evidence. Remaining D1 families and broader D3 metrics require separate
qualification; no bank campaign or universal model/validation selector follows.

## Separate research decisions

[R1–R5](STRUCTURAL_GENERALIZATION_RESEARCH_PROGRAM.md) covers mechanisms,
multi-scale correspondence, deployment-dependent degradation, remedies and
publication. The [boundary](PRODUCT_RESEARCH_BOUNDARY.md) assigns ownership;
promotion requires generic usefulness and scientific qualification, not success
on one dataset. No research fitting or new repository creation follows from this
roadmap. The two programs can progress independently.

The M1–M5 research-oriented roadmap is preserved at the immutable
[5b0354a snapshot](https://github.com/dcornet/nirs4all-domains/blob/5b0354a236318e42188a17f9703363a33e6df706/docs/ROADMAP.md).
[Earlier roadmap](ROADMAP_PRE_SCIENTIFIC_RESET.md),
[v2 design](STRUCTURAL_FRAGILITY_RESEARCH_V2.md),
[v2 pilot](STRUCTURAL_FRAGILITY_V2_PILOT_PLAN.md), frozen H1–H5 and historical
results remain unchanged. The [continuity manifest](research-continuity.json)
references these records without moving or duplicating an archive.
