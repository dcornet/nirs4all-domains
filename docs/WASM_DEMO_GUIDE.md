# Browser demo guide

The demo under [`../demo`](../demo/README.md) is a local, exploratory browser
client. It demonstrates reviewed X/Y/M import through published IO/Formats and
scoped access to existing Domains, Preflight, and Methods APIs. Imported Y
remains in main import memory for inventory/masking but does not enter scientific
worker requests or report exports. The client sends no data to a server and has
no upload API.

## Clean build

Prerequisites: Rust with the `wasm32-unknown-unknown` target, `wasm-pack`, Node
and npm. From the repository root:

```shell
rustup target add wasm32-unknown-unknown
cd bindings/wasm
npm run build:native
npm ci --ignore-scripts
cd ../../demo
npm ci
npm run typecheck
npm run build
npm run preview
```

The WASM build uses the existing crate and `browser-wasm` feature. Generated
files in `bindings/wasm/native/` are build output and are not a source package;
`Cargo.lock` is the locked Rust dependency source. The local npm binding is
`@nirs4all/domains@0.1.0-alpha.17`, depending on Methods 1.3.13 through the
Preflight 0.1.6 provider / ABI 2.20. The demo lock pins IO-WASM and
Formats-WASM 0.2.14 and nirs4all-ui 0.2.5. Build the local WASM package before
`npm ci`; npm does not run the Rust/WASM build for it.

Vite is configured for `/nirs4all-domains/`. Serve the `demo/dist/` output at
that prefix, with a static-host fallback for the application route. Local
`preview` is not deployment evidence. `demo/src/main.tsx` supplies the runtime,
worker orchestration and report exports. The Pages workflow builds and publishes
`main` when the repository's Pages source is GitHub Actions; consult its actual
deployment outcome before claiming public availability.

## Use

The [F2 journey](ux/F2_USER_JOURNEY.md) documents the four open steps, exact
evidence navigation, local import help and partial/complete export selection.
Its [qualification](ux/F2_VALIDATION.md) distinguishes actual executed checks
from human utility and full accessibility claims.

Choose the deterministic synthetic fixtures to inspect provider behavior,
select the packaged public saved tablet example to read its already saved
evidence, or import a supported dataset locally. For import, review source and
column roles, declared identity keys, keyed joins, and partitions in
`DatasetBuilder`, then confirm the reviewed assembly. Import retains the dataset
and missingness but performs no automatic fit. Choose an operation separately:
Train structure uses train rows; the raw support query uses train as reference
and test as query; metadata audits are documentary; global descriptive structure
requires explicit transductive consent and includes train plus test, excluding
predict rows. An unpartitioned source continues through the legacy full-source
descriptive route. The page provides data and provenance, spectra, geometry,
findings, intended-use context, evidence and export sections. English/French and
light/dark preferences are application settings. The shared `nirs4all-ui`
package supplies qualification charts and the official nirs4all logo assets;
there is no Domains-specific mark in that package release.

Live input accepts at most 32 files / 8 MiB; a fully assembled source is
limited to 2,000 observations and 1,000,000 cells. IO and Formats own parsing,
keyed joins and assembly. The demo refuses implicit multisource fusion,
aggregation and row deletion; nullable X/Y/M values and declared partitions
remain visible after import. Operations needing complete X may be unavailable
rather than imputing or dropping rows. No Y value is sent to a scientific
request. Metadata audits report counts, cardinality, levels, missingness and
literal overlap; statistical associations are unqualified. Metadata coloring
is presentation-only and does not calculate association or alter PCA evidence.
See the [architecture](WASM_DEMO_ARCHITECTURE.md), [capability
matrix](WASM_CAPABILITIES.md), [F4.0 partition behavior](WASM_PARTITION_GUARD.md),
and [F4.0 architecture notes](browser/F4_0_IMPORT_ARCHITECTURE.md) for exact
boundaries. The [F4.2 validation record](browser/F4_2_VALIDATION.md) separates
local execution evidence from pending final-head and hosted checks.

### F4.3 representation sensitivity

The F4.3 worktree adds **Preprocessing sensitivity** as a separate X-only
operation. Review the prospective plan before running it: raw is required
first, and the default fixed panel includes SNV, MSC, SG smoothing/derivatives,
linear detrend, Gaussian smoothing, StandardScale, Normalize, and two explicit
SNV→SG chains. Each entry's parameters remain visible/editable in the bounded
JSON plan. The attributed AOM bank contributes descriptors only; Methods
1.3.13 / ABI 2.20 executes the numerical transforms, with no AOM equivalence
claim.

For partitioned data, run the first stage on the declared training reference
population only. An optional test-X audit is a second explicit action after a
matching reference result and plan are frozen; it reuses the reference-fitted
transform states and never fits on test. Test inspection can influence later
choices, so it is descriptive rather than an untouched final evaluation. The
request has no Y field. A fully unpartitioned source follows a separately
labeled descriptive path; mixed assigned/unpartitioned populations are not
accepted.

The display shows each representation and its own diagnostics. It does not
rank or recommend transforms, compare absolute distances across scales, or
claim that stable results establish chemical relevance, independence,
prediction quality, or cause. Read the [representation contract](browser/F4_3_REPRESENTATION_CONTRACT.md),
[comparability rules](browser/F4_3_COMPARABILITY_RULES.md),
[train/test policy](browser/F4_3_TRAIN_TEST_POLICY.md), and separate
[qualification record](browser/F4_3_VALIDATION.md) before interpreting results.

A single `.json` file is read as a saved standalone Domains report and must
pass its existing report schema. It is not a generic JSON matrix import. An
explicit IO configuration must use the exact lowercase suffix `.nirs4all.json`
and be selected together with the source files it references. A configuration
alone does not contain a spectral population. Use CSV/TSV or a supported spectral
reader for X; renaming a matrix JSON does not qualify a new input format.

## Outputs and data rights

The report contract excludes raw spectra and retains source, content hash,
original axis, scope, provider evidence, reasons, findings and limitations.
The application downloads HTML, Markdown and JSON from one report model; HTML
is self-contained for offline viewing and printing. Never treat a serialized
report as permission to redistribute its source dataset.

Synthetic examples are generated by deterministic fixture code and licensed
with the project. The tablet example is a public source-permitted saved report
projection; consult its included attribution and per-source rights record. No
private Research example, raw private data, target values or unlicensed source
table is part of the demo. The UI and IO/Formats npm packages are offered under
`CeCILL-2.1 OR AGPL-3.0-or-later`; see their package notices and
[repository licensing](../LICENSING.md). Data licenses remain separate.
