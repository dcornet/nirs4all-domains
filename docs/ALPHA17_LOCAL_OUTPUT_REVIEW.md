# Alpha.17 local-output review

The identified 2026-10-18 execution was an assistant-authored PowerShell raw
configuration inspection through the execution tool. Its correlated tool
response contained generic development/cache/evidence directory locations.
It was not an application diagnostic, exception or native numerical message.
No raw matrix, target value or credential is identified in that configuration dump.
Exact values, event correlation and content receipts remain protected locally.

**Dissemination:** the tool response and persisted local agent transcript are
observed. A generic source-cache location also occurs in public scripts predating
the incident; that is distinguished from the newly displayed configuration.
Inspection of two existing package archives and 32 local/downloaded CI logs finds
none of the configuration locations. A Git/package scan cannot establish that
no external agent transcript exists. Separate terminal recordings and uninspected
upload destinations are not established.

**Retention:** the matching local transcript prefix remains accessible to the
local owner. Service-side retention, access and other copies are unknown from
these local inspections. Neither remote transmission nor its absence is inferred
merely from a path appearing locally.

**Mitigation:** `python scripts/inspect_private_roots.py <configuration>` prints
only a fixed shape-validity/unavailability code, without checking source rights
or certifying an ACL. A synthetic subprocess regression
exercises valid configuration, unknown fields, malformed JSON and missing files,
with no path, value or exception detail in stdout/stderr. The repository guidance
also requires projected JSON inspection. Raw shell bypass remains possible;
this is a bounded workflow correction, not a new logging/privacy framework.
No key rotation, cache relocation or historical deletion occurs.
