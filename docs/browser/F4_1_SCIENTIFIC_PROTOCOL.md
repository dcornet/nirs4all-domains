# F4.1 factor–PCA association protocol

Frozen before numerical implementation. Base: main
`c7e2230066a114114a83bfb9a73eb7974d0dd2dc`; Domains only. Preflight 0.1.6,
Methods 1.3.13 / ABI 2.20 and all historical protocols/tolerances stay fixed.
The explicit F4.1 request requires FR/EN presentation, overriding the general
English-only convention for those user-interface translations.

## Estimands and analysis populations

The additive wire protocol is `domains.browser_factor_association.v1`.
Its default is an observation/acquisition-weighted descriptive association
between a selected declared M field and **each resolved component** of a
previously executed raw PCA. It is not an association with total spectral
variance, a global spectral-space test, a causal effect or calibration risk.
Do not sum component associations, choose the strongest component or tune PCA
using M/Y. Use every resolved component in the source's fixed component rule;
requested but unresolved components retain an unavailable reason.

- Main population: all original train X rows fit the PCA independently of M/Y;
  the association receives their scores and selected train M only.
- Explicitly unpartitioned data: descriptive exploration of that entire declared
  source, without inventing train/test partitions.
- Global train+test: separate explicit association consent and an already
  explicitly transductive PCA. Never substitute it for train-only evidence.
- Prediction rows never enter these operations. No X matrix or Y values enter
  the association request. Source/partition manifests contain declarations only.
- A missing M value removes that pair for that factor's statistic, with exact
  counts and a used-key fingerprint. It never refits PCA, removes observations
  from the dataset or imputes values. Different denominators are explicit.
- Factor and score keys must form the same unique population before missingness
  filtering. Keyed reordering is allowed; ambiguous, extra/test or absent keys
  are errors. Zero is a valid continuous value, not missing.

Only explicitly selected factors run. Known Y-derived M and original Y fields
are refused before a provider call. Unknown derivation/provenance can support
descriptive analysis with an explicit limitation, never qualified inference.
Identifiers/dependency declarations remain distinct from experimental factors.
The reserved origin declarations `Y`, `Y_train`, `Y_test`, `target` and `targets`
(case insensitive) explicitly identify target provenance and are refused even
if a contradictory derivation flag says false. Arbitrary source names do not
prove non-target provenance. Numeric categorical/dependency labels outside the
JavaScript safe-integer range are refused: declare such identities as strings,
without row deletion or silent conversion, to avoid native/browser label merging.

## Owner kernels and descriptive quantities

Categorical factor: deterministic type-preserving level coding, followed by
Methods `preflightFactorAssociation(codes, scores, false, 0, 0)`. The target is
a continuous score vector, even when M is categorical. Report owner eta²,
F/df/counts when defined, level sizes, missing counts and singleton/saturation
warnings. Eta² is between-level separation of the particular score vector;
it is **not** the fraction of total X variance explained by M. Saturated
singletons may give eta²=1 while F is undefined. Keep the descriptive value
and mark the degenerate contrast; never interpret it as useful explanation.

Continuous factor: Methods `statsCorrelationTest(M, scores, method, 0, 0)`.
Pearson is the explicit default for linear association; Spearman is an explicit
alternative for monotone rank association, never an automatic fallback.
Preserve unit and owner distinct-value counts. Constant vectors, numerical
domain refusals and undefined statistics keep null/reason values. Do not
rescale, clip, transform or replace a refused kernel silently.

Both calls have zero permutations. Owner NaN means an unavailable slot, never
JSON NaN, p=0 or p=1. An undefined auxiliary F does not erase a defined eta².
Methods owns every association, correlation, exact test, correction and numeric
summary. Rust owns access/identity checks and literal documentary counts;
frontend code owns display only.

Signed correlation refers to the **recorded** PC orientation. Sign reversal
changes signed r/rho and not its strength. Equal/near-degenerate eigenspaces
can change component-wise associations under basis rotation; retain the PCA's
resolution and warn against stable physical attribution to individual PCs.
Do not orient PCs using M. Native/WASM association comparisons use the same
frozen source-score vectors, separately from existing PCA geometry parity.

## PCA provenance and actual access

The request carries the original qualified raw-PCA evidence, its scope and
content fingerprints, ordered fit keys, score fingerprint and execution
reference. Rust verifies the original evidence checksum, dimensions, finite
resolved scores, component status, dataset/content binding and key population.
Scoped PCA additionally requires the matching successful train/global receipt;
the legacy unpartitioned source must identify a complete unpartitioned fit.
Imported saved/unknown PCA coordinates are not silently recycled by the UI.
Original evidence is hashed for lineage; only aligned score vectors and admitted
M values reach the statistical provider. No PCA, HDBSCAN or support refit occurs.

As in F4.0, content hashes are consistency/provenance bindings, not signed proof
that an arbitrary caller's supplied history or physical identities are true.
The product path uses its own retained runtime results; it does not promote an
unverified saved source into an executed fit. A stale hash, changed population,
unknown source, wrong scope or unresolved component is refused before statistics.

Receipts record methods/version/parameters, actual score/M/key fingerprints and
sizes, missing exclusions, source-PCA/fit references, actual provider calls,
dependency evidence, analysis unit, known/unknown independent-unit support,
no-X/no-Y access and zero PCA refits. They contain no raw M vectors or codes.

