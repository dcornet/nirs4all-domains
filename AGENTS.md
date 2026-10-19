# Working conventions

- Read README, docs/ARCHITECTURE.md, METHOD_REUSE_MATRIX.md and SCIENTIFIC_PROTOCOLS.md
  before changing a protocol. The Word plan was read during the initial audit;
  its local attachment is ignored and is not a runtime dependency.
- Reuse public Methods/Preflight APIs. Never copy numerical algorithms into Rust
  or Python. Generic missing kernels belong in Methods; intrinsic qualification
  belongs in Preflight. Document proposed upstream work without changing upstream.
- Keep the task explicit: dataset/content version/source/target/split/policy.
  Prefer declared identities. The owner's content-bound same-export X/Y/M
  order contract may support exploratory positional alignment when counts,
  order, exclusions and absence of independent sorting/filtering are verified.
  It does not establish physical/reference independence. Preserve original axes.
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
- The owner authorizes budget increases up to 5,000,000,000 bytes per alpha
  without another budget approval request. Freeze a concrete staged plan and
  report increases, actual usage, limits and scientific scope. Preserve volume
  reserves, history and actual access restrictions; ask before exceeding this cap.
- Inspect private-root configuration with scripts/inspect_private_roots.py;
  never dump its values to tools. Project JSON result fields before inspection.
- The user authorized GitHub repository creation and the first commit/push on
  2026-10-16. Further changes to upstream repositories still require explicit
  authorization. Verify git identity; do not invent an author or change global config.
