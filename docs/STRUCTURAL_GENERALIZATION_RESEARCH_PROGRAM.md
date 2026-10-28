# Structural generalization research program — proposal

Prospective R1–R5 program, revision 2026-10-28. Proposed future home:
`nirs4all-structural-research`. That repository has not been created. The program
reuses Domains diagnostics and public model execution APIs; it is not the generic
Domains product definition. No experiment, GPU setup or model training is authorized
by this document. [Ownership and promotion](PRODUCT_RESEARCH_BOUNDARY.md) remain separate.

The research question asks when structural organization contributes additional,
target/estimator/pipeline/deployment-dependent predictive dependence while useful
X–Y signal remains. Small but statistically supported contributions can matter.
Magnitude, uncertainty, statistical significance and causal interpretation are
distinct. There is no arbitrary 20%/30% deterioration threshold or universal
shortcut-risk probability.

## Research milestones

| Milestone | Research question and work | Completion evidence |
|---|---|---|
| R1 — Structural mechanisms | Real X with IID random targets, group-random targets and useful spectral signal plus weak/zero injected group effects | Calibrated null response, effect sizes and uncertainty, falsifiers, estimator dependence and clear mechanism limits |
| R2 — Multi-scale correspondence | Discrete, continuous, nested, crossed and partially nested structures; compare X hierarchies with documented factors | Support, stability, representation sensitivity, correspondence/disagreement and cases without a biological hierarchy |
| R3 — Deployment-dependent degradation | Representative, known-group, unseen-group and external-experiment prediction | Separate absolute out-of-domain utility, baseline skill and relative/common-null deterioration for the actual intended shift |
| R4 — Representation/model remedies | Global linear/nonlinear models, local neighborhoods, hierarchical or soft-gated experts, SSL/contrastive/invariant features and controlled/generative spectra | Improvement on prespecified genuinely observed held-out groups/specimens with unchanged original boundaries, complexity/cost and adverse cases |
| R5 — Scientific publication | Original-database-level evidence, dependency-aware synthesis, negative results and independent confirmation | Reproducible registrations/analyses, multiplicity control, effective independent support, explicit exploratory versus confirmation roles |

R4 includes possible RF/XGBoost routing and local TabPFN/TabICL comparisons as
hypotheses, not demonstrated remedies. New estimators belong in appropriate
upstream model/Methods packages. Domains can consume qualified diagnostic results
without housing every proposed learner or generator.

## Experimental units and outcomes

Use `portal -> original experimental database -> source/view -> target -> protocol -> estimator`.
Multiple EcoSIS collections are not one database merely because they share a portal
or material family. Multiple Y columns, folds and spectral views of one population
are dependent observations, not new independent databases. Preserve study/specimen
overlap and unknown relationships, and give original databases comparable macro
influence with within-database target effects and dispersion. Do not average raw
RMSE across incompatible target units or select the best target for synthesis.

Preserve `G = log(RMSE_stress / RMSE_reference)`, reference/null skill and common-null
effects where matched populations permit. Model deterioration conditional on
baseline skill, target family, estimator, preprocessing and protocol; retain
negative-skill baselines and mathematical-coupling/uncertainty limitations.
Also retain absolute out-of-domain error, null-relative predictive utility and
target units. An already poor model does not earn a robustness advantage merely
because it deteriorates little. Small G is not sufficient evidence of useful transfer.

Separate SPXY/LOGO benchmark-protocol gaps from known/unseen-group contrasts and
from entire-experiment holdout. Same evaluation observations and whole-component
size controls help where feasible, without isolating every causal mechanism.
Use qualified uncertainty and multiple-testing methods at the actual database/
dependency level; unknown independence cannot be repaired by counting many targets.

## Controlled mechanisms and candidate remedies

