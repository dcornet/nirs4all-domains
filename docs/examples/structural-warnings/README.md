# Worked conditional warning report

The [tablet report](tablet.report.json) reuses qualified UCPH aggregate evidence:
batch-PC1 eta²0.979306 with weak flat-partition ARI0.038111. It contains no raw
spectra, individual labels, target or newly fitted model. The
[request](tablet.request.json) asks about future production batches; the
[result](tablet.annotation.json) and [rendering](tablet.interpretation.md) explain
why a matching batch contrast could be relevant and which original memberships,
physical/reference dependencies and confounding still need checking. They do
not infer leakage or predict degradation.

Run the CLI shown in [the API reference](../../STRUCTURAL_WARNINGS_API.md) to
replay the interpretation without fitting. Change only the validation intent to
see why within-experiment proof of concept and future-context prediction prompt
different checks. When intent is unknown, several conditional readings remain.

[scientific-cases.json](scientific-cases.json) preserves five named source
snapshots, including their native method/settings, input/result hashes and original
source links: UCPH tablet, Cucurbita two-stress leaf/canopy, Cedar Creek leaf litter,
Cucurbitaceae fruit and milk composition. Multiple factor rows are not additional
datasets or independent studies. The source-specific terms and attribution of
these derived scientific aggregates remain applicable; the software license is
not a replacement data license. Original source references are embedded in each
request. No raw data are redistributed.

Milk's Cow_ID correspondence is kept separately from its nearly-zero partition
agreement. Original split controls, missing levels, high cardinality and repeated
acquisition weighting remain in their snapshots. This example is conditional
scientific guidance, not evidence that any one validation protocol is always best.
