# Local storage audit — alpha.8

Measured on 2026-10-17T07:58:34.675426+00:00. Filesystem: NTFS (queried on Windows).
Sizes below are bytes, not marketing GB rounded from folder names. Detailed absolute paths,
file mtimes and duplicate groups are in ignored `.audit/storage-alpha8/`.

Workspace: **11,507,047,962 logical bytes**, **11,082,038,104 unique file-allocation bytes**; 61,129 files.
File allocations use Windows FileStandardInfo, and physical file IDs prevent hardlink double counting.
Reparse points are not traversed. Directory/MFT overhead and unlisted external caches are excluded.
The first preliminary scan used logical sizes and was superseded by this file-ID/allocation audit;
its original JSON remains preserved. This corrected audit follows small source/check changes,
so it includes the initial inventory file and a development check, not a historical 11-GB snapshot.

## Volumes and external caches

| Root category | Total volume bytes | Free volume bytes | Present |
|---|---:|---:|---|
| workspace | 1,680,752,578,560 | 355,838,337,024 | True |
| datasets_default_cache | 365,979,234,304 | 161,180,864,512 | False |
| pip_cache | 365,979,234,304 | 161,180,864,512 | True |

Datasets 0.3.11 documents its Windows default under `%LOCALAPPDATA%/nirs4all-datasets/cache`;
it is absent. No configured alternate Datasets cache was discovered. Historical canonical
reproductions are inside results and charged there, not charged again as an external cache.
The pip cache contains only 5,405 logical bytes at this measurement. This does not inventory
unrelated repositories, every user Rust installation or protected private origin storage.

## Top-level footprint

| Path/class | Logical bytes | Unique allocated bytes | Files |
|---|---:|---:|---:|
| `.tools` | 3,406,532,784 | 3,284,662,088 | 24,425 |
| `target` | 3,131,805,345 | 2,777,321,352 | 7,740 |
| `results` | 3,072,588,295 | 3,074,427,288 | 920 |
| `.audit` | 1,193,039,391 | 1,207,583,384 | 6,868 |
| `.venv` | 695,402,461 | 729,233,216 | 20,464 |
| `docs` | 3,692,308 | 3,814,144 | 55 |
| `tests` | 1,472,432 | 1,589,248 | 50 |
| `.git` | 1,279,554 | 1,949,192 | 491 |
| `bridges` | 528,620 | 615,296 | 44 |
| `crates` | 213,587 | 238,568 | 14 |
| `scripts` | 169,836 | 221,184 | 23 |
| `examples` | 135,887 | 143,360 | 4 |
| `<root files>` | 123,406 | 135,800 | 8 |
| `schemas` | 53,336 | 77,824 | 13 |
| `configs` | 7,382 | 22,064 | 9 |
| `.github` | 3,338 | 4,096 | 1 |

Tools/Rust build/Python/upstream audits are reusable development costs; they do not scale per
dataset. `target/debug/deps` and `target/debug/incremental` dominate build space; there is no
release profile in this measurement. `.tools` includes Rust, GCC, LLVM and their downloaded
archives. `.venv` includes native DLLs and data transport dependencies, not dataset matrices.
The tracked source/docs/fixtures are small; git object bytes are separately inventoried.

## Largest directories (overlapping hierarchy; do not sum)

| Path/class | Logical bytes | Unique allocated bytes | Files |
|---|---:|---:|---:|
| `.tools` | 3,406,532,784 | 3,284,662,088 | 24,425 |
| `target` | 3,131,805,345 | 2,777,321,352 | 7,740 |
| `target/debug` | 3,127,303,473 | 2,772,578,472 | 7,524 |
| `results` | 3,072,588,295 | 3,074,427,288 | 920 |
| `target/debug/deps` | 1,547,389,313 | 1,422,960,712 | 533 |
| `target/debug/incremental` | 1,366,832,876 | 1,187,449,032 | 5,859 |
| `.audit` | 1,193,039,391 | 1,207,583,384 | 6,868 |
| `.audit/methods` | 972,747,615 | 980,907,352 | 3,809 |
| `.tools/mingw64` | 960,400,285 | 979,554,112 | 11,873 |
| `.tools/rustup` | 945,110,751 | 945,558,416 | 219 |
| `.tools/rustup/toolchains` | 945,110,587 | 945,558,248 | 217 |
| `.tools/rustup/toolchains/stable-x86_64-pc-windows-gnu` | 945,110,587 | 945,558,248 | 217 |
| `.tools/llvm-mingw-20261006-ucrt-x86_64` | 750,050,593 | 768,759,408 | 9,053 |
| `.venv` | 695,402,461 | 729,233,216 | 20,464 |
| `.venv/Lib` | 691,948,327 | 725,714,128 | 20,434 |
| `.venv/Lib/site-packages` | 691,948,327 | 725,714,128 | 20,434 |
| `.audit/methods/benchmarks` | 683,562,203 | 686,710,056 | 1,261 |
| `.audit/methods/benchmarks/cross_binding` | 682,983,139 | 686,096,864 | 1,239 |
| `.audit/methods/benchmarks/cross_binding/data` | 669,863,569 | 672,436,072 | 967 |
| `.audit/methods/benchmarks/cross_binding/data/.x_target` | 649,060,475 | 649,490,432 | 165 |
| `results/split-stress-alpha7` | 585,615,772 | 585,696,992 | 42 |
| `.tools/rustup/toolchains/stable-x86_64-pc-windows-gnu/bin` | 492,849,450 | 492,879,872 | 14 |
| `.tools/rustup/toolchains/stable-x86_64-pc-windows-gnu/lib` | 430,493,737 | 430,767,496 | 132 |
| `.tools/rustup/toolchains/stable-x86_64-pc-windows-gnu/lib/rustlib` | 430,493,737 | 430,767,496 | 132 |
| `.tools/rustup/toolchains/stable-x86_64-pc-windows-gnu/lib/rustlib/x86_64-pc-windows-gnu` | 429,297,085 | 429,545,312 | 116 |