IID random targets probe pipeline null behavior; one favorable score is not proof
of leakage. Distinguish randomization under a frozen split from regenerating every
Y-dependent SPXY split. Outer Y cannot enter either selection pipeline. Group-random
targets measure engineered group recognition, not demonstrated real-target leakage.
Weak spectral-signal/group-effect simulations preserve useful signal, zero effects,
opposite model responses and unsupported cases. Freeze generators, seeds, groups,
SNR/scales and model settings before response evaluation. Monte Carlo draws do not
increase the number of independent experimental databases.

The [multi-scale/augmentation concept](MULTISCALE_AND_AUGMENTATION_NOTES.md) states
the synthetic-spectrum hypothesis, physical/conditional generation and SSL alternatives,
their risks and controls. Reduced clustering alone is not success. A real held-out
population, not synthetic evaluation samples, is the principal predictive endpoint.

## Continuity and current evidence

Domains currently records 137 characterized views and 682 complete primary
quantitative tasks, with exploratory context/pipeline and plot sensitivity.
Those counts are not an independent-database count or confirmed mechanism. The
existing PLS/Ridge and historical FastAOM evidence can be imported only with
matching content, target, representation, population, split and model lineage.
No TabICL execution evidence was identified at the preserved v2 baseline.
Do not silently substitute TabPFN or another estimator under its name.

[Frozen H1–H5](ALPHA13_SUPERVISED_PREREGISTRATION.md), the
[v2 research design](STRUCTURAL_FRAGILITY_RESEARCH_V2.md),
[v2 pilot](STRUCTURAL_FRAGILITY_V2_PILOT_PLAN.md), associated schema/example,
M1–M5 lineage and historical numerical outputs remain intact. They are associated
research records, not product prerequisites. Earlier observed results remain
exploratory; no future hypothesis is retrospectively validated.

## Separate first research experiment — proposal only

Start with the R1 null/weak-effect subset of the preserved v2 plan, without adding
an augmentation or expert-learning arm. Select at most three mapped database X
populations by pre-outcome diversity and metadata support, keeping unknown overlap
explicit. Retain the v2 fixed raw PLS/Ridge rules, two known/unseen regimes and at
most three folds. Use 100 IID, 20 group-random and 20 draws at each of lambda
`{0, 0.1, 0.5}` where the mechanism is applicable: at most
`3 * 180 * 2 * 3 * 2 = 6,480` model fits. Means add no model fits.

This is a subset, not an addition to the 10,848-fit v2 cap. It excludes new SPXY
null arms, VAE/SSL/TabPFN/TabICL, augmentation and a B60 expansion. Use only already
qualified memberships in this first subset; unsupported group mechanisms stay
unavailable. Freeze actual database mapping, coefficients, scales, seeds, target
generation, splits, provider evidence and analysis before authorization. Do not
choose them from favorable observed scores.

Planning estimate, not measurement: at 0.25–1 second per model fit plus 15–30
minutes of overhead, about 45–140 minutes, with a three-hour hard worker stop.
Propose sequential execution, at most 2 GiB RAM, 128 MiB additional local output
and 24 MiB campaign reservations inside then-current limits, subject to remeasurement
and the owner's scientific execution authorization. No new ceiling is approved by
this proposal. Preserve the existing task/evidence caps and 2 GiB free-volume reserve.
There are zero such fits/reservations in this assignment.

Three X populations can characterize conditional mechanism behavior, not support
a large independent cross-database significance model. A separate power/precision
and independent-database confirmation design is needed. Keep unfavorable, weak,
zero and opposite effects; do not extend computation just to obtain significance.

## Future repository README specification

Its README should state the scientific question, R1–R5, experimental database
units/dependencies, frozen versus exploratory evidence, controlled mechanisms,
deployment endpoints and nonclaims. Link to Domains versions and immutable source
evidence rather than mirror its implementation or data archive. Explain model/
provider ownership, reproducibility, source terms and independent confirmation.
The proposed [layout and continuity interface](RESEARCH_INTEROPERABILITY_AND_TRANSITION.md)
are preparatory documentation only.
