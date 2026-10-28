# Read-only research interface and transition proposal

Status: documentation-only v1. The proposed future repository
`nirs4all-structural-research` does not exist as an action of this assignment.
Creating it, moving private evidence/raw data or publishing new research artifacts
requires explicit owner approval. This plan does none of those operations.

## Keep one evidence lineage

Research imports Domains evidence and public model execution APIs; it does not
copy the toolkit or reimplement numerical kernels. Prefer existing JSON schemas,
compact manifests and immutable references. There is no second global result
schema, migration engine or new privacy/disclosure framework.

| Evidence identity / relationship | Existing record or read-only mapping | Missing-value interpretation |
|---|---|---|
| Original experimental database | Study interpretation contract and preserved v2 research hierarchy, with evidence-backed mapping | Catalog entry or portal is not an invented original database; unknown identity/overlap remains explicit |
| Source/view and content | `structural-matrix.json` source `dataset_id`, `content_version`, `source_id`, `view_id`; original report provenance | Do not join unrelated source axes, content versions or tables by position |
| Content/protocol fingerprint | Existing source, descriptor/campaign freezes and report provenance, bound to immutable commit/blob | Missing binding prevents that exact comparison; it need not invalidate unrelated X diagnostics |
| Representation and structural diagnostics | Existing source aggregate rows and native structure/X-profile reports | No target/model required for local descriptive X evidence; unsupported full moments/hierarchy remain unavailable |
| Target and model/pipeline | Existing task/model outcome records, model configuration/provider lineage | Null/absent when no compatible prediction result exists |
| Split and deployment intent | Existing FoldSet/population references plus the optional documented validation-intent description | Current reports may lack intent; provide conditional alternatives rather than retrofit a claimed deployment |
| Experimental versus X group basis | Existing declared/verified unit metadata or X-partition evidence; retain crossed-factor links | Never relabel X clusters as physical groups or infer independence from names |
| Support and uncertainty | Existing reference/evaluation populations, diagnostics, intervals and their scope | One-PC support and conditional OOF intervals retain their limits; no invented effective sample size |
| Outcomes and null baseline | Existing compatible native errors/skill and matched context comparisons | Preserve target units, evaluation membership and null denominator; incomparable pairs stay explicit |
| Evidence level / limitations | Existing status/reason/value, evidence roles and source/task limitations | Distinguish observation, concern, sensitivity, mechanism hypothesis and validated interpretation |

Existing schemas include [structure report](../schemas/structure-report.v1.schema.json),
[unsupervised evidence](../schemas/unsupervised-evidence.v1.schema.json),
[full-bank matrices](../schemas/full-bank-matrix.v1.schema.json),
[split-stress report](../schemas/split-stress-report.v1.schema.json),
[qualification evidence](../schemas/qualification-evidence.v1.schema.json) and
[study interpretation](../schemas/study-evidence.v1.schema.json).
The [v2 research hierarchy](../schemas/structural-fragility-research.v2.schema.json)
remains a proposed research format, not a replacement product schema.

A small consumer can maintain its own pointer/index mapping these identifiers to
existing evidence. Resolve declared source/content/target/population identities
and verify the referenced schema/version/fingerprint before combining records.
Scalar research estimands and inferential outputs live in the research registry
with links to their inputs; they must not overwrite local descriptive Domains
metrics or silently become calibrated product guidance. No new mandatory field
or behavior is added to current APIs in this documentation assignment.

Read-only import must not refit models, resample or rerun clustering as a side
effect. Future execution uses public providers under a separately frozen research
protocol. Discovery, post-outcome reinterpretation and independent confirmation
retain different roles; importing a frozen metric does not confirm a hypothesis.

## Source restrictions and public aggregates

Confidential raw inputs stay in existing Datasets/authorized storage. Sensitive
identifiers, credentials and explicit restrictions remain protected. Published
names/links and ordinary source-permitted aggregates can be reused according to
their actual terms; a private catalog tier is not itself a ban on derived metrics.
An external evidence pointer must not expose a private filesystem location or
silently grant access/publication rights. Unknown permissions restrict the
affected outgoing data, not all otherwise authorized local analysis. No new HMAC,
suppression layer or recurring public-aggregate approval system is introduced.

## Minimal continuity manifest

[research-continuity.json](research-continuity.json) records the inspected source
repository/commit and Git blob IDs for v2/H1–H5 and selected existing evidence,
with immutable public URLs. It is a reference inventory, not a results copy or
new global scientific schema. Product documentation can change while original
research records remain byte-equivalent to the recorded commit. The old M1–M5
roadmap is referenced at that commit, since the current roadmap now describes D1–D5.

The manifest distinguishes frozen research records from evolving product/status
indexes. All have immutable snapshots. Current campaign status, matrices, release
index and product roadmap may legitimately evolve in future releases without
rewriting the recorded snapshot; the continuity check must not freeze product
development forever. This assignment changes none of the historical result files.

Nothing is moved or deleted. A later owner-approved research repository would
initially link these immutable records; no large archive or private tree needs
copying. A future import should record both the Domains code/protocol version
and exact evidence content/version, not only a branch name such as `main`.

## Optional future repository layout

```text
README.md                 # Scientific question, scope, evidence roles and R1–R5
protocols/                # New frozen research designs, not duplicated kernels
registry/                 # Original-database/target/design/dependency records
evidence-pointers/        # Immutable source references; no copied raw/private archive
analyses/                 # Database-aware synthesis and publication reproducibility
experiments/              # Orchestration over public model/Methods/Domain APIs
tests/                    # Mechanism, leakage and evidence-import checks
```

The future README specification is in the [research program](STRUCTURAL_GENERALIZATION_RESEARCH_PROGRAM.md).
New models belong in the appropriate upstream package; the research repository
owns experimental orchestration and conclusions. Neither repository receives a
method automatically because it wins one dataset.

## Bounded transition sequence — proposal only

1. Keep product D1–D5 and research R1–R5 separate; retain existing references in place.
2. Obtain explicit approval before any repository creation or data/artifact movement.
3. If approved, create only the minimal README/registry/pointer skeleton first.
4. Validate one X-only and one compatible supervised read-only import with source,
   content, target, representation, split and pipeline parity; preserve unknown intent.
5. Freeze any new experimental execution and budget separately. A successful
   import is not permission to fit a VAE, expert model or synthetic-target campaign.

No acquisition, publication of new scientific results, private artifacts, model
training, schema migration or storage-ceiling increase is part of this transition.
