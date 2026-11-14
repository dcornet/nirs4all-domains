# PR #7 targeted review closure

Reviewed head: `4656e98d533aecd96008f4101ebd48340a245224`.
[Review observation](https://github.com/dcornet/nirs4all-domains/pull/7#discussion_r4572359617)
requests complete CommonMark structural escaping while preserving evidence.
No merge, release, tag or version change is part of this closure.

## Demonstrated defect and correction

The reference CommonMark parser reproduced six failures among fourteen new
renderer checks before the patch: tilde fences and retained CR/indentation
could create extra blocks or hide later sections. Greater-than cases are also
covered; the old HTML entity encoding already prevented some quote examples.
This is report-integrity behavior, not an observed spectrum upload.

Only untrusted Markdown prose is normalized to a single unindented line and
all escapable ASCII punctuation is backslash-escaped, including tilde,
greater-than, backslash and reference/HTML delimiters. CR, LF, CRLF and tabs
cannot start new blocks. The original JSON string is never passed through
this transformation. Its tilde fence is independently sized to exceed every
run in the payload, using an iterator rather than a spread-size argument list.

Tests parse the result with pinned **commonmark 0.31.2**, BSD-2-Clause, a small
test-only reference-parser dependency (plus its types). No runtime import or
new production parser is introduced. The unsanitized renderer is used so a
sanitizer cannot hide a serialization defect. Thirteen adversarial prose inputs
plus an all-ASCII-punctuation case assert visible following headings, one JSON
code block, no injected blockquote/link/image/HTML, exact JSON block contents,
and unchanged original report/numerical values. Existing URI byte assertions
now expect stronger literal escaping; no scientific fixture was replaced.

## Evidence and acceptance gates

Local corrected typecheck and **33 frontend/export tests pass**, including the
fourteen new renderer checks. A separate exact comparison of reviewed versus
corrected serializers on seven hostile public-report inputs confirms **14
byte-identical HTML/JSON comparisons**. Three analytical-checker adversaries and
four exact-source-byte native/WASM saved fixtures are reused unchanged.

The corrected commit must pass all current
[PR checks](https://github.com/dcornet/nirs4all-domains/pull/7/checks): scientific,
read-only reporting and actual WASM/browser matrices on Windows/Ubuntu. Their
exact commit/run IDs and final outcomes are recorded in the response to the
linked review thread, rather than a self-referential commit ID in this file.
A pending/failed gate means the PR is not technically ready. Preserve the
decreasing/gapped-neighbor refusals, analytical absolute 1e-10 versus platform
abs/rel 1e-8, and unchanged four-fixture scopes/metrics/evidence hashes; none of
those numerical/test contracts is weakened by this Markdown patch.

The public site remains separately bound to main d1b14cc until owner integration;
a branch CI preview is not a deployment of this PR. Recheck actual public
HTTP/assets/WASM/import/export/refusal behavior without real-source fitting.
Research remains read-only; its original files, package, journal and reservations
are preserved. Test-only dependency locking changes no scientific package version.

The new [train-fitted review](TRAIN_FITTED_PROTOCOL_REVIEW.md),
[human evaluation plan](HUMAN_UTILITY_EVALUATION_PLAN.md),
[single-experiment decision](PHASE2_EXPERIMENT_DECISION.md) and
[owner decisions](OWNER_DECISIONS.md) are approval candidates, not executed work.
No independent human judgment or new real-data experiment is claimed.

CommonMark basis: [escapes and blocks, specification 0.31.2](https://spec.commonmark.org/0.31.2/)
and the [reference JavaScript parser](https://github.com/commonmark/commonmark.js).
