# D3 read-only comparison v1 — execution plan

Frozen before implementation/tests, 2026-10-30. Base: D1 `93c503b`;
main remains `378dc4c`. D1 PR [#1](https://github.com/dcornet/nirs4all-domains/pull/1)
is open, not merged. D3 will use a separate dependent branch.

Expected scientific behavior: compare existing RMSE values only after exact
target semantics and units compatibility. Unknown compatibility yields no
direct numerical contrast; incompatible values explicitly reject it. Equal
counts or a shared database name never imply paired evaluations. Matching
explicit unique evaluation IDs in the same source/content and population can
support an ID-matched contrast, not independent sampling or significance.
Different populations, training sizes, models and pipelines remain visible.
Null/skill definitions stay separate when their population/definition differs.
Positive skill means improvement over the stated null only, not practical
usefulness; zero/negative skill makes relative deterioration a weak-baseline
contrast. Missing/zero RMSE cannot produce an invented ratio. No fits, causal
shortcut inference, universal split preference or composite risk score.

Implementation: standalone optional content-bound companion, strict schema,
deterministic Python interpretation/validation and JSON/Markdown CLI. Reuse
validation-intent interpretation for each side, including unknown deployment,
dependencies, group basis, factors, transduction and spectral support. Accept
explicit pointers to existing evidence; no result database, raw inputs or new
numerical provider. Simple scalar RMSE subtraction/ratio is protocol assembly;
no metric, prediction, null, uncertainty or model is recomputed.

Validation: synthetic adversaries for matched/unmatched/reordered IDs, unequal
counts, targets/units, missing/zero/negative/nonfinite metrics, distinct nulls,
training populations, X clusters versus documented contexts, unknown identities,
stale bindings and exact input preservation. Hashes/IDs are exact; comparisons
use exact declared semantics, no fuzzy unit conversion/tolerance. Scalar formula
checks use absolute tolerance 1e-12. Public example reuses the historical tablet
report and preserves its bytes. Run bridge/schema/package regression plus
fmt/Clippy/workspace/native gates on synthetic fixtures and final-branch hosted
Windows/Ubuntu CI. No real scientific fit, new hierarchy fit or raw acquisition.

Resources, staged: review/inventory, implementation/public fixture, validation,
then Git/CI delivery. At most 512 MiB incremental local engineering output
(including logs/packages/application build artifacts), no new campaign
reservations and no ceiling increase planned. Initial combined usage
19,440,245,007 bytes, ceiling 20,289,597,121; campaign 1,801,584,082 of
1,805,306,368 bytes. C:/D: free 149,762,846,720 / 344,895,692,800 bytes.
Preserve 2 GiB free per volume, the scientific journal and all historical
reports/source hashes. Standing owner authorization permits at most
5,000,000,000 bytes increase per alpha without another request; any used
increase must be recorded. Stop or bound output before exceeding the plan.

D1 review: actual remote head and main match the above commits, two ahead/zero
behind, no pre-existing PR. CI run
[41030197917](https://github.com/dcornet/nirs4all-domains/actions/runs/41030197917)
passed both platforms at the exact D1 head. Only an additive sidecar schema is
introduced; legacy report schemas and frozen unsupervised/stream sources are
unchanged. Existing owning Methods adapter retains numerical ownership. Docs
separate within-fit persistence, resampling robustness and physical groups.
Remaining concern is scientific scope, not a known compatibility blocker:
observation support is not independent-unit support and broader cuts need
point-level paths not available from the condensed cluster-node transport.
