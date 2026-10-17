# External Datasets sidecar — domains.datasets_sidecar.v0.1

Datasets owns source axes, content versions, identities, access and canonical
bytes; Domains owns benchmark tasks and qualification. No upstream card changes.

`datasets-sidecar.v1.schema.json` binds dataset/content version, task ID, Domains
protocol, relative evidence reference, exact evidence SHA-256 and purpose tags.
Consumers resolve under a trusted sidecar root, validate schema/hash/context,
and display availability/limitations. Tags are not universal quality ranks;
dataset native splits remain declarations rather than automatically applied tasks.

The [EcoSIS sidecar](benchmarks/alpha8/datasets-sidecar.json) references compact
Domains evidence. Ignored machine configuration resolves authorized cache locator
keys. No private absolute path/token or heavyweight source/debug data is embedded.
Missing evidence/authorized bytes or hash mismatch remains explicit; a small
sidecar alone does not promise exact replay.

Proposed upstream work: optional versioned external qualification-link field and
partition-aware target access. Acquisition/cache/verification stays in Datasets.
This proposal modifies no upstream repository and posts no external message.
