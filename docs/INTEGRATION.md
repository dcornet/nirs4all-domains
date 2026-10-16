# Integration, dependencies and obstacles

Preflight crates are pinned to `=0.1.0-alpha.1`; Cargo.lock pins the remaining Rust
dependency graph. Methods is loaded through an explicit path, never a package
path hardcoded in a distributable manifest. Native version, ABI and SHA-256 are
recorded in the report. Python transport pins Datasets 0.3.11 as an optional extra,
and records its installed version when used. The installed 0.3.11 public getters
were executed on controlled synthetic canonical Parquet through a local `get()`
path. This qualifies the adapter seam, not acquisition of the real pilot
datasets. No numerical Python fallback exists.

For a new environment, install the bridge and Methods separately. The Windows
wheel has a companion `nirs4all_methods.libs` containing a renamed MSVC runtime;
the Python import registers that DLL directory, while a Rust process needs it in
PATH. `scripts/dev-env.ps1` handles this prepared workspace. Missing dependent DLLs
are a loader failure, not evidence that ABI symbols are absent. The loader checks
ABI >=2.18 and required symbols before any fit. ABI 2.19 alone does not activate
unimplemented Domains protocols.

The initial host had neither Cargo nor a C linker in PATH. An isolated toolchain
was installed under ignored `.tools`, plus a venv under `.venv`; no system PATH or
global Git configuration was changed. These local tools are conveniences, not
package dependencies. Normal Windows MSVC Rust plus installed build tools is
supported by the source layout but not locally exercised here. Native Linux CI
is configured; only an executed CI run can qualify that platform.

The bridge uses Datasets' public getters on one source. Metadata, Y and split
tables join on **sample_id** with duplicate keys rejected. The per-source X rows,
observation IDs and sample IDs are the same accessor contract; another source is
never concatenated. Missing/unknown split labels, version mismatches or unconfirmed
physical identities fail the task. `sample_identity_confirmed=true` records an
explicit assumption; it is not inferred from row count. A keyed identity table
can instead supply physical/reference/group/individual IDs and repeat types.
Alpha.3 additionally accepts `observation_identity_table` keyed by acquisition ID
for per-acquisition context/reference/repeat declarations. It carries instrument,
campaign, site, lot, reference status and unit without reading test target cells.
Missing requested target join IDs and duplicate acquisition IDs fail conversion.
Optional `representation: technical_mean` selects the qualified comparison policy.

Dataset access is optional and on demand. Acquisition, checksums and cache remain
in Datasets. Do not embed credentials in campaign files. Public `y()` returns a
whole frame, so storage-level test-label exclusion cannot be promised; only
algorithmic access/selection exclusion is implemented. Missing native splits are
not silently randomized. A separately authored experimental JSON task is supported;
the alpha.4 local pilot explicitly authors a separately named experimental
plot split, never a catalog native split. General automatic splitting is deferred.

The audited three candidates are in configs/pilot.yaml. Shootout X1 now runs through
a local raw reproduction described in REAL_DATA_PILOT.md. Its exact native mapping
is calibration=train, test=test, validation=exclude; target assay is mg/tablet.
`--catalog-root` selects that local catalog without embedding machine paths in
published packages. CORN has no native split
and manual/private access. Shootout declares original split but actual labels
require canonical bytes. UCPH exposes batch/replicate/scale metadata and marks
sample IDs unavailable; historical split terms alone are insufficient. No real
bytes or newly inferred groups/splits were committed. The pilot command records
the real task result plus each remaining task's unavailable reason and continues.

| Proposed upstream request | Appropriate owner | Acceptance before consumption |
|---|---|---|
| Retain PCA means/loadings or a fitted transform in Rust provider result | Preflight adapter, existing Methods C ABI sufficient | Train-only fit/transform test on held-out rows; no new eigensolver |
| Identity-only reference transport without numeric target access | Preflight contracts; Datasets partition-aware target access | Cross-test reference checks with Y_test inaccessible |
| Typed Rust adapters to HDBSCAN/ARI/noise/near duplicates/association | Preflight or Methods Rust binding | ABI 2.19 checks, public typed calls, real native fixtures and unavailable behavior |
| Repetition aggregation/context provenance | Preflight intrinsic protocol | Equal physical-sample weights; heterogeneous contexts/partition crossing refused |
| Generic Ward/GMM/MMD/energy/variance partitioning if broader audit confirms absence | Methods | Public ABI, publication, binding and reference parity before enabling Domains protocol |
| Group/nested probe execution seam | DAG-ML for execution, Preflight for generic intrinsic readiness | Inspect public phases/folds/OOF APIs; adversarial nested leakage fixtures; no local clone of CV engine |

No upstream repository was changed; these are documented requests, not posted
issues or claims of missing code across every possible ecosystem repository.
The limited requests actually encountered in alpha.3, including API shapes and
scientific gates, are in [UPSTREAM_DEPENDENCIES.md](UPSTREAM_DEPENDENCIES.md).

AGPL-3.0-or-later was explicitly selected by the user. Preflight manifests declare
`CECILL-2.1 OR AGPL-3.0-or-later`; Datasets declares the same alternatives. Methods
uses CeCILL-2.1 with third-party notices, including BSD-3 HDBSCAN code; native
libraries are not redistributed in this repository. A release bundling binaries
must include their actual notices/SBOM and validate its dependency closure. This
inventory does not claim legal review or authorization to redistribute datasets.

The initial GitHub checks found `gh` authenticated as dcornet and the requested
repository returned HTTP 404. Git was initialized on main and origin configured
locally; no commit or push was made during the initial implementation.

On 2026-10-16 the owner explicitly authorized the first commit and push. The
verified GitHub profile is Denis Cornet, login dcornet, numeric ID 5694013. Local
Git author configuration uses that name and the GitHub noreply address
`5694013+dcornet@users.noreply.github.com`; global Git configuration is unchanged.
The destination is created private unless the owner requests public visibility.

## Alpha.4 optional native workflow

Install `bridges/python[test,datasets,predictive]` for the EcoSIS qualification
runner. The predictive extra pins DAG-ML 0.3.41, Methods 1.3.6 and scikit-learn
1.7.2 (estimator façade base classes only). Numeric fit, selection, metrics and
means remain native. The selected Methods library must be the same explicit
binary as the one used by Python artifact replay. DAG-ML's published native
CV/SELECT/REFIT binding is consumed; its high-level strict terminal-predict API
does not yet provide this grouped workflow. See PREDICTIVE_SANITY_CHECK.md.

The EcoSIS runner uses original wavelength-indexed CSV and explicit relational
joins, then the public Datasets canonical writer/getters. It does not decode a
vendor format. Official source hashes and the derived local metadata descriptor
are checked before creating explicit experimental plot splits. Full 2151-band
input is retained by default. A declared `axis_stride` selects columns only and
records that operation; final qualification uses stride 1. No interpolation,
scaling, missing-target repair or acquisition deletion occurs.

`n4domains represent <task> --out <new.json>` exports the native-built comparison
view and dependency components. `n4domains stability <task> --out <new.json>
--draws 100` refits whole train-component bootstrap draws without test Y. Both
require an explicit provider (or the configured environment path) and refuse an
existing destination file. Pilot directories must be new. Full PCA moments have
their own availability reason; their budget no longer blocks public FlexiblePCA
scores and coverage. The exact large rank-one solver case remains a separate
upstream robustness proposal in UPSTREAM_DEPENDENCIES.md.
