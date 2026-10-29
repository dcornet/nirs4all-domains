# Validation interpretation v1 API

Available in `nirs4all-domains-bridge 0.1.0a19`. This optional D2 feature explains
an existing result relative to declared prediction objectives. It does not fit,
load raw data, select splits or judge whether a score is good.

## CLI

```shell
python -m nirs4all_domains.validation_intent existing-report.json --intent intent.json --out results/intent-annotation.json
```

The input is any finite JSON report object, including X-only reports without
target/estimator. The command creates `intent-annotation.json` and
`intent-annotation.md`; it refuses to overwrite the source, request or existing
outputs. Omit `--intent` for three conditional interpretations of unknown use.
The [worked public example](examples/validation-intent/README.md) is executable.

## Python

```python
import json
from nirs4all_domains.validation_intent import interpret, markdown, validate_annotation

with open("existing-report.json", encoding="utf-8") as stream:
    report = json.load(stream)
annotation = interpret(report, {
    "intended_use": "known_context",
    "prediction_population": "New acquisitions from known specimens on the existing instrument",
    "prediction_unit": "new_acquisitions",
    "split": {"family": "random_kfold", "description": "Declared observation-level CV"},
    "transductive": False,
})
validate_annotation(report, annotation)
section = markdown(annotation)  # append to a consumer's human-readable report
```

No metric reference is supplied here, so this example explicitly establishes no
prediction performance. To interpret a stored score, add e.g.
`"prediction_metrics": [{"name": "rmse", "pointer": "/metrics/rmse"}]` where
that exact RFC 6901 pointer resolves to an existing
`{"status": "computed", "reason": null, "value": 1.2}` state. Supported metric
names are RMSE, MAE, MSE and R² (`rmse`, `mae`, `mse`, `r2`). Only finite scalar
states are accepted; negative error metrics and unavailable states are rejected.
Values are referenced, not copied or interpreted as proof of useful prediction.
This narrow v1 adapter does not discover metrics or convert arbitrary score
formats. Callers must select metrics from the same evaluation they describe.

## Request contract

All top-level request fields are optional. Unknown defaults limit interpretation.
The strict contract is `$defs/request` in
[`validation-intent.v1.schema.json`](../schemas/validation-intent.v1.schema.json).
Unknown keys, truthy strings in boolean fields and nonfinite JSON are rejected.

| Field | Meaning |
|---|---|
| `intended_use` | `proof_of_concept`, `known_context`, `outside_context`, or `unknown` |
| `prediction_population`, `prediction_unit` | Population text and `new_specimens`, `new_acquisitions`, `new_context`, or `unknown` |
| `split.family`, `split.description` | Actual declared family: random/representative, grouped, LOGO, LOCO-X, context/external/temporal holdout, other or unknown; not a recommendation |
| `dependencies[]` | Named unit, kind, evidence quality, separation and reference; retain specimens, shared assays and sessions separately |
| `factors[]` | Name/kind, relevance to objective, exclusion, evidence/reference and relationship text; crossed factors need not form a tree |
| `groups.basis`, `groups.construction` | Physical, declared context, X-derived, mixed, none or unknown; construction declared, train-only, complete-X or unknown |
| `transductive` | Boolean or null; complete-X group construction forces true even if supplied false, with a conflict limitation; its groups are treated as X-derived even if labeled physical |
| `prediction_metrics[]` | Existing computed scalar metric pointers, not new predictions |
| `spectral_support[]` | Existing evidence pointer, description, representation, reference population and limitations; unavailable support remains explicitly missing |
| `limitations[]` | Additional evaluation-specific limitations, retained verbatim |

Evidence quality is `unknown`, `declared` or `verified`. The latter two require
a nonempty reference. **Verified is a caller assertion**, not certification by
the interpreter. Separation/exclusion may be null. A factor kind does not create
physical identity; `Type` is not automatically an experiment or genotype.

For new-specimen interpretation within a known context, v1 conservatively
requires an explicit verified separated specimen unit, no recorded crossing
dependency, a known evaluation family, known non-transduction and no X-derived
grouping. Ordinary KFold can satisfy this when actual unit separation is verified
(for example, one independent specimen per observation). This is a claim guard,
not a recommendation to replace KFold with LOGO. Missing or lower-quality
evidence yields a conditional reading.
Factor holdout describes observed excluded levels only, without proving future
unseen-level performance. Random/representative CV and LOCO-X never supply that
factor-transfer claim. A temporal family label does not authenticate time order;
document the actual deployment direction in the split evidence/limitations.

## Optional serialization and compatibility

The annotation is a **linked companion**, not a replacement report envelope or
a new global result framework. Existing reports and Rust/Python consumers need
no new fields. This also supports historical schemas with
`additionalProperties: false`; never inject a key into them. Existing native
serialization remains unchanged and is not expected to preserve arbitrary new
fields. The annotation root has its own small schema; no historical schema is
relaxed or regenerated differently.

`source_report.sha256` binds the entire report using existing Domains
`storage.fingerprint`: sorted-key compact JSON, default ASCII string escaping,
finite values, one newline, UTF-8 SHA-256. It binds JSON content, not input
whitespace, an external file path, or independently authenticated provenance.
`validate_annotation(report, annotation)` recomputes the deterministic reading
and rejects a stale report or edited claims. A syntax-only JSON Schema check
does not provide that semantic validation. No timestamp makes repeated calls
vary; no report value is changed. Missing transductive status uses explicit
`unavailable`/reason/null, not an invented boolean. Other facts use nullable
declarations with explicit evidence quality and a missing-information list.

V1 does not verify raw-data identities, source permissions, metric/split
provenance, sampling representativeness, training leakage or complete dependency
enumeration. It does not certify independent generalization or produce a causal
shortcut/risk score. Those limits accompany every reading. Spectral support is
specific to representation/reference; a PC range is not full support.