## Largest files

| Relative path | Bytes | Modified UTC |
|---|---:|---|
| `.tools/rustup/toolchains/stable-x86_64-pc-windows-gnu/bin/rustc_driver-737f10a507f50706.dll` | 340,951,063 | 2026-10-16 |
| `.tools/winlibs-x86_64-posix-seh-gcc-16.2.0-mingw-w64ucrt-14.0.0-r2.zip` | 273,613,326 | 2026-10-16 |
| `.audit/methods/.git/objects/pack/pack-f5a061ca99dbf2591c987f69c3cf628794fcca3a.pack` | 221,153,495 | 2026-10-16 |
| `.tools/rustup/toolchains/stable-x86_64-pc-windows-gnu/lib/rustlib/x86_64-pc-windows-gnu/bin/rust-lld.exe` | 218,408,593 | 2026-10-16 |
| `.tools/llvm-mingw-20261006-ucrt-x86_64.zip` | 190,836,485 | 2026-10-16 |
| `results/split-stress-alpha7/ecosis/report.json` | 137,560,715 | 2026-10-17 |
| `results/split-stress-alpha7/control-independent_y/report.json` | 107,659,100 | 2026-10-17 |
| `results/split-stress-alpha7/control-mixed/report.json` | 105,467,268 | 2026-10-17 |
| `results/split-stress-alpha7/control-trait_only/report.json` | 105,378,480 | 2026-10-17 |
| `results/split-stress-alpha7/control-group_only/report.json` | 105,105,688 | 2026-10-17 |
| `.tools/llvm-mingw-20261006-ucrt-x86_64/bin/libLLVM-23.dll` | 77,676,032 | 2026-10-16 |
| `.tools/rustup/toolchains/stable-x86_64-pc-windows-gnu/lib/rustlib/x86_64-pc-windows-gnu/lib/libcore-d9c7ef74bee84a19.rmeta` | 68,100,145 | 2026-10-16 |
| `target/debug/n4domains.exe` | 63,336,448 | 2026-10-17 |
| `target/debug/deps/n4domains-43bb4b75575e2c10.exe` | 63,336,448 | 2026-10-17 |
| `target/debug/deps/n4domains-a0813e276d37c5b1.exe` | 63,298,560 | 2026-10-17 |
| `target/debug/deps/n4domains-217af7890da41aa1.exe` | 60,413,440 | 2026-10-16 |
| `.tools/rustup/toolchains/stable-x86_64-pc-windows-gnu/bin/cargo.exe` | 59,565,191 | 2026-10-16 |
| `results/structure-alpha5-qualified/shootout-repeat/report.json` | 56,147,546 | 2026-10-16 |
| `results/structure-alpha5-qualified/shootout/report.json` | 56,147,546 | 2026-10-16 |
| `results/structure-alpha5-final/shootout-repeat/report.json` | 56,147,546 | 2026-10-16 |
| `results/structure-alpha5-final/shootout/report.json` | 56,147,546 | 2026-10-16 |
| `results/structure-alpha5/shootout-repeat/report.json` | 56,145,018 | 2026-10-16 |
| `results/structure-alpha5/shootout/report.json` | 56,145,018 | 2026-10-16 |
| `target/debug/deps/structure-b6323ce878d7874a.exe` | 54,403,584 | 2026-10-17 |
| `target/debug/deps/structure-ef3a1515724277ed.exe` | 54,400,512 | 2026-10-17 |

## Results by pilot

