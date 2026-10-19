# Matched stress endpoints

Frozen before the new reference and stress outcomes. The six selected context
tasks compare the SAME evaluation observations, three training regimes and two
fixed models. Full reference uses all non-evaluation development observations;
stress excludes the selected evaluation context; the size-control reference
uses an exact-size whole-component subset and must retain that context.
Available target cases intersect each frozen population consistently.

Each regime reports its own training-mean baseline and ordinary skill.
For the paired primary D_skill, both stress and size-control predictions use
the SAME size-control training-mean null RMSE on the common evaluation IDs:
`D_skill = (RMSE_stress - RMSE_size_control) / RMSE_null_size_control`.
This avoids interpreting changes in the null denominator as deterioration.
D_RMSE is the unscaled numerator in target units. Full-reference versus stress
scores are retained separately and are training-size confounded. A zero common
null denominator makes D_skill unavailable, not zero.

Three train-only FlexiblePCA fits per task request one centered component.
Evaluation transforms reuse those fitted states. Report the fraction outside
each training PC1 range, training/evaluation PC1 native summaries and target
range extrapolation. A single-PC range is limited spectral-support evidence;
full retained-subspace residual coverage and causal shortcut attribution remain
unavailable. Registered H1-H5 are unchanged: these declared-context experiments
are exploratory precursors, without independent studies or a complete test of
the registered stability/pipeline/identity estimands.
