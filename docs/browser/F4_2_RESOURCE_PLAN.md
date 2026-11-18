# F4.2 staged engineering plan — 2026-11-18

Owner authorization: 4,000,000,000 bytes **total cumulative engineering growth**,
preserving the initial 18,663,326,977-byte baseline and all charged consumption.
The effective aggregate cap stays 25,000,000,000 bytes, authorized maximum 50 GB,
and physical reserve 2 GiB per participating volume. No scientific reservation.

Before amendment: actual aggregate 20,103,414,966 bytes; charged engineering
1,440,087,989 bytes. Indicative new remaining allowance is 2,559,912,011 bytes;
the authenticated amendment performs a fresh measurement and records actuals.
Science remains 2,015,788,498 / 2,023,410,176 bytes, journal SHA-256
`237f8a7fedd5f83eff4a850e78900a892e640fd2582bac099520e39108d25e0c`.

Stages: audit/transport/controller tests and source changes (up to 128 MiB);
reuse existing dependencies and a dedicated/reusable reduced-debug Rust/WASM
target for local synthetic tests (up to 1.5 GiB additional); browser/report
artifacts, comparison and compact hosted proof receipts (up to 512 MiB).
Measure/admit before builds and after substantial output. These staging estimates
share the cumulative allowance; they do not create scientific reservations or
reset accounting. Stop and explain actual usage at a bound; no hidden cleanup.

Keep every Research result, frozen fixture, journal, proof, Git object and active
worktree. No real-data numerical operation, VAE/SSL/AOM, upstream edit or version
change. Public owner dependencies may be fetched only as required for software
qualification; no raw dataset is acquired. Local tests are useful and authorized;
hosted Windows/Ubuntu completion and actual Pages checks remain separate proof.
