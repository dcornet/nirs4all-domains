# F4.3 qualification — partial draft

The frozen protocol is `domains.browser_preprocessing_sensitivity.v1`, using
Methods 1.3.13 / ABI 2.20. This is **PARTIAL**, not a completed native/WASM
qualification. No real-data analysis, Y access, upstream edit or scientific
reservation was added. PR #15 separately addresses worker loading; merging
that hotfix does not merge or qualify this feature.

## Executed evidence

| Check | Actual result |
|---|---|
| Rust access/protocol spies | 8 passed, including forbidden populations and fitted-state/frozen-reference guards |
| Native public preprocessing ABI | 4 ignored gates passed with the isolated published 1.3.13 DLL and its companion libraries |
| Public Methods JS adapter | 8 passed using the actual published WASM |
| Strict JSON schemas | 5 passed; existing scoped-result additions remain optional |
| Lightweight parity adversaries | 5 passed; wrong statistics/statuses, source/M/keys, Gram/rank and partitions remain failures |
| Engineering controller | 18 synthetic unittest cases passed before the authenticated budget amendment |
| Integrated frontend | TypeScript production build passed; 207 tests across 30 files passed |
| Actual Rust/Methods WASM panels | 35 requests completed; 20 adversarial requests refused before any provider access; all inputs/results schema-checked |
| Actual native replay | Same 35 requests and 20 pre-provider refusals completed, using backend-own frozen ancestors |
| Full numerical portability | **Failed**; original tolerance and unfavorable evidence retained |
| Workspace clippy | Passed with warnings denied after a type alias resolved the demonstrated type-complexity diagnostic |
| Historical integrity | 1,031 original files plus 5 additional preserved paths hash-checked; zero failures |

The current full comparator remains fail-closed on opaque/legacy serialization
hashes. Independently, the raw-Rust-JSON-bound diagnostic finds **144 differing
scalar fields across 27 cases / 43 nondegenerate representation-PC pairs**,
including 51 factor estimates. Consequently a hash-comparison refinement alone
would not make this feature qualified. See
[the numerical findings](F4_3_NUMERICAL_PORTABILITY_FINDINGS.md) for the exact
values, evidence hashes, limitations and bounded Methods investigation.

The diagnostic companion reports `DIAGNOSTIC_ONLY_NOT_A_PARITY_GATE` and exits
1 for the measured differences. It cannot replace a passing parity gate. CI
collects both failures and retains the overall failed status; no tolerance,
component-resolution flag, factor value or requested representation is changed.

## Fixed synthetic panel performance

One runtime, 24 reference observations by 25 bands, all 12 default entries,
one warm-up pair and three measured alternating cache-on/off pairs:

- Actual provider calls: **227 versus 233**; preprocessing fits: **11 versus 13**.
- All representation evidence was exactly equal with and without prefix reuse.
- End-to-end measured times with reuse: 238.37, 199.43, 206.71 ms; without:
  220.73, 209.29, 208.13 ms. These overlapping measurements establish call
  reduction, not a general speed advantage.
- Post-call RSS ranged from 151 to 174 MB; Node reported maxRSS 172,904 KiB.
  These are process observations, not strict allocation containment or browser
  peak measurements. Initialization was measured separately (39.30 ms).

The benchmark calls the real public runtime. It preserves the fixed population,
parameters, complete results and unfavorable cases; it makes no real-bank
throughput claim. AOM contributes attributed bank descriptors; no algebraic
shortcut or supervised selection is qualified here.

## Browser and release disposition

The actual Chrome production preview executed the six-family reference panel,
frozen four-row test audit, and invalid-SG refusal with valid raw/SNV siblings.
Reference fitting received no test/predict/Y values. Earlier F4.0/F4.1/F4.2
histories stayed unchanged. EN and FR automated accessibility each reported
zero violations, 35 passed rules and two incomplete categories; this is not
WCAG certification. Three scientific histories survived exact uncapped exports:
41,912,332-byte HTML, 30,985,620-byte Markdown and 18,962,476-byte JSON.

The initial live layout had 245,650 nodes and 3,260,816 pixels height. Reusing
existing disclosures and collapsing advanced tables reduced height to 85,108
pixels while retaining 245,656 nodes and every table/anchor. This improves
layout, but does not establish low memory use: full-document accessibility
remained expensive.

**PDF failed resource qualification.** Printing the exact HTML reached an
observed 10,013,401,088-byte renderer working set. The owned Node/Chrome tree
was terminated, its absence checked, and no PDF was produced. The full helper
now refuses F4.3 print admission above 8,000,000 HTML bytes with
`F43_PRINT_RESOURCE_QUALIFICATION_REQUIRED`; it preserves complete exports and
fails the gate. This engineering guard is not a scientific truncation or a
claim that smaller reports have qualified RAM bounds. No large print retry is
authorized by this result. Future work must avoid redundant leaf-level report
expansion while preserving every scientific value and original companion.

A separate bounded **raw-only synthetic lifecycle** run passed cancellation,
history preservation, worker termination, source replacement, reset and stale
response rejection. It does not requalify six-family printing or the complete
browser gate. The six-family partial receipt explicitly has `success:false`.
Local runs, failed receipts and all existing results are retained.

Windows/Ubuntu CI, Chromium/Firefox and the final production artifact must be
reported using actual run IDs. Configuration is not proof. Public Pages still
serves main until the owner merges a qualified PR; this branch is not deployed.
Do not mark this draft ready while numerical portability or bounded complete
printing is unresolved. CI runs the fail-closed numerical gates before the
new browser matrix, preventing a known unsafe print attempt. Passing existing
scientific/report suites does not qualify the unfinished F4.3 browser path.
