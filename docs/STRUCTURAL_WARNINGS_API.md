# Conditional structural warnings v1

`nirs4all_domains.structural_warnings` interprets already measured evidence. It
works without Y, an estimator or a complete experimental identity mapping. No
PCA, clustering, score or model is computed. Existing reports and predictions
remain unchanged; JSON and Markdown are optional, content-bound companions.

```python
from nirs4all_domains.structural_warnings import interpret, markdown, validate_annotation

annotation = interpret(existing_report, request)
validate_annotation(existing_report, annotation)
section = markdown(annotation)
```

```shell
python -m nirs4all_domains.structural_warnings docs/examples/structural-warnings/tablet.report.json --request docs/examples/structural-warnings/tablet.request.json --out results/tablet-warnings.json
```

The CLI also writes `tablet-warnings.md`; it refuses existing outputs or paths
that would replace a source/request. Consumers may append that Markdown section
to their own report. The [schema](../schemas/structural-warnings.v1.schema.json)
is packaged with the bridge; no legacy schema/default consumer is changed.

## Source and measurement bindings

The request contains a `source`, `evidence` bindings and optional existing D2
`validation_intent`. Source identity includes dataset/source/content version,
fitted population ID, scope, representation and original observation count.
Historical identifiers remain historical, not aliases silently rebound to a new
catalog version. References and original-source identifiers remain explicit.

Each binding declares a kind, evidence-root JSON pointer, exact source scope,
native/documentary method/version/settings/reference, measurement pointers and
qualifications. Values may be finite recorded scalars/arrays or existing
status/reason/value states. This is a reader of existing report fields, not an
alternative loader or diagnostic engine. The same pointer/hash conventions as
D2/D3 are reused. Scope mismatches, malformed states, nonfinite values, stale
annotations, edited conclusions and measurement pointers outside their root fail.

Bindings are provenance declarations, not independent authentication. The caller
must supply actual recorded method/settings and source-role evidence. Missing
native configuration stays explicit; a receipt is not permission to invent it.
Comparative inputs require matched original populations/observations and query
references as appropriate. Source fields present in a record are cross-checked.

Representation contrasts need distinct named representations; parameter
contrasts can compare settings within one representation. A Preflight binding
qualifies physical dependence only for verified declared-identity or
shared-reference overlap (`preflight_finding_scope`); spectral duplicates alone
do not establish physical units. This interpreter does not replace that audit.

## Five conditional findings

| Warning ID | Observable condition | Concrete next check / prerequisite |
|---|---|---|
| `physical_unit_dependence` | Declared technical repetitions/shared specimens/reference units or a qualified existing Preflight finding | Inspect actual unit/split overlap through existing Preflight controls; evaluate an indivisible-unit contrast only when deployment concerns new units. X clusters and repeated-key counts alone do not qualify. |
| `experimental_factor_structure` | Qualified non-Y metadata with recorded descriptive factor-PC correspondence | Establish whether that specific factor changes in intended deployment, then inspect a matching contrast with original memberships, crossed factors and whole units preserved. A categorical column alone requires no GroupKFold/LOGO. |
| `preprocessing_dependent_organization` | Matched admissible representation/parameter comparisons or a computed all-noise result | Check sensitivity of the motivating conclusion; distinguish full-X neighbors, PCA geometry, density partitions and parameters. Do not choose a favorable preprocessing winner. |
| `spectral_support_mismatch` | Observed evaluation X exceeding a train-fitted PC1 range | Inspect extrapolation and multivariate overlap for that observed deployment population. Full-X fitting does not qualify; zero PC1 exceedance does not prove full support. |
| `insufficient_experimental_context` | Specific physical/acquisition/reference or deployment questions remain unanswered by this report | Read available original mappings/metadata; otherwise retain the limitation and perform explicitly exploratory sensitivity checks. Do not reconstruct groups or label the dataset dangerous. |

Every record includes observation/method provenance, a **risk hypothesis**,
conditions, alternatives, checks/prerequisites/testability, exact evidence scope,
dataset/view/source coverage and limitations. Existing state invariants apply:
`status=computed` has null reason and a qualitative `value` of `observed`,
`conditional` or `contradicted`; unavailable has a reason and null value. These
are interpretation states, never numerical risk scores or global dataset grades.
The separate observation state retains the measured values, including zero.

No severity threshold is fitted. Arithmetic zero/nonzero and identity endpoints
describe recorded measures, not significance or estimated prevalence of harm.
High PC1 alone does not establish a shortcut; weak ARI does not negate continuous
factor variation. All-noise, trivial ARI and native refusal are different states.
Target-derived metadata are excluded from primary X-only factor evidence.
Cardinality, missing levels, acquisition weights, repeated units and confounding
remain explicit. Marginal eta-squared is not causal attribution.

Unknown intended use retains the existing three D2 conditional interpretations.
Predicting observations within one experiment, new specimens, future dates/new
instruments and entire independent experiments need different evidence. A
recommendation is a conditional analysis to consider, not an automatic splitter
or preprocessing choice. `testability=available` means referenced inputs exist;
it does not authorize or execute a new scientific fit.

## Coverage and metric semantics

Each warning automatically identifies the supporting dataset identity, X view,
eligible/computed/unavailable case, representation/native scope and references.
Original database grouping remains unavailable when no authoritative identifier
is supplied. Declared provenance groups are not certified independent studies.
Factor rows, targets, PCs and preprocessing variants never add dataset votes.
Research aggregates exact case coverage using these owner annotations, without
introducing a competing interpretation engine.

D1 needs no predictive skill. Where historical skill is discussed, the actual
frozen bridge uses `one_minus_rmse_over_null_rmse` = `1 - RMSE/null_RMSE`.
`one_minus_squared_rmse_over_squared_null_rmse` is a distinct formula and must
not silently replace it. Frozen numerical evidence is unchanged. Neither scalar
is converted to a probability or expected performance loss by this interpreter.

See the [worked report and five qualified source snapshots](examples/structural-warnings/README.md)
and [pre-test behavior plan](D1_WARNINGS_V1_PLAN.md).
