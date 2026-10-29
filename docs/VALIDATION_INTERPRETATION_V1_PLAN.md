# Validation interpretation v1: implementation plan

This is a D2 product change over `810d3b5ed9a763ec40c540ea10cfc71828f13278`.
It interprets supplied evaluation facts and references existing evidence. It does
not select a split, infer identities, judge score quality or verify provenance.

## Expected behavior, frozen before implementation tests

- A within-experiment score describes that evaluation, not external transfer.
- New specimens require an evidenced, separated specimen/dependency unit;
  acquisitions of known specimens remain a different prediction population.
- Excluding an instrument, genotype, block or whole experiment supports only
  the stated kind of observed holdout. Crossed factors remain separate facts.
- An X-derived holdout describes geometry, never physical independence.
  Full-X group construction makes its interpretation transductive.
- Unknown intent yields three conditional readings without ranking protocols.
- X-only evidence describes structure/support, never prediction performance.
- Missing or conflicting declarations limit claims rather than creating facts.
- Annotation adds no numerical evidence. Existing report bytes, schemas and
  defaults remain unchanged. A content-bound optional sidecar works with both
  open and closed historical report schemas.

## Stages and validation

1. Add a pure Python deterministic interpreter, strict request/annotation schema,
   linked JSON annotation and Markdown CLI output. No numerical provider import.
2. Document the API and annotate the existing public alpha.17 tablet pilot.
3. Check the distinctions above, adversarial declarations, historical report
   compatibility, finite serialization and exact numerical/byte preservation.
   These are symbolic checks: no new numerical tolerance is introduced.
4. Run existing format, lint, workspace/native fixture gates, bridge integration,
   JSON/schema and package checks. Execute the Windows/Ubuntu GitHub matrix.
   Existing synthetic regression gates are software validation, not a new
   scientific campaign. Do not rebuild upstream native kernels.

## Resources

At most 512 MiB of incremental local engineering output (logs, packaging and
existing compiled application test artifacts), zero new scientific fits, PCA,
raw acquisition, campaign reservations or private evidence. Retain the current
combined ceiling of 20,289,597,121 bytes and campaign ceiling of 1,805,306,368
bytes, including the separate research checkout in accounting. Preserve 2 GiB
free per volume. Measure before/after and report actual usage. No ceiling
increase is planned; the owner's standing allowance is 5,000,000,000 bytes per
alpha if a later measured need requires a documented increase.
