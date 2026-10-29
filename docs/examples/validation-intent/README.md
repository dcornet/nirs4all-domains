# Worked example: existing public tablet pilot

Source: [alpha.17 tablet pilot summary](../../benchmarks/alpha17/tablet-pilot-summary.json),
with its [frozen design](../../ALPHA17_TABLET_PILOT_PLAN.md) and
[results](../../ALPHA17_TABLET_PILOT_RESULTS.md). This example references existing
source-permitted aggregates; no raw values, model fitting or PCA are added.

Run from the repository root after installing `./bridges/python`:

```shell
python -m nirs4all_domains.validation_intent docs/benchmarks/alpha17/tablet-pilot-summary.json --intent docs/examples/validation-intent/tablet.request.json --out results/tablet-intent.json
```

The checked-in [request](tablet.request.json), [annotation](tablet.annotation.json)
and [rendered interpretation](tablet.annotation.md) reproduce the same result.
The request describes the declared four-Type nested evaluation. It names Type
as a source category, with canonical blocks nested inside it. Physical specimen
and assay independence are unknown. The report's pooled PLS/Ridge RMSE states
are referenced unchanged. Existing train-fitted PC1/PC2 summaries have a fold
reference; continuous support remains unavailable.

The reading supports a descriptive score for those observed held-out Type
contexts. It does not establish a new genotype, new instrument, independent
experiment, future unseen population or a causal shortcut. It retains the
source limitation that pooled results conceal context variation. Neither model
is refitted, retuned, selected or recommended.

Integration tests reproduce the JSON/Markdown, validate its content binding and
check that the historical source bytes and numerical evidence stay unchanged.
