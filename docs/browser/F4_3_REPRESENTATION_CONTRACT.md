# F4.3 representation contract

Protocol `domains.browser_preprocessing_sensitivity.v1` treats each requested
preprocessed matrix as a named derived spectral source. It preserves the parent
dataset/source/content identity, ordered acquisition keys, and original axis
lineage. It does not replace or relabel F4.0–F4.2 evidence. The execution owner
is Methods 1.3.13 / ABI 2.20; the AOM catalog supplies candidate descriptors,
not numerical kernels or an equivalence claim.

## Frozen plan

The public request and result types are declared in
[`bindings/wasm/preprocessing.d.ts`](../../bindings/wasm/preprocessing.d.ts),
with strict DTO schemas in
[`preprocessing-input.schema.json`](../../bindings/wasm/preprocessing-input.schema.json)
and [`preprocessing-result.schema.json`](../../bindings/wasm/preprocessing-result.schema.json).
The current versioned descriptor catalog is
[`aom-bank.json`](../../bindings/wasm/aom-bank.json), bank ID
`aom_methods_balanced_v1`. The prospective plan binds the ordered
representations, effective per-step parameters, diagnostic toggles, correlation
method, and support parameters. Selected factor IDs are transported separately
as M columns and are bound into the reference-input fingerprint. Raw is
required first; the current bounds are 16 representations and three steps per
representation. A changed plan after a computed reference result is represented as an
`exploratory_revision` with its parent plan hash.

The initial fixed panel contains raw, SNV, MSC, SG smoothing and first/second
derivatives, linear detrend, Gaussian smoothing, StandardScale, Normalize, and
two declared SNV→SG chains. Quadratic detrend and a fixed explicit crop are
catalog alternatives, not default entries. Defaults and complete parameters
must be read from the bank rather than inferred from these family names.
SG `delta=1` is in feature-index coordinates. A crop is a half-open original
column interval; its returned axis is the matching original slice. No
intersection, sorting, resampling, imputation, or automatic range alignment is
performed.

## Execution and lineage

Each non-raw step uses Methods' public estimator create/validate/fit,
export-state, transform, and destroy lifecycle through the bounded provider.
Reference fitting uses only the declared train rows (or all rows for a fully
unpartitioned descriptive source). The result records each step's operator and
parameters, provider version, reference-only fit role, state fingerprint,
reference input/output fingerprints, input/output axis fingerprints and band
counts, and whether state bytes were unchanged after transform.

Every representation result is either `computed` with a value or `unavailable`
with a reason and null value. A provider, budget, parameter, or shape failure
must remain explicit; it does not silently substitute a different operation.
The top-level computed result carries the frozen plan and hashes for the plan,
reference input, full request, and evidence. The receipt records provider,
ordered reference/query keys, test-X access, `y_accessed:false`,
`x_predict_accessed:false`, provider calls, cache settings/hits, catalog hash,
AOM source provenance, and the frozen reference evidence hash when present.
No raw X array or serialized estimator state is part of the public result.

## Derived-source interpretation

Downstream diagnostics run separately on each derived source with that source's
own axis, matrix and content identity. An inner `raw` label means raw relative
to that derived source. It does not mean the original untransformed source.
Preserve original-source reports and all requested representation outcomes.
Transformations describe sensitivity of the selected diagnostics to the
specified panel; they do not identify a preferred representation or establish
chemical relevance, physical independence, prediction quality, or causality.

## Evidence status

This contract documents the checked-in API and protocol. It is not an execution
or scientific-qualification result. See
[`F4_3_REMAINING_CAPABILITIES.md`](F4_3_REMAINING_CAPABILITIES.md) for the
specific evidence still needed; the separate F4.3 validation record owns actual
test and browser outcomes.
