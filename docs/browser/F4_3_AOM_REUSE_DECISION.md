# F4.3 AOM reuse decision

## Decision

F4.3 will use a small, versioned, declarative candidate catalog informed by
`nirs4all-aom`. The catalog reuses an ordered subset of AOM's
`compact_no_fd_gaussian` operator bank and its Raw, SNV, and MSC base names.
It does not depend on or execute the AOM Python package. A compatibility
adapter must resolve supported catalog entries to the public Methods 1.3.13
WASM APIs; Methods remains the owner of all numerical transformations.

The catalog also names Methods-owned StandardScale and Normalize candidates.
An optional Crop candidate remains disabled until the protocol declares its
axis interval, units, and boundary behavior. Each candidate is an explicit
representation choice. This catalog does not create the Cartesian product of
all operators or imply that every pair forms a valid chain.

No algebraic shortcut is enabled. The catalog does not select preprocessing
from Y. A future supervised selector that uses Y_train requires a separately
versioned protocol; it must never read Y_test. There is no fitting on retained
test data.

## Pinned source and provenance

The GitHub repository metadata reports `main` as the default branch. The latest
commit from the GitHub commits API at audit time was
[`157954dc8c4fbf06e45ed7b421b8a02b007d8331`](https://github.com/GBeurier/nirs4all-aom/commit/157954dc8c4fbf06e45ed7b421b8a02b007d8331)
(`fix(demo): pin the qualified Methods runtime`, 2026-11-09). Catalog
provenance is pinned to this immutable commit, not a moving branch.

Relevant source files and Git blob identifiers at that commit:

| Source | Reuse | Git blob |
| --- | --- | --- |
| [`aom_nirs/pls/banks.py`](https://github.com/GBeurier/nirs4all-aom/blob/157954dc8c4fbf06e45ed7b421b8a02b007d8331/aom_nirs/pls/banks.py#L41-L80) | Ordered `compact_no_fd` list and its `compact_no_fd_gaussian` extension. | `91c4261413c8ec796608e7332f481a1d8bfd100c` |
| [`aom_nirs/fast/bases.py`](https://github.com/GBeurier/nirs4all-aom/blob/157954dc8c4fbf06e45ed7b421b8a02b007d8331/aom_nirs/fast/bases.py#L66-L167) | Raw, SNV, and MSC base descriptors. `build_base_bank` includes these at lines 410–450. | `5adf268b3e04d1200d9f3fae9ef5248554dbb5e4` |
| [`LICENSING.md`](https://github.com/GBeurier/nirs4all-aom/blob/157954dc8c4fbf06e45ed7b421b8a02b007d8331/LICENSING.md) | Declares `CeCILL-2.1 OR AGPL-3.0-or-later`. | `9014e3374b1114df03c224a7e7da55f087902b0e` |
| [`demo/wasm/n4m/version.json`](https://github.com/GBeurier/nirs4all-aom/blob/157954dc8c4fbf06e45ed7b421b8a02b007d8331/demo/wasm/n4m/version.json) | Records the staged Methods package, archive integrity, and asset hashes. | `c0c4d4656ca792fd917cdfde9fec20d249a97f21` |

The pinned browser bundle records `@nirs4all/methods` 1.0.18. It is not the
Methods 1.3.13 runtime required by this project and is not used as compatibility
or execution evidence. Copying AOM code or importing its engine is outside this
decision. If descriptor text or expressive metadata is adapted, retain source
attribution and the applicable license notice and terms; keep the source pin
and blob identifiers in the catalog provenance.

## Initial catalog proposal

The AOM bank's relative order is preserved within the selected operator subset:
SG smoothing, SG first derivative, SG second derivative, detrend degree 1,
detrend degree 2, then Gaussian smoothing. Raw, SNV, and MSC are AOM base
families rather than members of that linear operator bank. The panel order
below groups these base families first for readability.

| Order | ID | Descriptor | Provenance and constraints |
| ---: | --- | --- | --- |
| 1 | `raw` | `{ "kind": "raw" }` | AOM `RawBase`; Methods adapter required. |
| 2 | `snv` | `{ "kind": "snv" }` | AOM `SNVBase`; use Methods semantics and defaults explicitly. |
| 3 | `msc` | `{ "kind": "msc" }` | AOM `MSCBase`; fit its reference using training X only and replay that state on retained rows. |
| 4 | `sg_smooth_11_2` | `{ "kind": "savitzky_golay", "window_length": 11, "polyorder": 2, "deriv": 0 }` | Exact AOM bank parameters. |
| 5 | `sg_d1_11_2` | `{ "kind": "savitzky_golay", "window_length": 11, "polyorder": 2, "deriv": 1 }` | Exact AOM bank parameters. |
| 6 | `sg_d2_11_2` | `{ "kind": "savitzky_golay", "window_length": 11, "polyorder": 2, "deriv": 2 }` | Exact AOM bank parameters. |
| 7 | `detrend_1` | `{ "kind": "detrend_projection", "degree": 1 }` | Exact AOM bank parameter. |
| 8 | `detrend_2` | `{ "kind": "detrend_projection", "degree": 2 }` | Exact AOM bank parameter. |
| 9 | `gaussian_smooth_1` | `{ "kind": "gaussian", "sigma": 1.0, "order": 0 }` | Exact AOM bank parameters. |
| 10 | `standard_scale` | `{ "kind": "standard_scale" }` | Additional Methods-owned family; executable only after every Methods parameter and fit scope is specified. |
| 11 | `normalize` | `{ "kind": "normalize" }` | Additional Methods-owned family; executable only after norm, axis, and zero-vector behavior are specified. |
| 12 | `crop` | `{ "kind": "crop", "lower": null, "upper": null }` | Optional, disabled placeholder. No candidate is executable until bounds, units, axis selection, and empty/edge behavior are declared. |

The selected AOM operator entries retain their exact bank parameters but do
not inherit an assumed numerical implementation. In particular, AOM documents
its strict-linear operators as zero-padded. The Methods adapter must explicitly
set every available Methods boundary parameter. It must refuse or report an
entry unavailable if Methods cannot express its required semantics. A matching
name or parameter tuple does not establish numerical equivalence. No AOM-to-
Methods parity claim is made here.

## Catalog record and execution boundary

The checked-in catalog should have its own schema and version, and store for
each candidate: stable ID and order; family and complete parameters; whether
the descriptor is AOM-derived or Methods-owned; source repository, pinned
commit, file, and blob where applicable; Methods API/ABI binding; fit scope;
axis and boundary requirements; and an explicit executable/unavailable
reason. Unknown parameters and unsupported operators fail closed. Runtime
results must identify the resolved Methods version and descriptor fingerprint.

For data-fitted transforms, fit state is derived from the declared training
population only. Preserve original axes and references. Do not sort, resample,
impute, or silently crop data to make an operator fit. A panel candidate is not
a scientifically qualified method merely because a Methods API can execute it.

## Sequential-prefix cache qualification

AOM has an exact transformed-training cache keyed by `(base_index,
chain.signature)` with LRU eviction, plus a cache of each transformed test base.
It caches a complete candidate chain, not shared operator prefixes; see
[`hard_aom_chain_pls_ridge.py`](https://github.com/GBeurier/nirs4all-aom/blob/157954dc8c4fbf06e45ed7b421b8a02b007d8331/aom_nirs/fast/models/hard_aom_chain_pls_ridge.py#L57-L65)
and [lines 97–119](https://github.com/GBeurier/nirs4all-aom/blob/157954dc8c4fbf06e45ed7b421b8a02b007d8331/aom_nirs/fast/models/hard_aom_chain_pls_ridge.py#L97-L119), blob
`049ead623bf3c4f67eaeeaa2f087d1c72de15abb`.

Domains may qualify a separate optimization that reuses exact intermediate
outputs and fitted states for identical prefixes while invoking Methods'
ordinary sequential APIs. It is contingent on Methods 1.3.13 exposing a public
state/transform path and on selected candidates actually sharing prefixes. It
does not combine operators, alter array axes, or substitute an algebraic
kernel. Cache keys must bind the input content and axis fingerprints, split or
fold, Methods version/ABI, ordered descriptor parameters, and fitted-state
fingerprint. Fit a prefix only on its declared training data; apply the frozen
state to retained rows. Never reuse fitted state across different training
scopes.

Before enabling the cache, specify expected behavior and tolerances, then
compare cached and uncached sequential Methods outputs and final results on
adversarial fixtures, including different input contents under identical
labels, changed axes, boundary cases, and fit-scope changes. Record numerical
differences, transform-call counts, measured end-to-end timing, peak cache
memory, and eviction/cleanup behavior. Claim an acceleration only when the
measured run shows it. No speed claim follows from AOM's cache implementation.

## Deferred work

Any Y_train-based preprocessing selection is a separate future protocol with
explicit selection data, folds, leakage adversaries, and versioning. It is not
part of this F4.3 descriptive panel, and Y_test is never available to it.

A future upstream proposal may request a versioned machine-readable AOM bank
and chain-descriptor export containing stable IDs, exact parameters, grammar,
boundary semantics, and license/provenance metadata. This document records a
proposal only; it does not modify AOM or create an upstream issue.
