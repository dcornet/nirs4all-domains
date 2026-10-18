# Alpha.13 execution and resource observations

The original identity-design calculation completed successfully. Its first
publication attempt encountered the alpha.12 export helper's intentional path
guard, which forbids writing into a different release namespace. The alpha.13
helper now has its own bounded destination guard. The completed StageStore
artifact was reused exactly; no identity simulation or native fit was repeated.

The first calibration tranche observes approximately .54 seconds per small
PCA/HDBSCAN draw, dominated by repeatedly starting the native executable and
loading its DLL. The prospective 6,480-draw calibration would therefore require
about an hour without reducing this overhead. This cost measurement, not scores
or classifications, motivates a distinct execution transport:
`domains.native_profile_stream.v0.1`. It sends bounded, sequential JSON lines to
the same native characterization function, with fresh Methods contexts for each
request. It retains the DLL in one process; no solver/parameters/statistical
threshold, source, identity, draw seed or selected subset changes.

Before adopting it, require exact old/new profile parity on the frozen controlled
mechanisms and an additional full-rank >500-row solver-route fixture, including
scores, labels, eigenvalues, statuses and provider identity. Test malformed/Y
requests, preserved full references, serial request isolation and error recovery.
Record both executable hashes and the unchanged native characterization source.
Numeric equality is checked before remaining calibration fits use the transport.

The running calibration may be stopped only at a verified durable stage boundary:
temporarily suspend its owned Python worker, verify the journal has no running
stage and that no native child exists, then end that worker. Otherwise resume
immediately and wait for another boundary. No valid PCA/HDBSCAN fit is canceled.
Completed exact artifacts are reused under explicit lineage and the qualified
transport parity; they are never relabeled as executions of the new binary.
The OS kernel lease releases on process exit; its persistent file is not deleted.

A local `qualification` Cargo profile inherits dev optimization/assertions but
omits debug symbols and incremental artifacts. It uses a separate target directory,
preserving earlier builds. Its actual bytes must satisfy the current approved
ceiling; requesting additional margin does not approve that margin implicitly.
CI continues to test the normal profile on both operating systems.

At the first storage stop, 7 controlled reference stages and 18 complete
resampling batches had been published: 4,334 unique PCA fits and 8,668 HDBSCAN
attempts, out of 6,498 / 12,996 planned. The next batch was refused before its
first fit. Exact completed artifacts and compatible prefixes remain available;
2,164 PCA fits remain. The revised design is not yet qualified for real execution.

An attempted symbol optimization of newly generated compiler-helper DLLs did not
reclaim space: their total size increased by 26,326 bytes. An objcopy invocation
also produced an unintended file named dash; its captured stdout was empty, so
the original empty-stream hashes do not establish helper instruction parity.
That claim is explicitly corrected in the private audit. The unintended new
output and the unqualified utility are preserved in ignored alpha.13 audit
storage. No historical file or cache was removed or migrated, and no space was
reclaimed. The executed scientific CLI hash and the frozen numerical source
hashes remain unchanged.

The independent preparation checks subsequently passed all 235 Python tests,
including the original 190, using the already executed qualification CLI. Worker
peak resident memory was 326,213,632 bytes; the separate native-child peak was
not measured. The suite took 132.72 seconds including its measurement wrapper.
Rustfmt and whitespace checks passed. This is an interim gate: current-version
clippy, Rust workspace/ignored gates, rustdoc, packaging and both CI jobs remain
pending. Editable installed metadata still reports alpha.12, so no alpha.13 wheel
execution is claimed.

The final generated SVG and CSV retain the native writers' exact line endings
and hashes through explicit binary Git attributes. This avoids newline rewriting
of checksummed scientific artifacts. Their numeric source JSON and human result
tables remain separately reviewable; no numerical result or published artifact
is changed to satisfy whitespace checks.
