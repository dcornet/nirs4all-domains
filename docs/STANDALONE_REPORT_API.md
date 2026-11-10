# D4 standalone report consumer v1

[D6 verification readiness](VERIFICATION_READINESS_API.md) is an optional
source-bound companion over an original D1 check. Add `readiness` and optional
`readiness_receipts` to a case/manifest; the CLI accepts `--readiness` and repeated
`--receipt NAME=JSON`. Absence of the new slot preserves old view JSON exactly.
Observation, verification data, protocol, authorization and execution stay
separate; an available observation is not an executed analysis.

The [D5 qualification](D5_WARNING_UTILITY.md) refines presentation only: declared
objective/population/unit and actual split appear before findings. Checks for
unavailable findings remain readable, with original reasons and prerequisites.
Testability flags do not authorize or certify execution. View/companion schemas,
interpretation rules and hash validation stay unchanged; historical exports are
not rewritten.

`nirs4all_domains.report_view` reads existing reports and validates their original
D1/D2/D3 companions before presenting observations, plausible methodological
concerns, proposed checks and scientific limits. It produces standalone HTML,
Markdown and JSON. It changes no source report and fits nothing. No Preflight,
Studio or Datasets code, package or UI is modified.

```shell
python -m nirs4all_domains.report_view existing-report.json --d1 warnings.json --out results/review
python -m nirs4all_domains.report_view --manifest cases.json --out results/cohort-review
```

Both commands create new `.html`, `.md` and `.json` files. Existing outputs,
source/annotation overwrites and unsafe manifest paths are refused. A manifest
contains `title` and a `cases` list. Each entry has a unique `case_id`, optional
`label`, and paths `report`, optional `d1`, `d2`, `d3`, `comparison_report`, all
relative to that manifest. Unknown fields fail rather than silently dropping an
annotation. The HTML opens locally without a server or JavaScript runtime;
navigation and disclosure sections remain usable offline.

```python
from nirs4all_domains.report_view import render_report, export_report

cases = [{"case_id": "sample-review", "report": report, "d1": warnings}]
rendered = render_report(cases)  # view JSON object, HTML and Markdown strings
artifacts = export_report(cases, "results/review")
```

## Source and companion contracts

| Input | Exact validation | Presentation limit |
|---|---|---|
| D1 | Existing `structural_warnings.validate_annotation(report, annotation)` | Original source/population/representation, provenance and all five owner states; no new warning engine |
| D2 | Existing `validation_intent.validate_annotation` | Existing conditional alternatives and supported/unsupported claims; no split choice or fabricated calibration |
| D1-linked D2 | Reuses D1's already computed `validation_intent` when no separate D2 is supplied | A supplied D2 must match that exact intended use/evidence |
| D3 | Existing comparison validator over both explicitly supplied reports | Original performance, units, baseline, matching/compatibility and limits; no new score, ratio or fitting |
| D2 plus D3 | Declared deployment facts must agree with D3's reference reading | Separate metric references remain scoped to their evaluations |
| D1 plus D3 in one case | Refused in v1: use separate cases | A common report hash does not by itself qualify a crosswalk between X populations and predictive evaluation populations |
| Preflight schema1 | Read-only projection of original scalar metrics, identities, parameters, native statuses, findings and limits | Native metrics are not renamed to Domains metrics; non-scalars remain in the source report; missing companions remain unavailable |
| Missing dataset/content identity | Explicit unavailable identity, retained full report hash | No identity inferred from a filename, common name, metric count or native library record ID |

Every public rendering/export entry point takes original reports and companions
and executes owner validation again. Exported view JSON is a presentation record,
not a substitute for source validation. Hashes establish content linkage rather
than authorship or source authenticity. Qualifier/evidence declarations keep the
limits of their original owners. No browser-side scientific interpretation or
HTTP service is added.

## Coverage and safety

The view names exact declared canonical dataset IDs, synthetic identities,
dataset/source X views, documented provenance groups, original-source references,
case counts, distinct source-report/annotation hashes, and owner warning states.
Original databases and independent-study counts stay `unknown` when unestablished.
Unidentified cases are counted separately. Multiple views, representations,
targets, intended uses or warning records are not independent datasets/studies.
Counts describe the saved cases being presented, not risk prevalence or new
scientific observations. Historical D1's347/78/80 counts are not D4 effectiveness.

HTML escapes all source strings and includes no executable script; its CSP blocks
scripts and network resources. Markdown escapes free text, links/HTML syntax and
code fences. Original numerical evidence remains unchanged. The JSON contains
exact validated companions and hash-bound source references, not source matrices
or raw prediction arrays. Original report bodies stay in their original files.

Source-specific permissions still govern publication. Local rendering does not
grant redistribution. The worked Research cohort reuses existing permitted
aggregates; negative, contradictory, all-noise and unavailable cases are retained.
No global danger color, risk grade, probability of failure or universal validation
recommendation is produced. Absence of a warning is not a safety certificate.
