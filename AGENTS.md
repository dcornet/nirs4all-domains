# Working conventions

- Read README, docs/ARCHITECTURE.md, METHOD_REUSE_MATRIX.md and SCIENTIFIC_PROTOCOLS.md
  before changing a protocol. The Word plan was read during the initial audit;
  its local attachment is ignored and is not a runtime dependency.
- Reuse public Methods/Preflight APIs. Never copy numerical algorithms into Rust
  or Python. Generic missing kernels belong in Methods; intrinsic qualification
  belongs in Preflight. Document proposed upstream work without changing upstream.
- Keep the task explicit: dataset/content version/source/target/split/policy.
  Join sources and tables by declared identities, never row position. Preserve axes.
- No fit on retained test. Never read Y_test for pre-training selection. Preserve
  references/groups and check indivisible identities before any aggregation/CV.
- Preflight alpha availability is not scientific qualification. Capabilities need
  separate source, ABI, binding, publication and executable evidence.
- Maintain JSON Schema and result status/reason/value invariants. No NaN/Inf or
  arbitrary score. Findings state observation, confidence, consequence and action.
- Use the two existing crates until a concrete consumer justifies another crate.
  Python is transport/batch only; test-data generation is not a numeric backend.
- Protocol changes require expected scientific behavior stated before tests,
  adversarial leakage fixtures, version changes and explicit tolerance choices.
- Run fmt, clippy with warnings denied, workspace tests, native ignored gates,
  bridge integration and JSON report checks. CI configuration is not execution proof.
- No absolute development paths in distributable manifests. Keep Cargo.lock.
  Large data use Datasets' cache; results/, .audit/, .tools/, .venv/ stay ignored.
- Use ordinary single-agent work unless the user requests delegation.
- Inspect private-root configuration with scripts/inspect_private_roots.py;
  never dump its values to tools. Project JSON result fields before inspection.
- The user authorized GitHub repository creation and the first commit/push on
  2026-10-16. Further changes to upstream repositories still require explicit
  authorization. Verify git identity; do not invent an author or change global config.
