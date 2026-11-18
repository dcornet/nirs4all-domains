# Prospective Domains storage decision — 2026-11-17

## Current cumulative amendment — 2026-11-18

F4.2 explicitly authorizes **4,000,000,000 bytes total cumulative engineering**.
The existing controller's new `amend` operation was actually applied, retaining
the initial **18,663,326,977-byte baseline**, all charged growth, the original
measurement and scientific-journal provenance. `activate` now refuses an already
existing policy; it cannot silently restart the counter. The authenticated
decision links its predecessor and fingerprint, and the full retained chain is
verified. No second registry, key or scientific reservation was created.

The effective 25,000,000,000-byte and maximum 50,000,000,000-byte caps, per-volume
2 GiB reserve and scientific ceiling/cumulative reservations remain unchanged.
The amendment measured **20,103,985,118 bytes**, of which **1,440,658,141 bytes**
remain charged to engineering, leaving **2,559,341,859 bytes**. Its authenticated
policy fingerprint is
`85afbe078e461fd70ad8e578645701d0ebc7818fe77f680be83da0e0dd0653a4`.
Fourteen synthetic controller tests passed before application. Amendments check
fresh aggregate growth and physical margins before publishing the pointer;
failed amendments preserve the active decision. The recipe and science journal
hashes below remain unchanged. See the [F4.2 staged plan](../browser/F4_2_RESOURCE_PLAN.md)
and its final execution record for later usage. Earlier figures below retain
their 2026-11-17 attribution; 2 GiB is the former allowance, not the current cap.

Example: use `amend` with the same locator/workspace/recipe arguments as the CLI
below and explicit `--engineering-bytes 4000000000`, unchanged effective/max/
reserve values, owner request digest and decision date. No baseline parameter
is accepted. A fresh `snapshot` reports the preserved baseline and charged use.

## Initial decision — 2026-11-17

The owner authorizes **50,000,000,000 bytes** of cumulative local storage in the
existing accounting scope. After inventory and targeted cleanup, the applied
operational cap is **25,000,000,000 bytes**, with **2,147,483,648 bytes** of
additional engineering capacity. This leaves normal development room without
consuming the entire authorization. No further owner approval is required for
an explicit prospective adjustment within 50 GB. A higher maximum requires approval.

The scientific reservation ceiling remains **2,023,410,176 bytes**. Its historical
cumulative reservations remain **2,015,788,498 bytes**, leaving **7,621,678 bytes**.
This task adds no scientific reservation, fit, raw data acquisition or protocol
change. Local capacity does not authorize an experiment or change its limits.
The minimum physical reserve remains **2,147,483,648 bytes per volume**.

## Applied source of truth and accounting

[EngineeringStorage](../../bridges/python/nirs4all_domains/engineering_storage.py)
and its [operator CLI](../../scripts/engineering_storage.py) use the **existing
Domains PrivateStore**, existing key, atomic writer, serialized lease and unique
file-identity accounting. No new key, scientific journal, root locator, copied
dataset store or Research configuration was created. A prospective authenticated
owner decision and current pointer were actually written in that store.
Immutable previous decisions and measurement receipts are retained.

The owner's request SHA-256 is
`84bb890fa1f9e06ac3a54af1dc466cf2920e9c9640b7e9daf3304ec7b3b400b3`.
The applied policy fingerprint is
`2f834f347facb882af6b4a5d3594f737dc05198ea0adecbc0ea2a45a069f5182`.
Its activation baseline is **18,663,326,977 bytes**. Engineering use is subsequent
positive aggregate growth from that baseline, not a scientific reservation or a
second sum of overlapping caches. Other activity in the accounting scope also
consumes that conservative growth allowance.

