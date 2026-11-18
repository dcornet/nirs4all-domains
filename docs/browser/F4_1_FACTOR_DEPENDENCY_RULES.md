# F4.1 factor dependencies and conditional inference

This is an additive pre-implementation rule record; the controlling estimands
are in [the scientific protocol](F4_1_SCIENTIFIC_PROTOCOL.md). No categorical
column alone establishes a physical dependency, a required group split, causality
or an independent unit. The current task preserves every imported observation.

Descriptive factor–PC associations count acquisitions/observations. Complete
declared specimen IDs permit a **declared unique-specimen count**, not an effective
independent n. Repeated specimen/reference/repetition identities are reported;
no specimen averaging, de-duplication or row permutation corrects them by default.
Unknown identities, missing IDs and unknown relevant factors remain unknown.

Pairwise documentary tables use complete pairs of selected/context M fields,
with original counts and missing denominators. One-to-one level correspondence
is literal total confounding of these observed labels. A level mapping in one
direction describes nesting. Partial crossing and absent combinations are
reported without asserting an experimental design or mechanism. Enumerate absent
combinations only within a fixed output budget; otherwise report their exact
count and the enumeration limitation, retaining all observed combinations.

Inference needs a separate external design-qualification record, explicit
request and prospective complete family. Mechanical validation requires:

- exact dataset/PCA population and complete aligned M;
- named unit field, evidence URI/content hash and external qualification basis;
- exactly one row per qualified unit, with no unknown physical/reference support;
- no repeated meaningful unit/reference/repetition or unsupported blocking
  constraint among supplied dependency declarations;
- explicit non-Y provenance and no post-association factor/component selection;
- all resolved PCs under the source's M-independent fixed rule;
- a finite complete nondegenerate family inside the exact enumeration budget.

This verifies formal consistency, not the truth/authenticity of physical metadata
or study documentation. Outputs remain conditional on that external record and
unrestricted exchangeability under the null. The ordinary UI has no default
qualified record; inference is unavailable rather than guessed from group labels.
No constrained permutation implementation or causal model is introduced.

Missingness, repeated acquisitions, unexplained references, unknown units,
conflicting qualification, degenerate/saturated factors, unsupported plans or
over-budget exact tests leave p-values/adjustment unavailable. They do not
erase valid descriptive statistics. Holm covers the prospectively named complete
factor-by-PC family; no BH/FDR or arbitrary p-based risk threshold is claimed.

## Individual M export boundary

Default JSON/HTML/Markdown contain aggregate association/dependency evidence and
fingerprints, not individual M vectors/codes or factor-colored row mappings.
Existing legacy/historical scientific source objects are preserved.

The optional `domains.factor_color_export.v1` declaration is local to the current
dataset content, factor and PCA evidence. It requires an explicit acknowledgement
that observation-level color/membership disclosure is authorized under the source
terms. It never follows from Select all supplements, an inference plan or a
scientific result. It authorizes only that selected report presentation, not raw
X/Y redistribution, scientific independence, publication of restricted identifiers
or a general release. Continuous colors use the selected unit/range and explicit
missing display; zero is valid. Without this declaration exported PCA is uncolored.
