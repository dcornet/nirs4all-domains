# Selected-branch persistence and support v1

Protocol `domains.selected_branch_persistence.v1`, bridge 0.1.0a20. This D1
descriptor answers: under this frozen Euclidean HDBSCAN configuration and fitted
representation, which density branches were selected, how many rows support
them, and what is their within-fit persistence? It needs neither Y nor a model
nor complete experimental metadata. It does not choose a validation split.

## Meaning and qualification

Methods 1.3.6 / ABI 2.19 owns clustering. Its public
[header](https://github.com/GBeurier/nirs4all-methods/blob/131a15a6bbf73a8ab941c7b3fb81b21f6b71b059/cpp/include/n4m/metrics.h)
and [implementation](https://github.com/GBeurier/nirs4all-methods/blob/131a15a6bbf73a8ab941c7b3fb81b21f6b71b059/cpp/src/core/clustering/_vendored/hdbscan.cpp)
define selected-cluster persistence as excess-of-mass node stability divided by
assigned members times the **global maximum lambda of that fit**, where lambda
is inverse mutual-reachability distance. The native implementation returns 1
when that maximum is zero or infinite (also if assigned membership is zero;
Domains rejects empty selected clusters). Duplicate/tied coordinates may trigger
this convention. A value of 1 is not a probability or a validity certificate.

The existing [Rust adapter](../crates/nirs4all-domains/src/methods.rs) transports
label-indexed persistence and the original condensed cluster nodes. The new
optional X-profile transport retains those same outputs, without another fit
or a change in representation/configuration. Methods' public summary ABI owns
quartiles/median/mean/SD; Python only validates, counts memberships, assembles
ratios and transports records. Numerical ownership remains upstream.

The retained native hierarchy is a **cluster-node** transport: parent, size at
birth, selected label, birth/death lambda and node stability. It is not a table
of every observation's exit event or complete observation-to-ancestor paths.
References to the original tree mean this entire available native array;
neither counts nor the sidecar recover unexported point-level ancestry.

| Quantity | Meaning | Does not establish |
|---|---|---|
| Within-fit persistence | Selected branch's normalized excess of mass over one density hierarchy | Resampling stability, significance, biological validity |
| Membership strength | Relative native per-row strength; retained in the source evidence | Probability of correct assignment |
| Observation support | Assigned rows and fraction of the entire fitted population, including noise in the denominator | Independent specimens or effective sample size |
| Independent-unit support | Unavailable in v1; no general verified unit-map adapter is provided | Independence from unique row IDs or a categorical factor |
| Resampling robustness | Separately designed perturbation/repeated-fit evidence | Inference from one fit's persistence |

`tree_size` is size **at birth**, which may exceed assigned support. Tree node
indices, selected labels and persistence indices are checked before linking.
No tree depth, biological hierarchy, universal risk score, p-value or database
ranking is calculated. Crossing factors need separate correspondence evidence.
This product does not execute or validate R1/R2 research hypotheses.

## API and existing report consumers

```python
from nirs4all_domains.multiscale import describe, markdown

annotation = describe(existing_report, setting_index=0)
section = markdown(annotation)
```

```shell
python -m nirs4all_domains.multiscale existing-report.json --setting-index 0 --out results/branches.json
```

The CLI writes JSON plus `branches.md`. A source/output collision is refused.
The input object/file is unchanged. Fixed input/provider gives deterministic
serialization; source binding uses Domains' canonical JSON SHA-256. The
`source.native_pointer` and `hierarchy.value.pointer` resolve in that original
report. Preserve/access the source file to inspect the original tree; the
sidecar is not a replacement for it. Source formatting is not part of the
canonical content hash. Native and summary-provider versions/binary hashes
remain separate provenance; neither a field nor a version string authenticates
a caller's report.

Accepted sources:

- Full `domains.structure.v0.1` reports: one reference fit/setting. These use
  train-fitted PCA and technical-mean rows; the reported support unit explicitly
  says fitted representation row, rather than original acquisition count.
  The existing resampling-evidence pointer remains separate; it is not relabeled
  or requalified by the new descriptor.
- `domains.unsupervised.v0.1` native X-profiles: original observation rows,
  raw or SNV followed by the source's centered, unscaled retained PCA. Use the
  new **opt-in** `n4domains x-profile --include-hierarchy --methods-library ...`
  stdin command with the unchanged X-profile request. It adds
  `cluster_settings[i].value.hierarchy_evidence` with parameters and the entire
  `HdbscanOutput`. Default CLI/stream output and historical schemas stay unchanged.
- Compact historical profiles from that protocol: retained labels/counts can
  still support observation support. Missing persistence and tree stay
  unavailable. Higher-level bank matrices without keyed/native populations are
  not accepted as substitutes; use their referenced native report when retained.

The X-profile configuration remains `min_cluster_size` 8/12, `min_samples` 4
(counts the row itself), EOM selection and no single-root selection. The full
structure adapter uses the parameters actually recorded by its setting.
Retain input row order: the provider has explicit deterministic MST tie rules
but does not promise permutation invariance. The descriptor summarizes the
retained PCA-space hierarchy, not automatically every direction of original X.

## Output and edge cases

The additive [sidecar schema](../schemas/selected-branch-persistence.v1.schema.json)
is packaged with the bridge. Each cluster records its label, assigned support,
whole-population fraction, persistence state and optional original node index.
Both distributions give **one vote per selected cluster**, not per row, and
exclude noise from the cluster population. The noise fraction has all fitted
rows as denominator. Summary SD can be null for a singleton population.

No selected clusters gives `not_applicable/NO_SELECTED_CLUSTERS` for the
distributions. It reports all noise under the configuration; it proves neither
continuity nor low risk. One selected cluster does not establish multiple
distinct populations. Small clusters remain visible without a significance cut.

Missing/nonfinite native persistence stays unavailable per cluster; incomplete
persistence makes the entire persistence distribution unavailable rather than
silently summarizing only finite clusters. Other valid support remains usable.
Native hierarchy infinities are transported as null with original diagnostic
reasons. Provider zero/infinite-density conventions are flagged when observable
from retained evidence; missing tree information leaves their scope unknown.
Native failures/zero spectral variance retain their reason. Inconsistent counts,
selected node mapping, parameters or strengths are rejected. Missing summary
bindings limit summaries alone, preserving per-cluster original evidence.

This first qualification covers the pinned provider's semantics only. Unknown
provider versions keep support but cannot receive qualified persistence merely
because they return a similarly named field. Available metadata, effective
independence, real source geometry and biological interpretation need their own
evidence. No cross-database/representation scale comparability is established.

See the [worked example](examples/multiscale/README.md),
[pre-test plan](D1_PERSISTENCE_PLAN.md) and [release record](RELEASE_D1_PERSISTENCE_V1.md).
