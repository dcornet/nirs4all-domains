# Multi-scale diagnostics and synthetic spectra — concept note

Revision 2026-10-28. Part A audits an existing product/provider boundary; Part B
is a research hypothesis. Neither adds a clustering engine, generator, GPU setup
or training experiment. Existing diagnostic usefulness does not depend on a
confirmed shortcut mechanism.

## A. Multi-scale structural evidence

Documented genotypes, blocks, treatments, years, plots, sessions and instruments
can be hierarchical, crossed or partially nested. An X hierarchy may agree with
them, disagree or have unknown correspondence. Do not force a crossed design into
a tree, or call every persistent X subtree a biological hierarchy.

### Provider and binding audit

The pinned public Methods header at commit
`131a15a6bbf73a8ab941c7b3fb81b21f6b71b059` was read again. Its SHA-256 matches
[the original source audit](audit/upstreams.json). This is an audit of the
qualified baseline, not a claim about the latest upstream release. Installed
Methods reports 1.3.6. The public [HDBSCAN declaration](https://github.com/GBeurier/nirs4all-methods/blob/131a15a6bbf73a8ab941c7b3fb81b21f6b71b059/cpp/include/n4m/metrics.h)
and the existing Domains [adapter](../crates/nirs4all-domains/src/methods.rs)
are separate source/binding evidence. Existing native tests and prior executed
CI provide executable evidence; availability alone is not scientific qualification.
No upstream code or test suite is modified or rerun.

| Information | Public provider / present transport | Scientific scope and missing qualification |
|---|---|---|
| Selected labels and noise | `n4m_cluster_hdbscan`; adapter labels and noise label -1 | An X partition, not specimen/context identity |
| Membership strength and outlier diagnostics | Native membership, GLOSH and explicit undefined/nonfinite reasons | Relative strength is not a probability; undefined density diagnostics remain null/reasoned |
| Selected-cluster persistence | Native `cluster_persistence`; retained by the Rust adapter | Within-fit density-tree persistence, not resampling stability or biological significance |
| Condensed hierarchy | Native parent, size, selected label, lambda birth/death and node stability; `HdbscanNode` transport | Density-tree structure; node mass/stability is not an inferential p-value or independent-unit count |
| Membership support | Native tree/cluster observation sizes; existing identity/component guards | Observation count is not effective biological/sample support when dependencies are unknown |
| Resampling stability | Existing component-aware structure/unsupervised protocols, native ARI and co-membership summaries | Conditional on frozen draws and eligible inclusions; separate from persistence and parameter agreement |
| Representation sensitivity | Existing raw/SNV, partition ARI and neighborhood comparison | A change in geometry does not identify a nuisance mechanism |
| Continuous geometry/noise | Existing PCA, applicable dimension and neighborhood/density evidence, explicit noise/trivial partitions | Do not force clusters or infer low risk from their absence |
| Separation and within-cluster heterogeneity | Some geometry/neighborhood summaries exist | No single qualified generic multi-scale separation/heterogeneity family is claimed |
| Effective independent-unit support | Declared/verified identity and group information can be reported | No general effective independent-size estimator is established; retain unavailable state where unknown |

The full `structure` report can retain detailed HDBSCAN output; the broad
`x-profile`/compact bank summaries deliberately expose selected fields and do not
necessarily carry the full tree. A field in the adapter is not proof that every
campaign export contains it. Do not reconstruct absent hierarchy from cluster
counts or infer unseen-group assignment from the batch tree. The existing
[held-out HDBSCAN proposal](UPSTREAM_DEPENDENCIES.md) remains separate.

### Planned generic descriptor family

Future D1 work may qualify hierarchical grouping, separation, persistence,
resampling stability, minimum membership, independent-unit support where known,
within-cluster heterogeneity, representation sensitivity, continuity and
noise/unassigned observations. First map actual report/provider fields and
define their denominators, uncertainty and failure modes. Reuse public Methods/
Preflight APIs and existing protocols. No recursive clustering framework,
arbitrary risk scalar or forced tree of experimental factors is proposed here.

LOCO-X remains an explicitly geometric, potentially transductive stress test.
Its use as a proxy for a deployment shift needs independent evidence of the
correspondence; it is not physical/experimental LOGO by name alone.

## B. Synthetic spectral augmentation — research hypothesis

**Can synthetic NIRS spectra reduce reliance on experimental group structure by
increasing coverage of plausible spectral variation between or within source
populations, while preserving the real relationship between spectra and traits?**

Filling spectral gaps is not assumed to improve prediction. Three distinct
mechanisms belong in the separate research program:

| Candidate | Intended mechanism | Assumptions to test |
|---|---|---|
| Physically motivated augmentation | Bounded multiplicative scatter, additive baseline or supported instrument perturbations | The change is physically credible and preserves target-relevant information under the stated acquisition conditions |
| Local/conditional generation | Plausible spectra near real observations or across documented conditions, potentially using a VAE or another generator | Chemical/spectral fidelity, trustworthy target consistency, genuine diversity and no memorization |
| Invariant/self-supervised learning | Multi-view, repeat-acquisition or source-domain information reduces unwanted representation variation | A factor may carry legitimate chemistry; invariance costs must be measured rather than assumed harmless |

Primary risks are off-manifold spectra, unverifiable generated labels, removal
of real chemical variation, reproduction of source-specific shortcuts, generator
memorization, train/test leakage, transductive held-out X use, apparent cluster
suppression without predictive gain, and better KFold scores with worse
unseen-group performance. No mechanism is established as a remedy here.

Required future comparators are no augmentation, simple physically motivated
augmentation, a bounded local interpolation/resampling baseline, a justified
generative candidate and, where justified, a representation-learning candidate.
Use the same original-data training, dependency-group and evaluation boundaries
for every method. Freeze transformations, generator training, synthetic-label
rules, scales/seeds, selection, model settings and complexity/cost controls before
evaluating responses. A local interpolation baseline cannot assume target
linearity or label validity merely because spectra are close.

Fit generators/representations only on allowed training populations for an
ordinary inductive claim. Held-out X may enter only a separately declared test-time
adaptation design with its own evaluation interpretation; held-out Y never enters
training or selection. Synthetic evaluation observations must not replace real
external specimens or groups. Jointly held-out original units remain outside
every generation, preprocessing, routing and tuning operation.

The principal endpoint is prediction on genuinely observed held-out specimens or
groups matching intended deployment, with absolute utility and deterioration both
retained. Secondary endpoints include chemical/spectral fidelity, target
consistency, invariance, diversity, memorization diagnostics and model complexity.
Favorable geometry or reduced clustering alone is not evidence of reduced
shortcut dependence. Preserve negative results and useful-chemistry losses.

The [R4 program](STRUCTURAL_GENERALIZATION_RESEARCH_PROGRAM.md) may compare these
ideas using public model APIs. This assignment implements no VAE, augmentation,
SSL learner, TabPFN/TabICL expert or generator and performs no experimental fitting.
Promotion to Domains would require the [generic-use qualification rule](PRODUCT_RESEARCH_BOUNDARY.md).
