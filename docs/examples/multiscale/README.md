# Within-fit persistence: public synthetic example

This example uses the existing published Methods separated-blobs fixture
(120 observations, two original coordinates). It is synthetic geometric
qualification, not a real specimen/biological benchmark. The existing native
hierarchy-profile path applies centered PCA, then the frozen EOM setting with
`min_cluster_size=8`, self-counting `min_samples=4`, no single-root selection.
The single 8/4 configuration is fixed in advance, without representation or
parameter search. The sidecar describes that one fit.

[Machine-readable descriptor](descriptor.json), [readable interpretation](descriptor.md),
and [original source report/tree](source-report.json) are retained together.

Three selected branches each have 40 assigned observations. Within-fit
persistences are approximately 0.684723, 0.634746 and 0.553886. Noise fraction
is zero. These numbers describe this density fit and representation only.
No independent-unit count, resampling robustness, biological organization,
harmful reliance or predictive generalization is inferred.

Reinterpret the already fitted report without another numerical fit:

```shell
python -m nirs4all_domains.multiscale docs/examples/multiscale/source-report.json --out results/branches.json
```

To reproduce the native-to-Domains transport on the bounded synthetic fixture:

```shell
python scripts/run_multiscale_example.py --binary target/debug/n4domains --library PATH_TO_PUBLISHED_METHODS_LIBRARY --out results/multiscale-example
```

Use `target/debug/n4domains.exe` on Windows, or set `N4DOMAINS_BIN` and
`N4DOMAINS_METHODS_LIBRARY`. This optional regeneration costs one PCA and one
HDBSCAN call, no Y/model. Provider binary hashes differ by platform; the
committed example records its actual Windows provider. Raw condensed evidence
is preserved without exporting redundant PCA score transport.
[Meaning, states and API](../../SELECTED_BRANCH_PERSISTENCE.md).