The controller invokes the previously qualified local measurement recipe,
pinned at SHA-256
`fb6d5e393b4308856427532f3754d3822320ce2bb3de6225bce3484bb2bb8b62`.
The scope still includes the original Domains workspace, associated Research
workspace, existing private evidence and registered participating external files.
Overlapping roots and hardlinks count once. Locator values are loaded through
[the private-root inspector](../../scripts/inspect_private_roots.py) and never
printed. No confidential path appears in the public snapshot.

The recipe's inherited 20,826,468,033-byte limit is now explicitly an **imported
historical reference**, not the Domains engineering cap. Research and historical
Alpha/task policies are preserved verbatim. Their scientific contracts are not
amended or executed by this engineering controller. Ordinary current engineering
must use this controller rather than treating an old scientific receipt or a
former 8/12 MiB F4.1 stage as its active authority.

Admission checks fresh measured aggregate growth plus the proposed bytes against
the engineering allowance, aggregate cap and each volume's actual free space
minus reserve. It never adds the capacities of different volumes. It validates
the recipe digest, retained receipt bytes, freshness, authenticated policy and
scientific counter consistency. This is cooperative admission and measurement,
not an OS filesystem quota or a promise that another process cannot write.

Operator usage (placeholders denote the already authorized local locations):

```powershell
python scripts/engineering_storage.py snapshot --workspace ORIGINAL_WORKSPACE --private-config VALIDATED_LOCATOR_FILE --measurement-recipe QUALIFIED_RECIPE --out SANITIZED_SNAPSHOT.json
python scripts/engineering_storage.py admit --workspace ORIGINAL_WORKSPACE --private-config VALIDATED_LOCATOR_FILE --measurement-recipe QUALIFIED_RECIPE --requested-bytes 1073741824 --out SANITIZED_ADMISSION.json
```

Activation requires explicit `--effective-bytes`, `--engineering-bytes`,
`--authorized-max-bytes`, `--reserve-free-bytes`, `--owner-request-sha256`,
`--decision-date` and `--recipe-sha256`. An amendment appends a decision linked
to its predecessor; it does not overwrite historical accounting. The CLI refuses
a missing existing key, invalid configuration or unavailable measurement. It
does not delete files, fit a model or reserve science bytes.

## Measured before and after cleanup

All sizes below are bytes. Measurements are sequential filesystem observations,
not an atomic disk snapshot. The after column precedes the isolated rebuild check;
later engineering consumption is reported separately below.

| Measure | Before cleanup | After cleanup / activation |
|---|---:|---:|
| Effective local cap | 20,826,468,033 | 25,000,000,000 applied |
| Authorized maximum | 50,000,000,000 | 50,000,000,000 |
| Aggregate measured use | 20,817,114,821 | 18,663,198,918 |
| Margin under effective cap | 9,353,212 | 6,336,801,082 |
| C: physical free | 144,512,573,440 | 144,507,408,384 |
| D: physical free | 336,642,949,120 | 338,808,004,608 |
| C: usable after reserve | 142,365,089,792 | 142,359,924,736 |
| D: usable after reserve | 334,495,465,472 | 336,660,520,960 |
| Scientific reservations | 2,015,788,498 | 2,015,788,498 |
| Scientific reservation ceiling | 2,023,410,176 | 2,023,410,176 |
| Additional engineering allowance | Former 12 MiB stage + 256 KiB receipts | 2,147,483,648 |
| Net aggregate reduction | — | 2,153,915,903 |
| Targeted directories removed | — | 81 |

Physical-space changes also include unrelated volume activity and allocation
effects; they are not an independently measured cleanup gain. The activation
snapshot was a later fresh measure, 128,059 bytes above the after-cleanup scan.

Unique-identity category inventory, retaining all uncertain objects:

