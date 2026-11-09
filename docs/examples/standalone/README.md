# Standalone review of existing public tablet evidence

```shell
python scripts/run_standalone_example.py --out results/standalone-tablet
```

Open `results/standalone-tablet.html` locally; Markdown and JSON are written beside
it. Both cases reuse unchanged existing public reports and saved companions:

- [X-only source](../structural-warnings/tablet.report.json) and its
  [D1 companion](../structural-warnings/tablet.annotation.json).
- [Historical prediction report](../../benchmarks/alpha17/tablet-pilot-summary.json)
  and its [D3 companion](../comparison/tablet.annotation.json).

The first case explains batch/geometry correspondence with weak cluster agreement,
future-batch conditions and missing physical/reference information. The second
keeps calibration errors, null definitions, evaluation matching and stronger
claims separate. Shared tablet names are not a population crosswalk: the cases
remain distinct. One declared canonical dataset identity and one X view come from
D1; the predictive case retains its original D3 context without a name-based join.
Two cases/source reports are not two independent studies. Original-database and
independent-study counts remain unknown. No model, PCA, clustering or new data is
needed. The example checks that every source file remains byte-identical.

See the [API](../../STANDALONE_REPORT_API.md). The broader private Research example
tests eight existing canonical datasets (seven NIR and one MIR outgroup), native
Preflight compatibility and explicitly labelled synthetic counterexamples.
