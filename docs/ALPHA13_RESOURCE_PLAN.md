# Alpha.13 resource admission plan

Read-only preparation at baseline `ebb1b9b8a45d01618931d846d059641701cac7da`:
13,678,049,640 workspace bytes under the approved 13,873,678,017-byte ceiling;
195,628,377 bytes remain. C: and D: have 161,443,471,360 and 353,074,810,880
free bytes. Methods 1.3.6 / ABI 2.19, DAG-ML 0.3.41 and Datasets 0.3.11 remain
the qualified providers. No new spectra or models have been acquired/fitted.

The previous versioned Rust test build grew the workspace by 212,104,726 bytes,
before rustdoc/package growth. The present margin cannot conservatively cover
that build plus alpha.13 evidence. Request only a 512 MiB workspace-ceiling
increase to **14,410,548,929 bytes**, with no historical cleanup or migration.
Allow 320 MiB fixed tooling/build growth; keep scientific source acquisition,
scratch and compact evidence within the unchanged campaign scheduler.

Existing cumulative reservations are 427,393,916 of 536,870,912 bytes. A bounded
alpha.13 envelope of at most **96 MiB additional reservations** would bring them
to 528,057,212, leaving 8,813,700 bytes for contingencies. These are proposed
upper envelopes, not advance reservations or automatic experiment admissions:

| Work | Additional reservation envelope |
|---|---:|
| Official source acquisition if separately rights-admitted | 32 MiB |
| Analytical/design and controlled-X calibration | 32 MiB |
| Bounded real X-only extension/stability | 24 MiB |
| Supervised pilot only after its separate scientific gates | 4 MiB |
| Publication/replay evidence | 4 MiB |

Keep 256 MiB/task, 4 MiB persistent evidence/task, serial execution and 2 GiB
free on every used volume. Reuse exact caches; do not copy X per draw/fold/target.
Actual source/shape/rights and controller costs must be admitted before each stage.
Sources whose original archives exceed these bounds remain explicit blockers.

Calibration first uses the frozen alpha.12 mechanisms and identity-only design
simulation. A provisional upper count is 9 mechanisms × 3 perturbation seeds ×
2 representations × 2 fractions × 80 draws = 8,640 PCA refits, with shared
prefix reuse for the original 20-draw comparison and two HDBSCAN attempts per
PCA fit. This is a sizing bound, not a frozen scientific selection. Analytical
calibration may justify a smaller predeclared suite. No real fit follows before
the revised design is qualified and frozen. Bound the first revised real study
to three selected source populations (at most 960 PCA refits at that design),
plus affordable raw/SNV reference profiles for independently admitted sources.
No bank-wide model campaign; TabPFN remains deferred.

Section 9 of the owner's alpha.13 mission forbids implicit workspace increases.
The owner approved this +512 MiB ceiling on 2026-10-18. The decision and fresh
disk measurement are retained in the private approval receipt; the portable
policy is `configs/bank/storage-policy-alpha13.json`. Other limits are unchanged.
The earlier preparation measurements above describe the proposal, not current use.

Execution closes at 88,894,038 additional reserved bytes, below the 96 MiB bound;
cumulative campaign reservations are 516,287,954 / 536,870,912 bytes. The unused
pilot envelope covers the compact-publication retry rather than model fitting;
total/task/evidence limits do not change. The initial fixed-build allowance was
an estimate: actual versioned compilation grew more, and each validation guard
checked the approved ceiling including selected external X files. The final
local/package snapshot is 14,382,291,979 combined bytes, with a separate Git/CI
metadata guard before completion. No implicit budget increase or cleanup occurs.
