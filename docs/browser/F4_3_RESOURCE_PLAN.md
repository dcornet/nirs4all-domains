# F4.3 staged engineering plan — 2026-11-18

The applied envelope is **8,000,000,000 bytes total cumulative engineering**,
with a **30,000,000,000-byte effective aggregate cap** inside the existing
50,000,000,000-byte authorization. It increases the former 4 GB allowance by
4 GB. It preserves the initial 18,663,326,977-byte baseline and all charged
growth. This is capacity for bounded engineering, not a spending target.

## Delivery measurement and independent loading hotfix

The authenticated `near-delivery-01` observation measures **23,221,661,899 bytes**
combined, **4,558,334,922 bytes** charged against the unchanged initial baseline,
and **3,441,665,078 bytes** engineering allowance remaining. The 30 GB effective
cap has 6,778,338,101 bytes headroom; engineering allowance remains the tighter
limit. C:/D: free bytes were 143,150,829,568 / 332,821,766,144, each above the
2,147,483,648-byte reserve. Subsequent receipts remain separately retained.

The owner's added worker-loading priority uses a separate main-based worktree
and PR #15 within this same accounting scope. Locked npm dependencies were
installed there with the existing cache; one cache miss required the original
hash-locked Methods package download. Its local Rust WASM came from the verified
successful main CI artifact, without rebuilding or changing a numerical kernel.
F4.3 uses its own compiled binding and retained original binding backup.

All old accounting, failed attempts, raw synthetic qualification artifacts,
native executables, logs and worktrees remain charged and preserved. There is
**no baseline reset and zero new scientific reservations**: 2,015,788,498 bytes
reserved against the unchanged 2,023,410,176-byte scientific ceiling. Journal
SHA-256 remains `237f8a7fedd5f83eff4a850e78900a892e640fd2582bac099520e39108d25e0c`.
The applied owner-policy digest is
`0f5a5f7ee886d13b9f278e4ceeb915a00f80eeda34474ad77f3ad8496e8c3b6a`.

Historical verification independently checked 1,031 manifest entries and five
additional preserved paths with zero size/hash failures. This does not turn the
partial F4.3 scientific qualification into a passing result.

## Measured starting point

The root agent's authenticated pre-amendment snapshot reports:

| Measure | Bytes |
|---|---:|
| Actual aggregate usage | 22,038,391,285 |
| Original baseline | 18,663,326,977 |
| Charged engineering | 3,375,064,308 |
| Existing cumulative engineering allowance | 4,000,000,000 |
| Existing engineering remaining | 624,935,692 |
| Existing effective-cap margin | 2,961,608,715 |
| Proposed cumulative engineering allowance | 8,000,000,000 |
| Indicative engineering remaining after amendment | 4,624,935,692 |
| Indicative 30 GB effective-cap margin | 7,961,608,715 |

These are sequential observations, not a filesystem quota or an atomic snapshot.
The actual `amend` operation made another fresh measurement after root review
and 18 synthetic controller tests. The application record below supersedes the
indicative margins; no policy was changed by the budget agent. The reported physical free space was approximately 143.7 GB
on C: and 335.4 GB on D:. Admission uses fresh exact free bytes and retains
2,147,483,648 bytes on **each** participating volume; volumes are never summed.

An 8 GB cumulative allowance implies a maximum baseline-plus-engineering usage
of 26,663,326,977 bytes. The proposed 30 GB effective cap leaves 3,336,673,023
bytes above that bound; the separate engineering allowance remains binding.
The former 25 GB cap cannot admit the complete proposed cumulative allowance.

## Public build and cache inventory

The budget agent used the existing `storage.tree_bytes` unique-file-identity
accounting helper, without opening private-root configuration or data contents.
Categories were scanned separately, overlap, and **must not be added together**
or substituted for the root agent's full-scope authenticated snapshot.

| Existing category | Measured bytes | Planned treatment |
|---|---:|---|
| Original workspace Rust target | 5,829,125,947 | Reuse; preserve build outputs and dependencies |
| Original workspace audit tree | 5,641,131,272 | Preserve history, proofs, active worktree and targets |
| Original workspace tools | 3,458,206,861 | Reuse installed toolchains/caches; no new dependency installation |
| Original Python environment | 695,402,478 | Preserve and reuse |
| F4.2 reduced-debug target, inside audit tree | 1,182,456,010 | Reuse where compatible; account for additional outputs |
| F4.2 native/native-provider output categories | 9,324,295 | Preserve native qualification artifacts |
| F4.2 Python tools | 55,873,885 | Preserve installed tooling |
| F4.2 npm cache | 29,469,604 | Preserve; no demonstrated need to clean |
| Three F4.2 browser-capture categories | 21,699,389 | Preserve unique qualification evidence |
| Active demo dependencies | 112,619,535 | Reuse existing installation |
| Active WASM dependencies | 3,947,762 | Reuse existing installation |
| Active demo distribution | 16,074,962 | Preserve prior build; new artifacts remain charged |

