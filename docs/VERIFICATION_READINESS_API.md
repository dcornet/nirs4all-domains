# Optional verification readiness v1 (D6)

`nirs4all_domains.verification_readiness` adds a source-bound companion to an
existing D1 warning/check. The standalone consumer displays its independent
dimensions in HTML/Markdown/JSON. Original D1/D2/D3 definitions, annotations and
hashes stay unchanged. A missing companion leaves historical view JSON unchanged.

| Dimension | Meaning and qualification limit |
|---|---|
| A. Observation evidence | Original D1 measurement availability and finding assessment, including contradicted findings. Copied from the validated parent, never inferred from authorization. |
| B. Verification inputs | `documented_accessible`, `requires_data`, or explicit unknown. Named requirements/references are declarations for this exact action. A new-analysis declaration of complete inputs must cover the parent's original prerequisites. Partial requirements remain unknown. |
| C. Protocol readiness | `qualified`, `not_qualified`, or unknown. Qualified declarations require a reference, intended use, units, split scope, transformations and evaluation population. This checks documentary completeness, not independent expert approval. |
| D. Execution authorization | `authorized`, `not_authorized`, or unknown. A grant requires explicit source-rights/resource/authorization references. It is a scoped declaration, not a permission issued by Domains. |
| E. Execution result | `executed`, `not_executed`, or unknown. Executed requires an original supplied receipt with matching canonical hash, source, parent annotation, observation scope, exact action and recorded execution. No analysis is run. |

Applicability is recorded separately. An inapplicable check is not prescribed;
the original observation remains. Unknown authorization is not a measurement
failure. Original `available`/`requires_information` flags keep their old meaning
and do not supply B/C/D/E. There is no global availability or risk grade.

Input accessibility is scoped to documented verification evidence/access
references, not a claim that raw data cannot exist in an authorized cache.
Documenting existing access may suffice; `requires_data` is not an automatic
acquisition instruction. Dimension counts overlap, include inapplicable candidate
checks and do not constitute a work queue.

## Public usage

```python
from nirs4all_domains.verification_readiness import interpret, validate_annotation
from nirs4all_domains.report_view import export_report

annotation = interpret(source_report, original_d1, request, receipts=receipt_objects)
validate_annotation(source_report, original_d1, annotation, receipts=receipt_objects)
export_report([{
    "case_id": "review", "report": source_report, "d1": original_d1,
    "readiness": annotation, "readiness_receipts": receipt_objects,
}], "results/review")
```

Run the compact public example without a numerical provider:

```shell
python scripts/run_verification_readiness_example.py --out results/tablet-readiness
python -m nirs4all_domains.report_view report.json --d1 warnings.json --readiness readiness.json --receipt stored=original-receipt.json --out results/review
```

The strict request lives in `$defs/request` of
`verification-readiness.v1.schema.json`. It binds the complete original report
and parent D1 hashes. Each check names its exact warning/check IDs, seven-field
observation scope, action, applicability, four independent states and references.
State invariants remain `computed`/null reason/non-null value, or
`unavailable`/explicit reason/null value. Unknown is not a false Boolean.
Partially documented protocol details retain known fields and explicit nulls;
they cannot be declared qualified until every required scope field is known.

For `action_kind=new_analysis`, the action must match the original check wording.
A narrower `review_saved_evidence` action may reference an actual saved review
receipt; its exact recorded action must match. This cannot establish that the
broader parent scientific analysis was performed. Receipts are supplied report
objects, never fetched or executed. JSON pointers only read their stated fields.

The standalone manifest accepts optional `readiness` and `readiness_receipts`
(receipt key to relative JSON path). All paths use the existing safe-path rules;
all sources/receipts are protected against overwrite. No D1 crosswalk means no
readiness attachment. D2/D3-only reports remain usable without inventing one.
Old strict D1/D2/D3 schemas are unchanged; standalone v1 permits the optional slot.

Hashes bind supplied content, not authorship, legal rights, physical independence
or scientific adequacy. The caller must document actual inputs and authority.
Synthetic grants/receipts in tests are explicitly artificial, not real permissions
or empirical executions. No risk probability, future-error estimate, model fit,
loader, scheduler or automatic follow-up is added.

## Qualification and bounded presentation

D6 freezes 38 cases: the original 20 D5 cases, ten valid synthetic dimension
counterexamples and eight expected source/check/receipt refusals. D5 remains
18 conforming/two nonconforming under its original criteria. D6 assesses its
own additional contract; those counts are not user effectiveness.

The real executed-action example is a prior D5 read-only manure evidence review.
The observed PC1 result remains one exceedance among 52 evaluation X. The new
multivariate/future-context analysis remains unexecuted and unauthorized. All
five D1 families retain missing metadata, negative evidence and conditional use.

A monolithic 30-case browser attempt reached the local working-set guard. The
qualified Research presentation uses three ten-case exports from the same
consumer, in original order, with every case/annotation retained. Complete
Markdown/JSON remain available. This is presentation partitioning, not scientific
sampling or a change in numerical evidence; the guard was not raised.

The separate Research expert package has 24 paired cases/48 variants, blank
response forms and coordinator-only expectations. Version labels/order are
masked only where possible; content/provenance may reveal condition. No reviewer
was recruited, contacted or impersonated: `human_review_status=not_executed`.
