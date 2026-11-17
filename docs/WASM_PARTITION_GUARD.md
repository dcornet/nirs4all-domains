# Browser import: retained-partition and scoped-operation behavior

Current F4.0 import uses the shared Dataset Builder for explicit source, column,
identity-key, join, and partition review. IO/Formats assemble the reviewed
dataset with original partitions and missingness; import performs no scientific
fit. Y may remain in the main import state for inventory and masking, but it is
not included in a worker scientific request or report export.

Partition labels govern each later operation independently:

- **Train structure** fits declared train rows only. An unpartitioned dataset
  takes the separate legacy full-source descriptive route.
- **Raw support query** uses train rows as reference and test rows as query;
  PCA fit/transform projection remains unqualified.
- **Metadata audits** report documentary counts, cardinalities, level counts,
  missingness, and literal nonmissing overlap. They do not calculate statistical
  association.
- **Global descriptive structure** requires explicit transductive consent,
  includes train and test, and excludes predict rows.

Every operation requests its own population and field grant. There is no
automatic fit at import, and an operation refusal does not discard the imported
dataset. See [F4.0 data access policy](browser/F4_0_DATA_ACCESS_POLICY.md),
[import architecture](browser/F4_0_IMPORT_ARCHITECTURE.md), and
[remaining capability notes](browser/F4_0_REMAINING_CAPABILITIES.md).

## Legacy history: browser_x.v1 retained-partition safety amendment

Expected behavior before the partition adversary test: a declared retained/test
or prediction population must not enter the present full-source PCA fit. IO
preserves the declarations; Domains refuses this live route before a numerical
request. It must not silently remove those rows, relabel them as training, or
invent a train-fitted projection from an unsupported binding.

This corrects the initial demo plan's overly broad sentence about combining all
imported partitions in a descriptive fit. A complete unpartitioned X-only source
remains a descriptive/transductive population. A declared train/test dataset
requires a separately qualified train-fitted browser protocol; use existing saved
reports meanwhile. The native historical protocols remain unchanged.

The refusal is `PARTITIONED_IMPORT_REQUIRES_TRAIN_FITTED_BROWSER_PROTOCOL`.
Every original observation/axis remains in the input files; no scientific
subsampling, imputation, fit on retained X or comparison against retained Y occurs.