No whole-target purge, cache deletion, migration or history removal is proposed.
The scan establishes retained capacity and reuse opportunities; it does not
establish that any specific object is inactive, safely reconstructible or
eligible for deletion. Any later targeted cleanup needs its own concrete
ownership, inactivity, reconstruction and preservation evidence.

## Staged additional-output forecast

The following estimates share the **4,000,000,000-byte increase**, while actual
admission still charges all growth from the original baseline. They are upper
planning allowances, not additional scientific reservations or per-agent grants.

| Stage | Additional-output estimate | Scope |
|---|---:|---|
| Sources, compact synthetic fixtures and controller tests | 134,217,728 | Fixed representative preprocessing panel; no new real-data acquisition |
| Reused reduced-debug native and WASM builds | 2,147,483,648 | Bound new outputs; reuse existing targets and locked dependencies |
| Browser builds and captures | 536,870,912 | Chromium/Firefox synthetic qualification and retained failures |
| Reports and qualification receipts | 536,870,912 | Compact native/WASM comparisons, exports and hosted proof receipts |
| Stage subtotal | 3,355,443,200 | Charge actual bytes, including failed attempts |
| Contingency inside the 4 GB increase | 644,556,800 | Available only after fresh measurement/admission |

Representation matrices and provider allocations also need the scientific
protocol's independent cell/memory budgets. Do not retain every intermediate
matrix for every parameter combination or infer that a disk allowance admits
an unbounded panel. Numerical preprocessing and diagnostics stay in the pinned
official providers; Python remains transport/accounting only.

Measure and admit before substantial builds, browser-output batches and exports,
then measure actual use after each stage. Stop and explain a refusal or estimate
overrun; do not reset the baseline, silently delete failed outputs or substitute
an old scientific allowance. The 50 GB authorization is a maximum, not the
active engineering allowance. This controller is cooperative admission, not an
OS quota, and unrelated activity in the accounting scope consumes the allowance.

## Amendment, preservation and validation

Use the existing authenticated `amend` operation, with explicit owner request
digest/date and the unchanged pinned recipe. Operator placeholders below refer
to existing authorized locations and contain no distributable private paths:

```powershell
python scripts/engineering_storage.py amend --workspace ORIGINAL_WORKSPACE --private-config VALIDATED_LOCATOR_FILE --measurement-recipe QUALIFIED_RECIPE --out SANITIZED_AMENDMENT.json --effective-bytes 30000000000 --engineering-bytes 8000000000 --authorized-max-bytes 50000000000 --reserve-free-bytes 2147483648 --owner-request-sha256 OWNER_REQUEST_SHA256 --decision-date 2026-11-18 --recipe-sha256 PINNED_RECIPE_SHA256
```

The new receipt includes `before_amendment` under the predecessor's caps using
the same fresh measurement. The prior policy fingerprint, immutable decisions,
initial measurement and charged usage remain linked and authenticated. No
baseline argument is accepted; `activate` rejects an existing policy/history.
The root agent reviews tests, applies the actual amendment and records actual
before/after usage, limits, physical margins and public policy fingerprint.

Scientific reservations remain 2,015,788,498 / 2,023,410,176 bytes, leaving
7,621,678 bytes. Preserve journal SHA-256
`237f8a7fedd5f83eff4a850e78900a892e640fd2582bac099520e39108d25e0c`,
all Research results, frozen D1–D6.1 evidence, Git history and existing access
restrictions. There is no new scientific reservation, real-data experiment,
upstream edit, key/root change, install or deletion in this budget work.

Local validation: `python -m unittest discover -s bridges/python/tests -p
test_engineering_storage.py -v` passed **18 tests**. These include all retained
F4.2 scenarios plus 25-to-30 GB cap amendment, unchanged charged growth,
before/after receipt coherence, authenticated predecessor cap, invalid
baseline/allowance/maximum bounds and fresh per-volume reserve failure. Actual
private-policy application is a separate root-agent action.

## Applied prospective amendment

The owner-authorized amendment was applied on 2026-11-18 using the existing
authenticated controller, measurement recipe, roots and key. Its same-measurement
before/after receipt records 22,039,426,984 total bytes and 3,376,100,007 bytes
charged from the unchanged 18,663,326,977-byte baseline. The allowance is now
8,000,000,000 cumulative bytes, leaving **4,623,899,993 bytes**. The effective cap
is 30,000,000,000; the authorized maximum remains 50,000,000,000. The prior
allowance was 4,000,000,000 and prior effective cap 25,000,000,000; the old charged
usage was not reset. Physical free bytes were 143,687,176,192 and 335,369,515,008,
both above the unchanged 2 GiB reserve.

New policy SHA-256:
`0f5a5f7ee886d13b9f278e4ceeb915a00f80eeda34474ad77f3ad8496e8c3b6a`.
Predecessor:
`85afbe078e461fd70ad8e578645701d0ebc7818fe77f680be83da0e0dd0653a4`.
Scientific reservations and the journal hash above remain exact, with no new
scientific reservation. All subsequent output remains charged to this baseline.
