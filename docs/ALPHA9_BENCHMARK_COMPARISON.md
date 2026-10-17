# A frozen task can expose estimator-specific sensitivity

The [Perten suite](benchmarks/alpha9/perten-comparison-suite.json) was frozen
before evaluating Ridge. Its task/evidence IDs, original development content,
outer folds, target unit and metric are fixed. All three designs were already
declared in the frozen PLS record; every one is evaluated. No membership changed
after observing Ridge. The two-task structure-challenge suite also references
the preserved alpha.8 EcoSIS evidence; its numerical results are not re-estimated.

Methods 1.3.6 public `roles.Ridge`, catalog `models.regularized.ridge`, supports
centered X/Y and unscaled X. DAG-ML 0.3.41's published native Methods scheduler
executes inner CV/refit and N4ME replay. The secondary design fixes **alpha=1**,
with one candidate; there is no post-hoc alpha search or cross-family selection.
Native analytical centered Ridge (X′X=2, X′Y=6, alpha=1) predicts [0, 8] at [-2, 2]
within absolute 1e-10. Native inner lineage, forbidden retained X/Y changes and
the frozen content/fold contract are tested. No numerical algorithm is added.

| Same physical evaluation IDs / design | PLS RMSE | Ridge RMSE | Ridge change from its reference, 95% interval |
|---|---:|---:|---|
| Context-safe reference | 2.38729 | 2.61656 | — |
| Cereal closure holdout | 5.08562 | 2.84675 | 0.23019 [−0.34077, 0.55215] |
| Instrument-model closure holdout | 3.49175 | 3.43364 | 0.81708 [0.43571, 1.03168] |

On cereal holdout, Ridge minus PLS RMSE is **−2.23887 [−3.57777, −1.20988]**.
On the reference design their difference is 0.22927 [−0.49377, 0.69132]. These
are paired frozen-OOF whole-context intervals with 100 successful draws,
conditional on the 359 observed specimens / 17 blocks. Cereal holdout has only
two closure units; this is not uncertainty over arbitrary new cereal species.
Selected native fit artifacts are represented by hashes and scoped lineage.

Observation: cereal-holdout sensitivity differs strongly between these families,
while instrument-model holdout degrades both. Confidence: exploratory, conditional
on these fixed configurations and contexts. Consequence: a PLS-only interpretation
cannot certify estimator-independent benchmark suitability. Action: preserve
Perten as a structure-sensitive challenge and test a small prespecified set of
families/preprocessing chains on the frozen splits in alpha.10. Do not relabel it
low dependence because Ridge improves this one stress design.

No raw RMSE is averaged across EcoSIS LMA and Perten moisture units. No new
retained-target evaluation is performed. See [native comparison](benchmarks/alpha9/perten-family-comparison.json)
and [paired uncertainty](benchmarks/alpha9/perten-comparison-uncertainty.json).