| Category / logical owner | Before | After | Decision and reconstruction scope |
|---|---:|---:|---|
| Sources, documents and other workspace files / Domains | 88,592,090 | 88,592,085 | Preserve; includes changing transient workspace files |
| Qualification build outputs / Domains | 175,573,720 | 175,573,720 | Preserve unique qualification proof |
| Other Rust outputs / Domains | 4,860,173,612 | 4,908,628,190 | Preserve final binaries, dependencies and rebuild outputs |
| Other incremental caches / build dependencies | 680,388,485 | 680,388,485 | Preserve; no demonstrated cleanup need |
| Selected Domains incremental caches / Domains | 2,203,368,216 | 0 | Remove only qualified inactive candidates |
| Audit, reports and active worktree / Domains | 1,950,931,276 | 1,951,028,272 | Preserve proofs and sources; new receipts retained |
| Scientific results / Domains | 3,109,024,297 | 3,109,024,297 | Protected, preserved |
| Python installation / developer tooling | 695,402,478 | 695,402,478 | Preserve working environment |
| Toolchains and declared caches / developer tooling | 3,242,598,652 | 3,242,598,652 | Preserve archives, toolchains and Cargo dependencies |
| Small tool caches / developer tooling | 18,126 | 18,126 | Preserve; insignificant gain |
| Git objects and references / Domains | 269,646,591 | 269,646,591 | Preserve all refs and unreachable objects |
| Node dependencies / developer tooling | 241,362,405 | 241,362,405 | Preserve installed environments |
| Research workspace, mixed protected contents / Research | 537,354,056 | 537,354,056 | No mutation |
| Private evidence and metadata / source owners | 105,176,139 | 105,176,139 | Protected, preserved |
| Participating external inputs, including active journals / source owners | 2,657,563,555 | 2,658,447,136 | Preserve; existing scope, no new raw acquisition |

Category assignment and aggregate measurement are separate scans. Their totals
differ by 58,877 bytes before and 41,714 bytes after. Removing one hardlink can
reassign retained bytes to another category without changing their contents;
category deltas must not be interpreted as new scientific computations. The
selected logical tree size is likewise not the recoverable unique-byte total.

## Exact cleanup decision

Only direct children matching `nirs4all_domains-[a-z0-9]+` or
`nirs4all_domains_cli-[a-z0-9]+` under the original workspace's
`target/debug/incremental/` were removed. The retained local inventory records
all **81 exact relative directory names**, per-directory bytes and metadata
digests. These inactive caches dated to October 30; they contained only standard
incremental-session directories and `.o`, `.bin`, `.lock` and `.rmeta` files.

Before deletion the supervised verifier rechecked canonical containment, all
ancestor reparse flags, regular file types, exact inventoried metadata, absence
of compiler processes and exclusive-read availability for every selected file.
No cache shared by another project, scientific result, unique proof or required
source was selected. All paths were checked before native PowerShell
`Remove-Item -LiteralPath` performed the targeted removals. No whole-target purge,
global npm/Cargo purge, Git pruning, worktree removal or migration occurred.

The **2,379,005,229 logical bytes** unlinked corresponded to at most
**2,154,913,638 unique recoverable bytes**, after retained hardlinks. The measured
net aggregate reduction was **2,153,915,903 bytes**; the 997,735-byte difference
includes concurrent engineering/journal growth between scans. All uncertain
caches, downloaded archives, captures, PDFs, logs, CodeGraph material, final
build outputs, dependencies and the 111 previously unreachable Git objects were
deliberately retained. Age or size alone was not a deletion criterion.

Retained local evidence SHA-256:

| Receipt | SHA-256 |
|---|---|
| Before inventory | `14a5c0848072c8459b7cc016b9599665bdfba9763fb8714636d4b922e2894e90` |
| Cleanup decision | `16ce88e1ba953c98b2aeb36e0fbbddac81be29bc244201aad37f9b6a0a61311a` |
| Cleanup execution | `5263e6001a3fc128ecd6cc9176b0f43037be6638da48ae8b737ecb60fbce75d3` |
| After inventory | `614567a04f867fdfa52a3e60f6edfa1b3848913c9ed3785434a8f039dd9318cc` |
| Post-clean preservation | `c021521ed4d9aa75355b00a3865ed50aa3b14fef4409ebba66e5cd6787dddf3f` |