## Inference is a separate, conditional contract

Three states are distinct: descriptive only; inference unqualified; inference
conditionally admissible under a supplied, externally qualified design record.
The default UI and API mode is descriptive only. A group ID, unique row key or
checkbox alone never proves exchangeability or corrects pseudoreplication.

The only candidate inferential design in v1 is unrestricted exact permutation
of **one acquisition per independently qualified unit**, conditional on the
recorded X/PCA, with a prospectively declared factor-by-resolved-PC test family.
The external qualification record must identify its evidence/content, unit and
population, missingness rule, known dependencies, selection timing and family.
Domains validates mechanical coherence and records the external assumptions;
it does not independently authenticate study documentation or prove independence.
The conditional qualification must remain visible beside every p-value.
The browser attaches a separate local design-record JSON after PCA (64 KiB
maximum); it is never part of the IO content fingerprint. Putting a record's
dataset/PCA hashes inside its own hashed import spec would create a circular
binding. Attachment validates shape, grants no independence and launches no
operation. Only an explicit subsequent request can ask Rust to check scope,
dependencies and the prospective family. Dataset reset revokes the attachment;
invalid replacement revokes the previous record and restores descriptive mode.

Require complete values/units, no repeated physical/reference/repetition units
or unsupported blocking constraints, explicit non-Y provenance, a complete
predeclared family and explicit inference request. Unknown units, post-exploration
selection, missingness, conflicts, repetitions, hierarchy or unsupported groups
make only inference unavailable; descriptive results remain usable. No bootstrap,
aggregation or custom constrained/random permutation is substituted.

Exact inference is bounded to at most eight observations, 40,320 arrangements
per test, four explicitly selected factors and all source-resolved PCs (at most
the existing source component budget). Use Methods `statsFactorAssociationExact`
or `statsCorrelationExact`, with their distinct-arrangement/tie/tail conventions.
If any declared family member is degenerate/unavailable, do not invent a p=1
to complete the family. Keep family inference/adjustment unavailable with its
reason. For a complete admissible family use owner Holm FWER adjustment;
its arbitrary-dependence validity suits these correlated PC/factor tests.
BH is inventoried but no FDR capability is qualified in this protocol.

These are conditional tests of score–factor association, not an independent-
population guarantee or causal attribution. Their p-values are not risk scores;
no automatic significance threshold, preprocessing remedy or split rule is added.

## Dependencies and presentation/export

Literal level counts and pairwise cross-tabulations describe observed/absent
combinations, nesting, one-to-one confounding and imbalance. They do not discover
causal mechanisms or certify that all relevant factors were supplied. Specimen,
reference, repetition and declared dependency fields quantify repeated acquisitions
separately from physical units; an independent effective sample size is not
invented. See [dependency rules](F4_1_FACTOR_DEPENDENCY_RULES.md).

The reading always separates observation, hypotheses, limitations and proposed
checks. Display categorical levels/counts and continuous unit/range with a coherent
color scale and separate missing swatch. Graphical factor changes are display
only, never a new fit or silent change of association statistics.

Default exports retain aggregate statistics, essential limitations, original
admissible machine evidence and uncolored PCA. They omit raw X/Y, per-row M
vectors/codes and M-colored observation mappings. Observation-level factor
coloring in an exported figure requires a separate explicit content/factor-
bound authorization under the source's terms; selecting all report supplements
does not grant it. This is a local export declaration, not scientific independence
or permission to publish restricted source data. Existing historical source
objects remain intact. No arbitrary page cap or suppression of adverse results.

## Frozen reference expectations and tolerances

Use deterministic public synthetic fixtures only; no real-data campaign.

| Case | Expected behavior |
|---|---|
| Scores proportional to centered [1,2,3,7,8,9], factor 000111 | eta²=27/29, F=54; B=0 and p unavailable; owner v1.3.13 reference |
| Centered [-3,-2,-1,1,2,3], factor 010010 | group means equal, eta²=0; no global absence-of-structure claim |
| M linearly/monotonically aligned with a resolved PC | absolute Pearson/Spearman=1; sign follows recorded basis |
| Constant M, one category or constant admitted scores | undefined owner statistic remains unavailable, with counts |
| Unique factor level per nonconstant score | eta²=1, F undefined; saturated/no informative inferential contrast |
| [1,2,3,4] scores, factor 0011 under admissible independent design | eta²=.8; 6 distinct arrangements; exact p=1/3 |
| Four distinct perfectly aligned continuous values | 24 arrangements; exact two-sided p=1/12; max absolute r=1 |
| Repeated specimen, shared reference, unknown unit or inadmissible plan | descriptive retained; no exact/correction call or numerical p |
| Reordered M, missing M or no-train factor | exact keyed alignment; documented subset, or unavailable factor |
| Instrument/lot one-to-one; partially crossed factors | literal confounding/crossing evidence; no causal attribution |
| Stale PCA hash, wrong fit keys, unresolved PC, forbidden Y/test | refusal before provider; unrelated results retained |

Analytical scalar/native-WASM tolerances are absolute/relative 1e-10 (existing
owner factor analytic fixtures retain 1e-12); identities, access, counters,
arrangements, hashes and same-input replay are exact. Existing F4/PCA comparison
tolerances and frozen reference files do not change. Add negative, degenerate,
missing, sign/basis, permutation-eligibility and confidentiality adversaries
before declaring executable or scientific qualification.
