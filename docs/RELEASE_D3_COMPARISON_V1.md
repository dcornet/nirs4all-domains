# D3 comparison interpretation v1

Bridge `0.1.0a21`, protocol `domains.comparison_interpretation.v1`.
The [API/CLI](COMPARISON_INTERPRETATION_API.md) interprets existing predictive
comparisons without fitting another model. A strict optional companion binds
both reports and evaluation pointers, distinguishes target/units compatibility,
ID matching, model/pipeline and training conditions, null definitions and
baseline skill, and retains separate deployment/support interpretations.
Historical numerical results, schemas, sources and consumers are unchanged.
The existing `comparison.ridge_on_frozen_folds` API remains intact; the new module
is `comparison_interpretation` and imports no numerical provider.

The [worked public tablet example](examples/comparison/README.md) compares
original Type C and Type A raw PLS results. Absolute errors use compatible
units, but populations and nulls differ, so the contrast is unmatched and the
skill definitions stay separate. An RMSE gap does not isolate a split effect.
No new raw source, prediction, PCA/hierarchy fit, bank campaign, statistical test
or scientific mechanism claim is added. Existing native synthetic regression
tests retain their own fitted-fixture scope.

Qualification: local format, Clippy (`-D warnings`), six Rust workspace and 30
native ignored gates pass. Full Python regression passed **446 tests**, followed
by **36 current focused D3 tests** including the final unavailable-identity
adversaries and input-alias protection. The final hosted suite includes 448
Python tests. Alpha.9–18 JSON checks, public replay, research continuity and
wheel/sdist parity (new module/schema and legacy comparison module) pass.
An initial local regression lacked the existing optional FastAOM runtime on its
search path; the corrected run used the established local runtime and passed.
No test or historical receipt was relaxed. See the [audit](audit/d3-comparison-v1-review.json).

D1 integration: [PR #1](https://github.com/dcornet/nirs4all-domains/pull/1)
targets main and remains open for owner-controlled merge. Actual remote D1 head
is `93c503b1298e3cddea6f495730307d8d932f6acd`; main remains
`378dc4ca752c3ab3e60f2514da1bdfa062e9a7da`. D1 Windows/Ubuntu
[CI 41030197917](https://github.com/dcornet/nirs4all-domains/actions/runs/41030197917)
passed at that exact head. Review found no known compatibility blocker;
observation support still does not establish independent units or resampling
robustness. D3 is delivered separately on `feat/d3-comparison-interpretation`,
based on D1, with its own
[Windows/Ubuntu Actions](https://github.com/dcornet/nirs4all-domains/actions?query=branch%3Afeat%2Fd3-comparison-interpretation).
The delivery message records the exact completed final-head CI run; workflow
configuration alone is not execution evidence. Neither feature is merged here.

Resources after local validation, before Git/hosted delivery:
**19,442,624,622 bytes** combined, **2,379,615 bytes** above the initial
19,440,245,007 measurement. Engineering bound: 512 MiB. Workspace ceiling:
20,289,597,121 bytes; campaign reservations: 1,801,584,082 of 1,805,306,368.
**Ceiling increases: 0 bytes. New campaign reservations: 0 bytes.**
The shared journal is unchanged; 2 GiB free per volume is preserved. No cleanup,
migration, upstream modification or research-repository edit was performed.

Limitations: semantic/provenance declarations are not authenticated; exact
strings need caller-curated equivalence. V1 handles RMSE and stored fractional
RMSE skill, not vector alignment, unit conversion or inferential statistics.
Positive skill establishes improvement over the stated null only; practical
usefulness and genuine independent transfer require further evidence. Unknown
physical dependencies and spectral support remain explicit.

Next D1–D5 priority: **D4**, integrate these optional companions into one
concrete report consumer without weakening binding or evidence-scope guards.