| Path/class | Logical bytes | Unique allocated bytes | Files |
|---|---:|---:|---:|
| `results/split-stress-alpha7` | 585,615,772 | 585,696,992 | 42 |
| `results/structure-alpha5-final` | 279,450,981 | 279,519,232 | 31 |
| `results/structure-alpha5-qualified` | 279,450,981 | 279,519,232 | 31 |
| `results/structure-alpha5` | 279,429,111 | 279,511,040 | 31 |
| `results/ecosis-alpha4-release` | 222,321,492 | 222,433,800 | 53 |
| `results/ecosis-alpha4-qualified` | 222,319,107 | 222,433,800 | 53 |
| `results/ecosis-alpha4-final` | 222,316,481 | 222,425,608 | 53 |
| `results/ecosis-alpha4-full-grid` | 222,214,739 | 222,319,112 | 51 |
| `results/dependence-alpha6-final` | 132,058,508 | 132,231,528 | 87 |
| `results/ecosis-alpha4-run2` | 124,249,530 | 124,342,792 | 51 |
| `results/shootout` | 115,325,183 | 115,523,456 | 107 |
| `results/dependence-alpha6-qualified` | 99,963,807 | 100,110,696 | 77 |
| `results/dependence-alpha6` | 70,502,610 | 70,623,592 | 64 |
| `results/shootout-alpha3-final` | 51,580,650 | 51,648,872 | 40 |
| `results/shootout-alpha3` | 51,580,614 | 51,648,872 | 40 |
| `results/ecosis-alpha4-run1` | 50,388,168 | 50,418,184 | 17 |
| `results/alpha5-quickstart` | 31,206,175 | 31,260,672 | 24 |
| `results/pilot` | 11,828,507 | 11,845,632 | 7 |
| `results/split-stress-alpha7-audit` | 8,427,974 | 8,437,760 | 3 |
| `results/dependence-alpha6-metadata-v3` | 5,373,818 | 5,378,048 | 2 |
| `results/shootout-alpha4` | 4,268,705 | 4,280,320 | 9 |
| `results/dependence-alpha6-canonical-check` | 1,822,849 | 1,830,912 | 4 |
| `results/alpha3-batch` | 216,810 | 245,760 | 13 |
| `results/synthetic` | 142,932 | 172,032 | 13 |
| `results/ecosis-alpha4-source-audit` | 46,192 | 61,440 | 6 |
| `results/reproducibility-1` | 41,805 | 45,056 | 2 |
| `results/reproducibility-2` | 41,805 | 45,056 | 2 |
| `results/wheels` | 34,691 | 40,960 | 2 |
| `results/alpha5-packaging` | 22,334 | 24,576 | 1 |
| `results/alpha4-packaging` | 22,333 | 24,576 | 1 |

The machine-local recovery report also groups every result by pilot/dataset/seed/phase path.
Some bootstraps, interventions and fitted models are embedded inside JSON reports; path
classification alone must not claim to measure their internal phases separately.

## Artifact classes

| Path/class | Logical bytes | Unique allocated bytes | Files |
|---|---:|---:|---:|
| `results-class/archive` | 79,358 | 90,112 | 4 |
| `results-class/bootstrap_or_stability` | 238,062 | 245,760 | 6 |
| `results-class/canonical_parquet` | 62,280,821 | 62,377,984 | 40 |
| `results-class/checkpoint` | 7,955,233 | 7,979,008 | 9 |
| `results-class/csv_intermediate_or_source` | 130,252,328 | 130,350,648 | 60 |
| `results-class/other` | 56,060,144 | 56,528,672 | 220 |
| `results-class/report_or_metadata` | 1,764,402,282 | 1,765,209,304 | 429 |
| `results-class/task_matrix` | 1,051,320,067 | 1,051,645,800 | 152 |

## Formats across measured roots

| Path/class | Logical bytes | Unique allocated bytes | Files |
|---|---:|---:|---:|
| `extension/.json` | 3,024,690,381 | 3,032,137,144 | 3,438 |
| `extension/.exe` | 2,462,816,120 | 2,184,327,168 | 699 |
| `extension/.bin` | 840,842,218 | 841,509,064 | 435 |
| `extension/.csv` | 783,219,888 | 784,407,864 | 534 |
| `extension/.dll` | 762,449,835 | 762,781,696 | 157 |
| `extension/.a` | 575,016,006 | 583,494,928 | 4,183 |
| `extension/.o` | 499,755,165 | 319,853,080 | 5,355 |
| `extension/.zip` | 464,453,432 | 464,463,888 | 9 |
| `extension/.rlib` | 403,293,664 | 357,908,480 | 104 |
| `extension/.pack` | 248,394,805 | 248,401,920 | 4 |
| `extension/.rmeta` | 245,080,754 | 229,072,896 | 252 |
| `extension/.h` | 220,786,722 | 235,775,304 | 7,420 |
| `extension/.pyd` | 188,172,288 | 188,907,520 | 397 |
| `extension/.py` | 159,607,103 | 176,822,136 | 9,376 |
| `extension/.pyc` | 143,611,628 | 155,544,960 | 6,271 |
| `extension/.so` | 70,028,720 | 70,049,792 | 12 |
| `extension/.parquet` | 62,303,941 | 62,410,752 | 45 |
| `extension/.mat` | 48,589,617 | 48,620,720 | 126 |
| `extension/.rs` | 47,137,642 | 50,806,976 | 2,179 |
| `extension/<none>` | 23,113,077 | 26,387,968 | 2,873 |

