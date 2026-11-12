# Optional decision reading v1 (D6.1)

The existing `nirs4all_domains.report_view` consumer accepts a Boolean
`decision_summary` on each case. The CLI also accepts `--decision-summary` for
individual reports or all cases of a manifest. Default behavior and historical
view JSON remain unchanged. Existing D1/D2/D3 and D6 annotations are read and
validated without rewriting them.

```shell
python -m nirs4all_domains.report_view report.json --d1 warnings.json --readiness readiness.json --decision-summary --out results/decision
python -m nirs4all_domains.report_view --manifest cases.json --decision-summary --out results/decisions
```

```python
from nirs4all_domains.report_view import export_report
export_report([{
    "case_id": "review", "report": report, "d1": original_warnings,
    "readiness": original_readiness, "readiness_receipts": receipt_objects,
    "decision_summary": True,
}], "results/decision")
```

The optional output object `decision_summary` has protocol
`domains.decision_summary.v1`. Its five prose fields distinguish observation,
conditional deployment relevance, documentary checks now, further requirements
and unsupported conclusions. Mechanism rows, factor questions and selected D6
readiness records provide the exact source-scoped distinctions. One semantic
object and section mapping drives HTML, Markdown and JSON. HTML begins with the
decision reading and keeps the original scientific evidence in an expandable
section, offline without scripts or network resources.

## Scientific interpretation contract

- `density_parameter` describes the original HDBSCAN settings and parameter ARI
  on one representation. It is not evidence of a preprocessing effect.
- `representation` requires the original admissible, observation-matched
  qualification. Cross-representation partition ARI stays separate from density
  ARI. Neighborhood rows require available values and matched query qualification;
  their recorded metric is **mean neighbor intersection / k**, not Jaccard.
- All-noise, trivial partitions, unavailable comparisons and contradictions keep
  their original states. `active_sensitivity_caution` concerns this descriptive
  comparison only, never a priority, severity, probability or universal stability
  verdict. A contradicted, unavailable or non-informative comparison does not
  acquire an active sensitivity caution. No numerical threshold is introduced.
- Conditional factor questions use actually documented non-Y associations and
  the declared objective/relevance. No dataset-name routing or universal
  factor-to-split rule is used. Unknown intent first asks which unit/context will
  be predicted. Factor labels do not certify physical/reference independence.
- Date/measurement-date fields with identical recorded statistics are flagged
  as possible aliases, not independent confirmations. Aggregate equality does
  not prove membership equality. Site/date associations do not establish an
  unmeasured treatment or preparation effect; qualify crossed factors first.
- Documentary prerequisites, reading existing evidence, proposed new calculation
  and receipt-backed execution remain distinct. D6's selected checks are not an
  exhaustive evaluation of useful investigations. Inapplicable checks are not
  prescribed; unknown applicability is conditional. Partial inputs never become
  complete. The stored `new_analysis` action label keeps its historical meaning.
- False/missing acquisition, physical-unit and reference-unit flags describe
  missing information in the carried qualified evidence. Absence from the
  original database is not established. No source search or acquisition runs.

When both raw and another representation are supplied in one export, the
consumer may carry existing cluster counts across the same declared canonical
content/source/population/scope/count. The second record must be among the
qualified comparison's representations; density configurations, native provider,
PCA configuration, method owner/version and recorded query scope must match.
Settings are matched as records, not inferred from array positions. These are
declared X-scope comparisons, not physical identity certification. A single-case
export without the peer leaves `paired_representation_counts` empty. Historical
source and annotation hashes remain unchanged.

## Compatibility and qualification

No source/companion schema, metric, scientific finding, preprocessing, numerical
kernel, fitted model or split is changed. The standalone v1 schema permits one
optional presentation field. Caller-supplied summary prose is not an accepted
input; callers provide only the flag plus original reports/companions.

Use a bounded number of cases per HTML part when a full report exceeds local
browser memory limits. Pair related representations within the same part if
their counts are being displayed together. Retain complete source/case coverage;
presentation grouping is not scientific sampling. New presentation variants do
not add empirical replications.

The separate D6.1 matrix qualifies 24 simulated-purpose cases from the unchanged
D6 expert corpus. The counter-review is `ai_simulated_non_blinded_not_independent`;
`human_review_status=not_executed`. Neither these tests nor the original D5 18/20
and D6 38-case outcomes measure user effectiveness. The original expert v2 package
and its blank forms remain unchanged for a later genuine independent review.
