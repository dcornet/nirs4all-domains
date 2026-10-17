# Alpha.12 structural stability

The frozen [protocol](ALPHA12_UNSUPERVISED_PROTOCOL.md) selected seven sources
using X-only diversity before new fits. All 560 PCA refits and 1,120 HDBSCAN
attempts completed: 20 draws at fractions .6 and .8, raw/SNV, two settings per
shared PCA fit. The 28 [summary files](benchmarks/alpha12/stability) retain each
draw's shared identity support, native ARI including/excluding noise, noise
agreement, membership summaries and a bounded co-membership panel.

Of 56 representation/fraction/setting summaries, four meet the operational
robustness gates, two have adequate support but fail quality gates, and 50 have
insufficient information. The four supported combinations are SNV/.8 for both
settings in Biotron and Cartilage; the two fragile combinations are raw/.8 in
Biotron. **None of seven sources meets the overall all-combination gate.** This
does not establish seven unstable sources or seven low-susceptibility sources.

All 56 have complete execution support. Forty-eight fail the pair-support gate,
nine fail eligible-ARI support, and 52 fail at least one quality criterion;
these counts overlap. Small reference fragments can receive too few panel pairs.
Insufficient information takes precedence over a fragility interpretation when
support is missing. Metric-level changes remain observable even then.

## Power and interpretation limits

The registered requirement of at least ten joint exposures per pair is demanding
with only 20 draws at fraction .6. For simple observation subsampling of m from N,
a distinct pair's expected joint exposure is `20*m*(m-1)/(N*(N-1))`.
At N=120 and m=72 this is approximately 7.16. This analytical design limitation
can prevent a perfectly reproducible partition from meeting the .6 gate. The
bounded panel also allocates little support to small fragments. These are
limitations of the chosen assessment, not evidence of biological instability.
No thresholds, populations or draw counts were relaxed after seeing results.
A future protocol should calibrate pair exposure before additional real fits.

The [controlled suite](benchmarks/alpha12/controlled-mechanisms.json) contains
16 mechanisms, 18 size-specific cases and a 20-draw .8 separated-cloud positive
control, which meets both settings' robustness gates. It establishes useful
geometrical responses, not calibration of all possible mechanisms, fractions
or a predictor of supervised failure. Continuous/noise/all-noise cases are
retained. The alpha.5 regular-one-dimensional continuum gate was not qualified
on these populations, so continuum classification remains unavailable.

Cartilage draws retain whole original-audited location blocks: 869 locations,
2,605 acquisitions, conditional on five joints. Missing donor/assay closure
prevents biological uncertainty. The other six sources use observation-level
algorithmic subsampling and make no independent-biological-sample claim.
CABO fresh/ground are related source views; physical identity overlap between
those catalog views remains unknown. They are not two independent studies.

The sentinel records remain per draw. Remaining batches use the independently
versioned [restart transport](ALPHA12_EXECUTION_NOTES.md), atomic prefix checksums
and the same selected subsets/providers/thresholds. No completed draw was rerun
to improve a classification. Failure/restart tests reject corrupted or conflicting
prefixes, and failed-attempt reservations remain charged.
