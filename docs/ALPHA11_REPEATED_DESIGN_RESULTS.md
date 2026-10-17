# Repeated fitted-design sensitivity, separate from OOF bootstrap

Protocol: [domains.repeated_design.v0.1](ALPHA11_REPEATED_DESIGN_PROTOCOL.md).
The [pre-score manifest](benchmarks/alpha11/litter-evaluation.json) fixes three
seeds, outer/inner folds, candidates, content and paired preparation identities.
All 298 development IDs receive exactly one OOF prediction in each design.
**894 predictions are 298 unique physical samples**, not 894 independent votes.
The 24 development blocks are declared plot/context groups; independent biological
group count remains unidentified because GEN collection and assay maps are missing.
The raw result field `n_independently_challenged_components` counts these declared
validation components; it is not a verified biological effective sample size.

| Seed | Outer train sizes | Outer validation sizes | Null RMSE |
|---|---|---|---:|
| 17 | 62 / 270 / 264 | 236 / 28 / 34 | .519287 |
| 31 | 86 / 264 / 246 | 212 / 34 / 52 | .490437 |
| 47 | 84 / 254 / 258 | 214 / 44 / 40 | .481937 |

The large GEN block drives this imbalance. It is kept whole. Per-group scores,
identity-matched prediction SDs, null-relative errors and complete selected
settings are in [results](benchmarks/alpha11/litter-model-results.json).
Small groups can have unavailable R²; they are never assigned an arbitrary score.

PLS selects 2/2/2, 3/3/2 and 3/3/3 components. Ridge selects .01/.01/.01,
1/.01/.01 and .01/.0001/.0001. SNV/PLS selects 3/3/3, 3/3/3 and 3/2/3.
Boundary selections are retained without extending any grid. Intact RMSE ranges
are .3150–.3397, .1870–.2551 and .2627–.2923 respectively. See
[the paired table](ALPHA11_REAL_DATA_PILOT.md) for preparation response.

Three repeated designs measure empirical split/refit/selection sensitivity on
this fixed population. Their range and SD are descriptive, not confidence limits
from three independent studies. They do not identify new-source uncertainty or
an unseen-biological-group error distribution. Perten's two cereal closures
remain incapable of such inference, regardless of extra fits.

The separate seed17 metadata/residual control uses 100 paired frozen-OOF block
draws. Its intervals condition on those executed fits and declared blocks;
they exclude refitting and unknown biological dependencies. They are not pooled
with repeated-design variation. Whole-vector target intervention gates and true
factor-closure failures remain explicit.

Primary experiments use **324 model fits**, with native preprocessing additional.
One residual-control study adds 30 fits while reusing the exact original spectral
OOF. One complete raw-PLS seed17 design freshly replays 298 predictions, 297
paired predictions and selected artifact hashes exactly, adding 30 fits.
Primary results are then reused from a content/provider/controller-verified
checkpoint; no complete second campaign is claimed.
