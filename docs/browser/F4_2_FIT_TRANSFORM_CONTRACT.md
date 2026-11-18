# F4.2 fit and transform transport

The additive request contains `schema_version=1`,
`protocol_version=domains.browser_train_fitted_support.v1`, `fit=train`, an
unchanged F4.0 `scope` envelope, explicit `parameters` (`n_components`,
`monitoring`, `max_components`, `n_folds`, `alpha`), documentary `dependencies`,
their exact `dependency_fields` grant and nullable `external_limit_plan`.
Rust closes every population and grant before any numerical provider call.

The owner callback operations are `pca_fit`, `pca_transform`, `pca_destroy`,
`summary` and `pca_monitor`. Fit sees only train. Transform sees train and then
test in separate calls. The actual serialized state returned after fit and each
transform is checked inside Rust, hashed and discarded from the public result.
Only train-derived component summaries decide which nonconstant coordinates can
be displayed. Test output never chooses a dimension, representation or parameter.

`projection` and `monitoring` independently use status/reason/value records.
An unavailable operation has a null value and exact reason. Projection preserves
both score matrices and keys, returned width, display-coordinate indices, owner
train summaries and actual state fingerprint. Variance/rank-resolution omissions
remain explicit. Monitoring preserves its own eigenvalues, effective dimension,
OOF reference statistics, monitored statistics, counts, empirical limits,
centroid diagnostics, total variances and numerical tolerances.

The fit identity binds dataset/source/content, original axis/unit, ordered train
keys, train spectra, explicit parameters and provider version. Query identity
is separate. F4.1 preflightPca provenance is never reused for this new fit.
Monitoring is separately identified by its full input/parameters/provider and
indexed-fold protocol; it is not a serialization of the FlexiblePCA handle.

Handles stay inside the operation's provider lifetime. Failed fits do not cause
a transform; failed transformations do not fabricate scores. Cleanup runs even
when provider data are invalid. Browser workers are terminated after completion,
timeout or cancellation; request/epoch guards discard stale responses.
