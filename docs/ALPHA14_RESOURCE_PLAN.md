# Alpha.14 resource proposal — 2026-10-18

Read-only audit at `dd4496718f449cd8d02839fa7b33ac155fbbcccb`: workspace
14,363,191,956 bytes; combined with the already participating external X files,
14,384,864,178 bytes. The approved ceiling is 14,410,548,929 bytes, leaving
25,684,751 bytes. C: and D: have 161,510,666,240 and 352,382,689,280 free bytes.
The cumulative journal reserves 516,287,954 / 536,870,912 bytes, leaving
20,582,958 bytes. No new spectra have been accessed or acquired in this audit.

Propose a **1 GiB ceiling increment**, to **15,484,290,753 bytes**, and a
**256 MiB cumulative campaign increment**, to **805,306,368 bytes**. These are
proposals awaiting the owner's explicit approval, not current policy.
Preserve all failed/completed reservations. No journal reset, deletion or migration.

Allow up to 640 MiB for versioned tooling, tests and packaging, 128 MiB for
additional participating existing cache files, and the remaining measured margin
for scientific scratch, evidence and Git metadata. Count external participating
files and the protected evidence root in the same combined ceiling. Stop and
review costs when the measured envelope is inadequate; free disk alone does not
authorize raising it.

The new scientific reservation envelope is at most 256 MiB, including failures:
64 MiB additional source-cache bytes, 128 MiB cumulative scratch reservations,
32 MiB local/public evidence and 32 MiB contingency. These are upper envelopes,
not pre-reservations or permission to acquire a source. At most 24 newly admitted
source views enter initial raw/SNV screening; at most three independently scoped,
cost-admitted views enter the unchanged B60 deeper protocol. Select by rights,
population diversity, full-source feasibility and frozen priorities before fits.
No outcome-based source choice. Preserve complete populations and axes.

Keep 256 MiB/task, 4 MiB persistent evidence/task, one scientific task at a time
and 2 GiB free per participating volume. Source-sized estimates precede each
execution. Unknown or oversized sources remain explicit blockers. Protected
evidence and mapping secrets will be outside the Git workspace in a separately
configured owner-only directory; source X remains in its existing authorized
Datasets/canonical cache. Do not copy matrices into the evidence root.

This proposal covers privacy engineering, rights screening and admitted X-only
analysis. **No supervised pilot is budget-admitted**: the mission requires a
separately reviewed exact pilot after rights, dependency and task gates pass.
No TabPFN installation, weights or fitting. No external private-data computation.

Section 13 of the alpha.14 mission explicitly requires owner authorization before
policy increases. Privacy and metadata engineering can proceed under the existing
limits while that decision remains pending. No higher limit takes effect until
the owner's answer is recorded locally.

The owner approved both increments on 2026-10-18. The active policy is
`configs/bank/storage-policy-alpha14.json`; the exact decision receipt is local.
The pilot remains excluded from this approval. Permission for local analysis is
recorded separately and does not authorize public release of private results.