## Reclamation proposals — no cleanup executed

Scientific result byte-identical groups account for **1,412,320,498 logical duplicate bytes**.
SHA-256, size and exact paths are recorded locally. Equal summary metrics never count as duplicates.
Historic repeated runs deliberately substantiate replay; byte identity alone does not authorize deletion
or imply that two model protocols are interchangeable. All frozen alpha.4–alpha.7 outputs remain protected.
The local plan names compiler incremental files and downloaded compiler archives as possible recovery
candidates; rebuilding or obtaining exactly the same compiler archive would be necessary. These proposals
overlap the top-level totals and must not be added as new costs. No scientific cache eviction is proposed.
**Bytes removed or migrated: zero.** User approval is required for any future cleanup/migration.

## Measured experiment costs and next measurement

Frozen real alpha.7 report: 137,560,715 bytes. Its alpha.8 compact scientific payload is
2,653,084 bytes before the small task/execution wrapper. The compaction preserves matched OOF
predictions, scalar/vector metrics, attempt availability, confidence intervals and scoped lineage hashes.
It omits full target maps/debug histories, whose reconstruction requires the preserved input and controller.
Current results contain 1,051,320,067 task-JSON bytes and 62,280,821 canonical-Parquet bytes across
repeated runs, plus 130,252,328 CSV bytes. These are not distinct-dataset input totals. Local per-file
hashes permit provenance review; alpha.8 does not copy any of those matrices into every execution.
The controlled stage measurements, peak estimates, authorized policy and post-run footprint are in
`docs/audit/alpha8-bank-qualification.json` after execution. Runtime estimates remain uncalibrated
for unacquired datasets; catalog dense-byte lower bounds must not be mistaken for compressed input sizes.
Full-bank storage is fixed footprint + distinct provider inputs + retained per-task evidence + bounded
concurrent scratch, as described in STORAGE_AND_REPRODUCIBILITY.md. Multiplying this workspace by 164 is invalid.

## Post-execution measurement

The second full inventory after controlled execution and all Rust builds measures
12,005,156,628 logical bytes / 11,579,025,256 unique file-allocation bytes on NTFS.
Relative to the corrected pre-experiment inventory this is +498,108,666 logical /
+496,987,152 allocated bytes. Rust build outputs account for +440,124,451 logical
bytes; both retained alpha.8 result roots together occupy 17,495,349 bytes.
The remainder includes fixed filesystem inventories, source/compact evidence,
packaging and verification output. This is not a clean single-task disk delta;
individual stage bytes/timings separately identify scientific costs.

The detailed post-inventory JSON itself is 37,115,506 bytes and is necessarily
excluded from its own scan. Its local path and exact file list stay ignored.
At the scan D: had 355,339,743,232 free bytes and C: 161,141,858,304; both NTFS.
The default Datasets cache is still absent. A real non-destructive cleanup plan
lists six validated owned scratch files; no byte is removed. Shared/custom cache
roots and referenced mean inputs are protected. The full machine-local plan is
under `.audit/storage-alpha8/`; approval would still be necessary for deletion.

## Distinct input costs

The retained original EcoSIS freeze-dried CSV pair outside this repository occupies 12,626,112 bytes (2 files), measured read-only by path/size/SHA-256. This is an external origin store, not a Datasets acquisition cache, and is excluded from the repository totals.

| Canonical dataset | All copied Parquet bytes | Exact unique Parquet bytes |
|---|---:|---:|
| pharmaceutical_tablets_nir_shootout_eigenvector | 29,904,749 | 4,272,107 |
| ecosis_freeze_dried_leaf_spectra_and_measured_traits_from_the_reflectance_nirs | 32,376,072 | 5,396,012 |
| unclassified_canonical | 23,120 | 23,120 |

Exact file hash deduplication is a cost estimate only, not authority to merge samples,
evict versions or replace provenance. Raw and canonical bytes may both be required.
Private/ephemeral sources require protected-cache access for portability.
