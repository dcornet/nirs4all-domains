# D4 standalone report consumer v1

The standalone consumer presents existing reports and validated D1/D2/D3
companions in new offline HTML, Markdown and JSON artifacts. It keeps source,
population, representation, metric and intended-use scopes explicit. Original
reports and annotations are read-only. No Preflight, Studio or Datasets source,
package or UI change is required or included.

The public [API/CLI](STANDALONE_REPORT_API.md) supports one report or a manifest
of saved cases. The [worked public example](examples/standalone/README.md) reuses
the existing tablet X-only and predictive reports as separate scopes. Native
Preflight scalar metrics/findings remain native; absent companions/identities
remain unavailable. A common label is not a source/population crosswalk.

Validation executes the original owner companion validators before every public
render/export. HTML uses escaped text, offline navigation/disclosures and a CSP
with no executable script or network resources. Markdown protects text and JSON
fences. JSON retains exact companions and source hashes, without copying entire
source report bodies. No global risk grade, probability or new scientific
calculation is introduced.

Local checks:65 focused standalone/D2/D3 tests pass, including11 consumer
regressions/adversaries. No numerical runtime is imported. The actual offline
browser checked15 case sections, exact embedded JSON, desktop/mobile navigation,
zero network resources and zero executable scripts. Source/companion hashes were
preserved. The private Research delivery contains the complete15-case report:
nine saved D1 cases on eight canonical IDs (seven NIR,one MIR outgroup), two
historical prediction cases, one original synthetic Preflight fixture and three
explicit synthetic counterexamples. Cases, targets and representations are not
independent studies; original-database/independent-study counts remain unknown.

Rust/native fitting suites are unchanged and were not relaunched for this
presentation-only increment. Historical Research pin failures and the optional
FastAOM environment failures remain documented in their original receipts.
Private Research platform receipts identify completed Windows/Ubuntu checks when
available; CI configuration alone is not execution evidence.

The owner commit stays local for review, with its exact patch in private Research.
Initial Preflight UI work was superseded by the owner's standalone instruction;
no such consumer patch is delivered. Next work is user feedback and narrowly
qualified saved-report adapters, without automatic scientific experiments.
