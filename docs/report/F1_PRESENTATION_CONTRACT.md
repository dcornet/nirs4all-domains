# F1 presentation contract and execution bounds

One additive, deterministic `domains.report_presentation.v1` projection supplies
localized figure/table captions, values, exact evidence pointers, statuses,
original source text and conditional findings to the demo and three exports.
The scientific browser and standalone schemas remain unchanged. Legacy report
fields remain present; JSON gains optional presentation metadata only.

Before tests: a figure/table must reference the same carried object as its
explanation. PCA percentages use eigenvalue/full covariance trace, never a
truncated sum. A single component has a 1D display, no invented PC2. Missing
coordinates yield a reason, not points. Display arithmetic is limited to plotting,
formatting and declared counts; no scientific estimator/statistical algorithm.
Noise counts and recorded strengths are descriptive, never resampling stability.
No new grouping, priority threshold, preprocessing winner or risk score.

Every evidence link must resolve to the exact metric or warning observation;
otherwise show the missing reference explicitly. Original source prose remains
unaltered; localized explanations are separately labeled. Flattened scalar tables
state their bounded overview scope and retain the complete original object.
No raw-X curves, cells or spectra enter HTML/Markdown/JSON exports. Display-only
X stays local; detailed spectral figure export is deferred.

CommonMark escaping remains literal for untrusted prose, including punctuation,
indentation and fence adversaries. Original JSON remains in one independently
sized fence. HTML has restrictive CSP, no executable script/external resource,
escaped strings, semantic tables/SVG, accessible disclosure and print expansion.
Numeric formatting distinguishes null/zero and retains round-trip original values.

Resources: no new scientific reservation or ceiling increase. Reuse installed
dependencies and compiled WASM; no local Rust/kernel build. Bound additional local
engineering files to 16 MiB, essential local receipts/screenshots to 4 MiB;
prefer CI artifacts for large previews, PDFs and captures. Maintain 2 GiB free
per volume and current cumulative ceilings. Synthetic browser tests only;
historical Research results and original ledger bytes must remain exact.

Expected adversaries include 1D/missing PCA, all-noise/unavailable density,
unknown units/intent, crossed/uncertified factors, partial readiness, absent D3,
broken evidence links, stale annotations, hostile HTML/Markdown, long strings,
zero/null/extreme numbers, retained test partitions and raw-X disclosure.
