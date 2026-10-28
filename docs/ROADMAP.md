# Domains product roadmap

Domains provides reusable structural diagnostics and deployment-aware validation
interpretation. Product objectives D1–D5 remain stable; releases update qualified
capabilities, coverage, limitations and evidence. A research result is not a
product feature, and useful descriptive diagnostics do not require causal shortcut
confirmation. Status comes from [campaign evidence](campaign/status.json).

| Product milestone | Responsibilities | Completion evidence | Current next decision |
|---|---|---|---|
| D1 — Comprehensive structural evidence | Authorized X, populations, neighborhoods/proximity, known factors and qualified multi-scale geometry | Source/protocol coverage, support, missingness, provider and executable qualification | Expose existing hierarchy information only after auditing its scientific meaning; keep continuous/noise cases |
| D2 — Validation interpretation | Intended use, target population, dependencies, group basis and spectral support | Descriptions that state supported and stronger unsupported claims; adversarial scenario checks | Add a small optional validation-intent annotation while preserving existing reports |
| D3 — Model-result contextualization | Compatible estimator/pipeline outcomes, evaluation populations and sensitivity | Source/content/target/split/pipeline identity, null comparison and uncertainty scope | Demonstrate read-only interpretation of an existing matched comparison without refitting |
| D4 — Usable integration | Stable reports/APIs and Datasets, Preflight, Methods, DAG/model interoperability | Existing schema compatibility, reproducible artifacts and actual tests/CI | Validate a pointer-based research import against current schemas; do not rebuild a framework |
| D5 — Evidence-supported guidance | Calibrated diagnostic interpretation and purpose-specific recommendations | Controlled tests, benefits/failures, stable providers and explicit scientific limits | Qualify one limited guidance rule for an explicit intended use; no universal risk score |

Current baseline: 164 entries / 171 views, 137 complete raw/SNV profiles, 43
source-permitted public profiles and 682 complete primary quantitative reference
tasks. These counts describe coverage and compatible research evidence, not
independent databases or validated product guidance. Multi-scale fields exist in
the native adapter, while a generic interpreted multi-scale descriptor family
remains planned. The current task adds documentation/ownership, not numerical
capabilities, synthetic spectra, estimators or causal validation.

## Deployment changes interpretation

Within-experiment proof of concept, new specimens/acquisitions in a stable known
context, and new experimental contexts are distinct intended uses. KFold/SPXY and
group-exclusive designs can each be appropriate for different questions. An
unseen genotype, block or instrument is not an unseen whole experiment by default.
No split is selected merely because a metadata column is categorical. Unknown
intent produces multiple conditional interpretations, not a quality label.
See [validation intents](VALIDATION_INTENTS.md).

## Bounded next product improvement — proposal only

Propose an optional, documented validation-intent annotation referencing an
existing report. Scope: the three intended uses plus unknown intent; supported
and unsupported claims, population/unit evidence, unseen factor, group basis,
support and transductive status. Preserve old schemas and defaults; no automatic
split recommendation or risk score. Before coding, state expected scenario
behavior and add only necessary compatibility/interpretation checks. No new
numerical kernel, model fit, raw acquisition or private artifact is required.
Suggested engineering envelope: one annotation/example and at most eight small
scenario fixtures, 16 MiB local output, zero campaign reservations and no ceiling
increase. This is a next-step proposal, not implementation in this assignment.

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
