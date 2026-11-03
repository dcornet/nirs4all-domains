# Read-only predictive comparison v1

Bridge 0.1.0a21, protocol `domains.comparison_interpretation.v1`. D3 adds an
optional companion to existing reports. It reads no raw data and fits nothing.
The two roles **reference** and **stress** name the caller's contrast; they do
not rank split families or require a controlled split intervention.

```shell
python -m nirs4all_domains.comparison_interpretation reference.json stress.json --request comparison.json --out results/comparison.json
```

The CLI writes JSON and Markdown, refusing existing outputs and source/request
overwrites. Reports may be the same file with different evaluation pointers.
The [public historical example](examples/comparison/README.md) includes a complete
request, generated annotation and human-readable interpretation.

```python
import json
from nirs4all_domains.comparison_interpretation import interpret, markdown, validate_annotation

reference = json.load(open("reference.json", encoding="utf-8"))
stress = json.load(open("stress.json", encoding="utf-8"))
request = json.load(open("comparison.json", encoding="utf-8"))
annotation = interpret(reference, stress, request)
validate_annotation(reference, stress, annotation)
section = markdown(annotation)
```

The strict request is `$defs/comparison_request` in
[`comparison-interpretation.v1.schema.json`](../schemas/comparison-interpretation.v1.schema.json).
Each side requires `evaluation` (RFC 6901 pointer to an existing object; `""`
means root) and `pointers` (a mapping of the following optional fields).
Absent pointers resolve as unknown, never invented identities or zero values.
All pointers are absolute within that side's report. A supplied missing pointer
is an error. Caller mappings must refer to the exact source/content and
evaluation whose scores they describe; naming a pointer does not authenticate it.
Identity/count fields may also reference computed states; explicit unavailable
states resolve as unknown, so two equal unavailable states never prove identity.

| Pointer field | Existing evidence |
|---|---|
| `source` | Array of pointers identifying dataset, content version, view; or one pointer to an object containing these. Exact identity equality, no database-independence inference |
| `target`, `units` | Nonempty semantic and unit strings; both must match exactly before a direct numerical contrast. No implicit unit conversion, synonyms or fuzzy equivalence |
| `population` | Original evaluation population identity, not merely the split family |
| `evaluation_ids` | Array of unique nonempty strings, if available. Same set in the same source/content and population supports ID matching; order may differ. IDs are hashed, not reproduced in the companion |
| `n_evaluation` | Positive integer; must agree with supplied ID count. Equal counts alone never imply matching |
| `model`, `pipeline` | Existing model and preprocessing/selection specifications; equality does not imply identical fitted parameters |
| `training_population`, `n_train` | Original training identity and positive integer count. Unknown/per-fold counts should stay unavailable rather than inventing a pooled count |
| `rmse`, `skill`, `null_rmse` | Existing finite numeric scalar or status/reason/value state. RMSEs must be nonnegative. Metrics must lie inside the selected evaluation subtree |
| `null_population` | Evaluation population on which the null was scored, separately from the population used to train the null |

Each side can also supply `null_definition` (description including how/where the
null was trained), `skill_definition` (`one_minus_rmse_over_null_rmse` or null),
and `intent` (the existing [D2 request](VALIDATION_INTERPRETATION_API.md)).
Only that defined skill has a sign interpretation. A referenced null RMSE,
its definition and matching model/null evaluation population are needed before
interpreting reference skill. Positive means improvement over that null, not
practical usefulness. Zero/negative skill explicitly changes the reading of
relative deterioration. A defined skill whose sign contradicts the referenced
RMSE/null order is rejected; its exact magnitude is not recomputed or certified.
Different null definitions/populations keep skills separate. Even a shared
definition/population does not establish identical fold-specific null predictions;
v1 never calculates a skill difference or a common-null effect.

For each side, D2 retains deployment, novelty, dependencies, crossed factors,
group evidence, transduction, support and conditional unknown-use readings.
Existing computed-state RMSE is automatically referenced in D2 when no metric
was supplied. Scalar-only legacy metrics remain in D3 performance; D2's stricter
computed-state reader does not establish predictive claims from those scalars.
Explicit D2 prediction pointers must lie inside the evaluation subtree. No
physical independence follows from matching IDs or categorical columns; LOCO-X
remains geometric, and complete-X construction remains transductive.

## Output and numerical scope

The companion contains exact original metric values, pointer mappings,
source/evaluation conditions, compatibility states, identity matching, null
scope, baseline context, D2 interpretations and supported/unsupported claims.
Unknown or incompatible target/units make direct contrasts unavailable.
Different evaluation populations can still have comparable errors in the same
units, but their contrast is unmatched and confounded by population differences.
Different models, pipelines or training sizes similarly preclude an isolated
split-effect explanation.

Only two scalar contrasts are assembled: `stress_rmse - reference_rmse` and
`(stress_rmse - reference_rmse) / reference_rmse`. The latter is a **fraction**,
not a percentage or risk probability. Negative means lower stress RMSE.
Zero reference RMSE yields `ZERO_REFERENCE_RMSE` for the ratio while retaining
the absolute difference. Missing RMSE yields `RMSE_UNAVAILABLE`; nonfinite
arithmetic yields `ARITHMETIC_OVERFLOW`. No predictions, scores, nulls, intervals
or significance tests are recomputed. Missing support is never low risk.

`validate_annotation` verifies schema and deterministic regeneration against
**both full report hashes**, including predictions not selected by the request.
It rejects stale metrics, identities, mappings and edited claims. Hashing uses
the existing canonical finite-JSON/newline convention from D2/storage.
`markdown` checks structure only; consumers must validate against source reports
before trusting a saved companion. A hash proves content binding, not source
authenticity, target equivalence or physical/assay independence.

No existing report schema, byte, native kernel, crate or default consumer
changes. The packaged schema is additive. This bounded v1 handles RMSE and
already stored fractional RMSE skill; other error metrics, prediction-vector
alignment, unit conversion, common-null effects and inferential statistics
remain outside scope. There is no universal validation selector, causal shortcut
label or independent-database claim. See the [pre-test plan](D3_COMPARISON_V1_PLAN.md).
