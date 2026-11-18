# Browser capability boundary

## F4.1 factor association (separate protocol)

`domains.browser_factor_association.v1` consumes original, scope-validated raw-PCA
scores and explicitly selected keyed M. It never fits PCA or accepts X/Y values.
Train is the main population; unpartitioned and separately consented transductive
analyses retain their own source evidence. Existing `browser_x.v1` metadata slots
and historical qualification remain unchanged.

Methods 1.3.13 / ABI 2.20 provides categorical factor association, explicit
Pearson/Spearman, exact tests, Holm and continuous range summary. Descriptive B=0
is the default, with unavailable p-values. Exact inference is conditional on a
supplied external exchangeability record and complete prospective family;
repeated units and unsupported designs do not gain inference. Four direct
published-Methods WASM adapter checks executed locally. Actual compiled Domains
native/WASM qualification and Chromium/Firefox executed on Windows and Ubuntu;
the [F4.1 execution record](browser/F4_1_VALIDATION.md) identifies the source
commits, current-head gates, artifacts, numerical checks and limits. Listing an
API is not execution proof. No global spectral association, causal or calibration
score is implemented. Optional external design records attach separately after
PCA; shape validation does not establish their scientific truth.
See [remaining capabilities](browser/F4_1_REMAINING_CAPABILITIES.md).

## Earlier protocol surfaces

This matrix describes the current demo product surface, not a scientific
qualification grant. A provider API, implemented path, and qualified scientific
interpretation are separate evidence. Runtime results retain their own status,
reason and value fields. F4.0 source implementation is not a completed browser,
native/WASM, or CI verification. The schema and detailed import boundary are described
in the [F4.0 import architecture](browser/F4_0_IMPORT_ARCHITECTURE.md),
[native/WASM compatibility](browser/F4_0_NATIVE_WASM_COMPATIBILITY.md), and
[remaining capability notes](browser/F4_0_REMAINING_CAPABILITIES.md).

| Capability | Current status | Evidence boundary |
|---|---|---|
| Reviewed local X/Y/M import | `implemented_pending_verification` | IO/Formats assemble user-reviewed Dataset Builder roles, explicit keys and declared partitions. Nullable X/Y/M, axes, and source identities are retained locally. Import does not fit or create a scientific request. |
| Train structure | `implemented_pending_verification` | The explicit Train structure action fits only the declared train population. Unpartitioned data use the separate legacy full-source descriptive route. |
| Raw-space nearest-neighbor test query | `implemented_pending_verification` | Declared train rows are the reference and test rows are the query; matching declared exclusions apply when supplied. This is raw-space support, not a transfer or deployment claim. |
| Metadata factor audit | `implemented_pending_verification` | Reports counts, missingness, cardinality, and levels. Cross-partition audit also reports literal shared nonmissing values. No statistical association is calculated. |
| Metadata coloring of PCA points | `presentation_only_pending_verification` | A selected eligible M field maps to existing PCA points by technical row key. It does not calculate association or alter PCA coordinates/evidence. |
| Explicit global descriptive structure | `implemented_pending_verification` | Requires explicit transductive consent and fits train plus test. Predict rows are excluded. No Y enters the scientific request. |
| Exact spectra / declared identity audits | `implemented_pending_verification` | Separate integrity operations use the selected X or declared identity fields; a negative audit does not certify independence. |
| Methods factor-association APIs | `owner_api_declared_unqualified` | Methods declares factor-target and numeric-vector association functions, but no scoped metadata association protocol or exchangeability qualification is established here. |
| Train-fitted PCA test projection | `not_qualified` | Methods has a generic `FlexiblePCA.fit`/`transform` API; the browser train-fit state handoff and separate test projection protocol are not qualified. |
| D1-D6.1 saved companion reading | `saved_evidence_only` | Reads the packaged public tablet report and exact saved companions; performs no new fit or recomputation. |
| Physical specimen / reference independence | `not_established` | Observation IDs, technical keys, groups, and a negative duplicate check do not prove physical or reference independence. |
| Predictive performance, transfer, causal attribution | `not_implemented` | No target is passed into a scientific request and no predictive fit, transfer test, or causal design is added. |
| Resampling robustness / SNV paired analysis | `not_qualified` | These require separate scoped protocols, admissible units and qualification; no local substitute algorithm is used. |

The legacy browser runtime's existing Methods provider capabilities include
PCA, summary, nearest neighbors, and HDBSCAN. The scoped F4.0 bridge uses the
same declared provider boundary. Capability presence is distinct from
qualification. Unsupported provider calls, budget refusal, numerical errors,
zero variance, and malformed responses retain explicit unavailable/error
states and null values.

The live protocol does not perform full D1 parity, D2 validation-intent
annotation, D3 predictive comparison, D4 standalone companion validation, D5
utility analysis, D6 verification readiness, or D6.1 decision summary. Those
remain saved-evidence consumers where an exact compatible public companion is
provided; the tablet example packages its D1-D6.1 public reading and shows
unknown physical independence. It is not regenerated from live data. Existing
standalone examples under [`examples/standalone`](examples/standalone/README.md)
retain separate source reports and companions rather than joining by a shared
dataset name.

## Current scoped import and operations

Import requires Dataset Builder review of source/column roles, identity keys,
joins and partitions. It preserves the reviewed dataset, including Y in local
import memory, but does not fit automatically. Y is excluded from exported
reports and worker scientific requests. Each selected audit or analysis
constructs its own row and field grant; no operation inherits an implicit
global train/test fit.

Partitioned data remain available after import. Train structure uses train rows
only. Test support uses train rows as the raw-space reference and test rows as
the query. Metadata audits use documentary counts and literal overlap. Explicit
global descriptive analysis uses train plus test only after consent and excludes
predict rows. An unpartitioned dataset continues through the legacy full-source
descriptive path. Missing cells remain marked; operations requiring complete X
can be unavailable rather than silently imputing or dropping rows.

Limits: 32 MiB serialized request, 2,000 observations, 1,000,000 spectral
cells, and 25,000,000 products per bounded kernel. Work above a limit is
unavailable rather than subsampled. Density uses one fixed setting; there is
no parameter search or resampling fallback. Membership strength is not a
probability, a cluster is not a biological batch, and no cluster is not proof
of low risk. Readiness is declaration-only and never indicates execution.

### Legacy history: browser_x.v1 partition refusal

The original browser_x.v1 route accepted one complete dense X source and
refused IO-declared test/prediction populations before its full-source fit. That
partition safety amendment remains applicable to the legacy API and is
documented in [WASM_PARTITION_GUARD.md](WASM_PARTITION_GUARD.md). It is not the
current F4 reviewed-import behavior.
