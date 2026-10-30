# D1 selected-branch persistence v1 — qualification plan

Baseline: `378dc4ca752c3ab3e60f2514da1bdfa062e9a7da`. Frozen before new
qualification tests on 2026-10-30. This is a generic X-only product feature.

## Provider semantics and expected behavior

Reuse Methods 1.3.6 / ABI 2.19 `n4m_cluster_hdbscan`, the existing owning Rust
adapter and public Methods summary ABI. No alternative clustering, quantile or
stability algorithm. The audited header and implementation at Methods commit
`131a15a6bbf73a8ab941c7b3fb81b21f6b71b059` define persistence as selected-node
excess of mass divided by **assigned members times global maximum lambda**.
The implementation returns 1 when that maximum is zero/infinite (also for a
zero-member cluster). Such conventions are not strong empirical support.
Tree size is size at birth, not necessarily assigned observation count.
Labels index the persistence vector; selected-node labels link to the tree.

Expose one optional content-bound sidecar: per-selected-cluster persistence and
assigned observation counts/fractions, equal-cluster descriptive summaries,
noise, exact representation/configuration, and references to original evidence.
The original full tree remains in the source report. Add opt-in hierarchy
transport to the existing X-profile CLI; its default output remains unchanged.
Compact historical reports must declare missing persistence/tree, never recover
them from counts. A missing field does not invalidate other available support.

- No selected clusters: observed all-noise partition, persistence distribution
  not applicable; no low-risk certificate or proof of a continuous population.
- One selected cluster: no demonstrated multiple-population separation.
- Small clusters/repeats: retain observation support without independence claims.
- Missing/nonfinite persistence: explicit unavailable per-cluster/distribution
  state; never summarize just a favorable finite subset.
- Invalid labels, support counts or selected-node mapping: refuse the inconsistent
  partition rather than manufacture support.
- Raw/SNV: separate fitted geometries/configurations; no invariant-partition
  expectation, no selection of the more favorable representation.
- Degenerate spectra: preserve upstream failure/nonfinite conventions and flag
  them; do not reinterpret a persistence of 1 as biological validity.
- Unknown identities/crossed factors: no metadata-to-tree or independent-unit
  inference. Within-fit persistence is distinct from resampling robustness,
  membership strength, significance, prediction skill and harmful shortcuts.

Counts, labels, tree links and content hashes must match exactly. Native public
reference persistence/tree values use abs/rel 1e-12; native-to-sidecar values are
copied exactly. Same-platform serialization is deterministic. No cross-database
ranking, universal hierarchy depth or risk probability is introduced.

## Stages and resources

1. Measure combined storage (including research/protected participating files),
   campaign reservations and C:/D: free space; preserve the journal/history.
2. Implement optional transport, descriptor/schema/API/CLI and a public synthetic
   example; preserve old report bytes and default behavior.
3. Bound new qualification to at most 64 native HDBSCAN and 16 PCA calls on
   synthetic/public fixtures, serial execution, no Y or supervised fitting,
   no B60 or bank campaign, no new raw acquisition or campaign reservation.
4. Run format/Clippy/workspace/native, bridge/JSON/schema/package regression
   gates and actual Windows/Ubuntu CI. Existing regression workloads are
   accounted separately from the new qualification; no upstream kernel rebuild.

At most 512 MiB incremental local engineering/fixture/log/package output,
2 GiB free reserved per volume, existing combined ceiling 20,289,597,121 bytes
and campaign ceiling 1,805,306,368 bytes. **No ceiling increase is authorized by
this mission or planned.** Stop/reduce work or seek review before exceeding an
actual limit. Preserve research artifacts and all historical report bytes.
Release report must give actual usage, test scope and final-commit CI evidence.
