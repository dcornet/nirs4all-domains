# Two historical tablet context results, read without refitting

This example compares two compatible predictive results within the existing
[alpha.17 public tablet report](../../benchmarks/alpha17/tablet-pilot-summary.json),
using the raw PLS pipeline for original Type C (reference) and Type A (stress).
The same source report supplies both objects; `evaluation` selects their separate
context entries. Source permission for ordinary aggregates is retained in the
historical report. No raw data, identities, folds, models or new fits are exposed.

```shell
python scripts/run_comparison_example.py --out results/tablet-comparison
python -m nirs4all_domains.comparison_interpretation docs/benchmarks/alpha17/tablet-pilot-summary.json docs/benchmarks/alpha17/tablet-pilot-summary.json --request docs/examples/comparison/tablet.request.json --out results/tablet-comparison-cli.json
```

[`tablet.request.json`](tablet.request.json) is the pointer/intent mapping;
[`tablet.annotation.json`](tablet.annotation.json) is the deterministic companion;
[`tablet.annotation.md`](tablet.annotation.md) is its rendered interpretation.
The source's byte SHA-256 remains
`0ea810ced51d38877a21d548798418b8361d9682d6b11ccef04d7be44dfeb247`.

| Condition | Type C (reference) | Type A (stress) |
|---|---:|---:|
| Evaluation observations | 80 | 70 |
| Training observations | 230 | 240 |
| RMSE, percent mass/mass | 0.823900 | 1.104235 |
| Skill `1 - RMSE / training-mean-null RMSE` | 0.206703 | 0.594149 |

The target semantics and units agree. Errors are numerically comparable, but
the observations, target ranges and training populations differ. This is an
**unmatched context contrast**, not a controlled split effect or paired
prediction test. No evaluation IDs are published; different context populations
and counts already rule out matching. Skill is larger on Type A even though its
absolute RMSE is worse, because the nulls address different evaluation
populations. Domains therefore keeps those skill definitions separate.

Both improve on their own training-only null. That does not establish practical
usefulness; in particular, historical Type A R² is negative. The report retains
its partial train-fitted PC summaries, unavailable qualified continuous support,
unknown physical/assay independence and original Type/block scope. Neither
Type holdout establishes unseen-instrument or independent-experiment transfer.
No H1–H5, shortcut mechanism or significance claim follows from this example.