## Qualification and remaining limits

The nine synthetic controller tests exercise cap/growth and per-volume reserve
refusals, journal preservation, authenticated immutable amendment history,
unsafe pointers, stale/changed receipts, recipe pins and output redaction. The
existing Windows/Ubuntu warning-contracts workflow now runs them explicitly;
it receives no private configuration or scientific journal. Completed exact-head
hosted results are recorded in the delivery PR, rather than inferred from YAML.

Post-clean preservation rechecked **1,031 frozen files plus five references**,
with zero failures. Preservation manifest SHA-256 remains
`2807c2390419e615a51ece22493d175cceb3e9b3f1bd03aceccb8f5667dd094a`.
The scientific journal remains byte-exact at
`237f8a7fedd5f83eff4a850e78900a892e640fd2582bac099520e39108d25e0c`.
Git fsck found zero integrity errors; both expected worktrees, 32 references and
all 111 existing unreachable objects remained. All selected original incremental
directories were absent after cleanup.

Installed Methods 1.3.13, Formats/IO 0.2.14, Python 3.11.9, Node 24.22.1,
Rust/Cargo 1.99.1 and GCC 16.2.0 remained usable. The retained local UI install is
0.2.1; the lock and clean hosted qualification use 0.2.5. No installed local UI
upgrade is claimed. Software reconstruction is checked in a separate retained
target using the existing six `browser_factor` transport-spy tests, without
loading a numerical Methods kernel, fitting PCA or using real data.

The first offline build found missing locked Cargo dependencies. Downloading
those software dependencies exposed a MinGW default-manifest path containing
spaces. The plain short executable path alone did not fix it. These failed logs
are retained; a process-local short `GCC_EXEC_PREFIX` supplies the existing
toolchain's search prefix without changing compiler files or global settings.
That corrects manifest lookup. The GNU `cdylib` link then reaches its existing
export-ordinal limit (`138311`); the complete local `cargo test` therefore remains
failed and is not reported as passing. No export suppression or source change
was used. The newly generated `rlib` was linked with the unchanged integration
test source via `rustc --edition=2021 --test`, the same dependency artifacts and
`-L dependency=...`: **all six tests passed**, zero ignored. This demonstrates
local cache/object/static-library reconstruction and transport behavior, not
successful GNU DLL production or numerical native qualification. The existing
hosted Windows/Ubuntu gates remain responsible for the complete native build.

The initially admitted 1 GiB estimate was exceeded by 16,165,768 bytes of
measured growth, still inside the applied 2 GiB engineering allowance. Before
the harness step, a fresh guard explicitly admitted up to 512 MiB further
engineering bytes. Failed build artifacts and all logs remain accounted for;
nothing was deleted to make the measurement pass.

The pre-commit closing measurement after reconstruction is **20,101,486,608
bytes**, leaving **4,898,513,392 bytes** below the effective cap. Engineering
growth is **1,438,159,631 bytes**, leaving **709,324,017 bytes** of the initial
allowance. This includes the retained 1,068,557,942-byte dedicated target,
348,152,380-byte executable test harness, dependency downloads and receipts;
these are included in the aggregate and must not be added to it again. The
science journal/counters are unchanged. C:/D: physical free space is respectively
144,497,885,184 / 337,365,983,232 bytes; usable space after each reserve is
142,350,401,536 / 335,218,499,584 bytes. All current admissions return `ready`.

The remaining engineering allowance can support F4.1 completion and bounded
F4.2 software work while measured growth stays inside it; another full build
may require a documented engineering adjustment within the authorized cap.
The larger 50 GB
authorization is available for a documented prospective adjustment; it is not
already allocated. Scientific reservations remain nearly exhausted and need
their own authorization for future experiments. This task does not merge PR #13,
publish a release, change a version, deploy the feature or qualify a new
scientific claim.
