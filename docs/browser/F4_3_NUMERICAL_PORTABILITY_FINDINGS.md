# F4.3 numerical portability findings — partial, not qualified

Recorded on 2026-11-18 with Methods **1.3.13+abi.2.20.0**. The frozen tolerance
remains **absolute 1e-10 plus relative 1e-10**. The panel, component-resolution
rules and factor statistics have not been changed to obtain a passing result.

Both actual runtimes completed **35 synthetic computational requests and 20
refusals before provider access**. The native replay uses each backend's own
earlier frozen reference result; it changes no original X, M, axis, key, plan
or parent-source identity. This establishes execution and access evidence.
It does **not** establish complete numerical portability: **F4.3 remains a
partial draft and the full parity gate remains failed**.

## Observed blocker

The independent [diagnostic companion](../../scripts/diagnose_preprocessing_portability.py)
found **144 scalar-field failures in 27 cases and 43 representation/component
pairs**. These comprise **51 factor estimates** (35 temperature correlations
and 16 instrument eta-squared values) and **93 owner-output fields**. The latter
include repeated correlation coefficients and F statistics; 144 is a field
count, not 144 independent scientific effects.

All these failures concern components whose eigenvalues are **not degenerate
under the frozen eigenvalue-gap comparison**. They cannot be waived as rotations
inside a degenerate eigenspace. Representative sign-aligned differences:

| Case / representation / component | Quantity | WASM | Native | Absolute difference |
|---|---|---:|---:|---:|
| Low frequency / SNV / PC5 | Temperature correlation | -0.15041766432532225 | -0.15042292654356995 | 5.2622182477e-6 |
| Low frequency / MSC / PC4 | Temperature correlation | -0.22072746907682764 | -0.22072858503757173 | 1.1159607441e-6 |
| Low frequency / SNV / PC5 | Instrument eta-squared | 0.002066658221955729 | 0.002066966471454332 | 3.0824949860e-7 |

The first example has a small resolved eigenvalue, approximately **1.365e-10**.
Its maximum score magnitude is approximately **2.773e-5**, while the largest
sign-aligned native/WASM coordinate difference is approximately **7.577e-10**.
Small absolute score perturbations can be large relative to a weak component
and can affect its factor statistics. This is an observed conditioning concern,
not a new numerical-rank threshold or proof that a particular owner kernel is
incorrect. Attribution requires controlled same-input owner tests.

## What the diagnostic did and did not find

At the unchanged tolerance, the examined published subtrees showed no
differences in PCA eigenvalues/resolved counts/full moments/score Gram geometry,
density partitions by observation identity and their membership/persistence,
neighbor summaries and identity retention, ARI/Jaccard evidence, or the separate
F4.2 combined projection geometry and T²/Q vectors/counts. These observations
are diagnostic findings, **not individual gate-pass certificates**.

Five extra signed-coordinate comparisons exceeded the tolerance. Coordinate
identity is stronger than the frozen primary PCA contract, which uses geometry,
eigenvalues and rank. Those coordinate differences remain recorded as diagnostics.
The nondegenerate factor-statistic differences above remain genuine failures
under their own strict scalar comparisons. Historical F4.1 same-score tests are
retained; their tolerance and interpretation were not loosened.

The diagnostic first validates all **35** original-input bindings, plan/reference
hashes, backend-own frozen ancestors and canonical result hashes. Each case now
also retains the exact raw Rust result JSON from the **same numerical call**,
its byte SHA-256, and semantic agreement with the parsed result. This preserves
float lexical/signed-zero evidence for later auditing without an extra fit.

Legacy serialized hashes and hidden preprocessing/model-state hashes require
separate treatment. Their byte equality across backends is not claimed. No
broad hash exemption was accepted: a proposed exclusion refactor was rejected
by automatic review and remains inert review evidence. The active checker is
fail-closed pending a narrower review; legacy opaque hashes are explicitly
unverified, not counted as passing. Resolving serialization bookkeeping would
not resolve the numerical factor-statistic failures.

## Retained actual evidence

The following large synthetic artifacts remain ignored and are not committed:

| Artifact under `demo/test-results/` | Bytes | SHA-256 |
|---|---:|---|
| `preprocessing-wasm-raw-json.json` | 82,630,870 | `295729f134798353128e516ec367e8a6028c795c3912fa388fb4f3970307557f` |
| `preprocessing-native-raw-json.json` | 86,442,341 | `5593e85e6daf0a85f743019ede8c9c09e47bbe8d48cf4349159abd5342fa67f9` |
| `preprocessing-portable-outputs.json` | 75,913 | `e238f40d162d4dca8287166bff3d1855ed3144586d1a7974c2df4cb56696ef0d` |

Reproduce the diagnostic with the existing artifacts:

```console
python scripts/diagnose_preprocessing_portability.py --wasm demo/test-results/preprocessing-wasm-raw-json.json --native demo/test-results/preprocessing-native-raw-json.json --out NEW_DIAGNOSTIC.json
```

It exits **1** for these observed numerical differences and writes
`DIAGNOSTIC_ONLY_NOT_A_PARITY_GATE`, never a parity-pass result. Source-binding
failure aborts before numerical enumeration. Failed runs, earlier artifacts,
native binaries and logs remain retained. The native summary transport defect
(floating JSON count rejected by an integer DTO) was corrected by routing to
the existing typed public summary provider; the numerical kernel was unchanged.

Five lightweight parity adversaries and five strict schema tests pass. The
adversaries reject changed Gram geometry/rank, wrong factor estimates or statuses,
source/key/M/protocol mutations and changed partitions, while accepting an
appropriate PCA sign flip with correctly aligned correlation. This does not
replace the failed full numerical qualification.

## Bounded read-only Methods proposal

No upstream repository, issue or scientific result was changed. The proposed
owner investigation is confined to the existing generic PCA/statistics seams:

1. Freeze one small **synthetic** low-frequency/SNV reference matrix from this
   declared panel, with ordered identities, exact bytes and parameters. Compare
   the complete preprocessing path first, then feed the **same frozen derived
   matrix** to native and WASM `preflightPca`. This separates preprocessing
   perturbation from PCA implementation differences without claiming that
   separate derived sources are identical.
2. Retain eigenvalues, resolution/unresolved flags, scores and their geometry.
   Investigate weak-component eigenpair residuals and conditioning in Methods.
   Reuse the official correlation/eta-squared APIs on the **same frozen score
   vectors** to separate statistical-kernel agreement from changing PCA inputs.
3. If the owner can supply justified eigenpair/coordinate accuracy or conditioning
   evidence, expose it through a public, versioned Methods interface and qualify
   its ABI, bindings and native/WASM execution separately. Domains must not copy
   a solver, invent an eigenvalue cutoff, change rank flags, substitute a score,
   relax the tolerance or remove unfavorable representations.
4. Acceptance must retain the fixed input/axis/identity and leakage adversaries,
   nondegenerate weak components, degenerate subspaces, original per-PC statistics
   and the **1e-10** comparisons for every quantity actually claimed portable.
   A later change to admissibility or protocol interpretation requires its own
   prospective version and expected behavior; it cannot rebless this evidence.

There were **zero new real-data fits or scientific reservations**, no Research
experiment, no Y access, no retained-test fit and no upstream edit in this work.
