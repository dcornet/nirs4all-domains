# Four open steps through the existing Domains evidence

Step 4 now includes [F3.5 report customization](../report/F3_5_USER_GUIDE.md).
Current-report checkboxes preserve the mandatory scientific core, survive language
changes and reset with a new dataset. Custom choices control print; resetting
them re-enables the historical F2 summary/complete reading described below.

F2 is stacked on F1 `c8e7f183886381aa9986055ebb0b190e643d4cf8` while PR #8
remains open. It changes presentation, not scientific scope. Start from the
landing import button or a labeled synthetic/live or public saved example.

1. **My data:** inspect the actual observation/variable counts, original axis,
   source, transported metadata, declared populations and provenance. Columns and
   row counts do not certify specimens, references or independent units. Missing
   metadata here can still exist in the original source.
2. **What the spectra show:** inspect the shared spectrum, score and eigenvalue
   charts, then open scientific details for F1's original neighbor, density,
   association and sensitivity evidence. The figure's evidence link opens and
   focuses its exact object. One component has no invented PC2; unavailable
   coordinates remain unavailable. Display zoom/selection never filters the fit.
3. **Why it may matter:** read the original observation, conditional relevance
   and possible verification. Details retain hypotheses, prerequisites,
   confidence, execution evidence and limits. Choose the prediction question:
   describing this dataset, new acquisitions, specimens, documented groups, a
   new context, or unknown. Optional population/unit/context text is an unverified
   declaration. Intent updates do not refit X or choose a validation split.
4. **My report:** return to the brief synthesis, original evidence or dataset,
   then choose a partial synthesis or complete scientific reading and download
   HTML, Markdown or JSON. The HTML preparation button downloads the chosen
   printable HTML; open it and use the browser print command. It does not open
   the live app's print dialog.

These are open anchor links, not a locked wizard. Detailed scientific navigation
remains available. Language, theme, display ranges and reading mode do not alter
scientific values. A new dataset resets dataset-specific display state; changing
intent/language/theme preserves it. Native disclosure controls and all help work
with keyboard Enter/Space. Exact evidence links reveal their containing details.

## Prepare an import

Simple CSV/TSV/text X has acquisitions in rows and variables in columns. Numeric
headers carry the spectral axis; nonnumeric headers remain original labels with
a logical index axis. Supported spectral routes include SPC and JCAMP-DX through
the pinned IO/Formats owners. No alternative parser is introduced.

For metadata, use an explicit IO configuration ending `.nirs4all.json`, selected
with every referenced file. The following artificial three-row example was
executed through the actual published IO WASM. Its authored row order is explicit;
it does not demonstrate physical specimen keys or biological independence.

```json
{"schema_version":1,"name":"Synthetic metadata import","sources":[
  {"id":"X","role":"features","input":"X.csv","partition":"train","params":{"delimiter":",","has_header":true}},
  {"id":"M","role":"metadata","input":"M.csv","partition":"train","params":{"delimiter":",","has_header":true}}
]}
```

`X.csv` contains `1000,1100` then rows `1,2`, `2,3`, `3,4`.
`M.csv` contains `acquisition,batch,site` then rows `a,g1,s1`, `b,g1,s1`,
`c,g1,s2`. The owner transports three metadata columns and three observations;
this configuration does not certify the acquisition column as a physical key.
Use the owner's declared identity/join contract for real multi-source identities;
Domains never guesses an identity, fuses sources, imputes or deletes rows.

An isolated ordinary JSON opens a saved **standalone Domains report**. Arbitrary
JSON matrices and the browser export envelope are not new X import formats.
This is documented routing, not a scientific-protocol change.

The complete-X browser route refuses declared test/predict partitions before
fitting. Preserve those populations and use a separately qualified train-fitted
protocol; relabeling/dropping them is not a remedy. Limits remain 32 files,
8 MiB combined, 2,000 observations, 1,000,000 X cells and 120 seconds per worker
request; individual kernels can separately be unavailable. No progress percentage
is invented. Cancel terminates the worker and rejects stale results.

## Reading and sharing

The partial reading is explicitly incomplete. It reuses F1 statuses, observations,
conditional checks and limits, without a new diagnostic, ranking or risk score.
Its HTML contains the full reading and original objects behind native disclosure;
JSON preserves the whole semantic model. Markdown retains exact original JSON in
an independently sized safe fence. Complete reading is the default, including
older envelopes without the optional `reading_mode` field. That additive field
accepts `summary` or `complete`; scientific schemas and protocol versions do not
change. `reportModel(..., declarations?, reading='complete')` remains compatible.

Partial HTML printing omits the complete-reading block and retains the partial
label. Complete printing keeps F1 figures/tables/parameters/provenance/limits,
without duplicating the entire machine payload on paper. There is no page target.
Full objects remain in both HTML files and JSON. Live/saved mode is explicit;
opening saved evidence is not browser numerical execution or authentication.

French/English help has sixteen four-part scientific definitions. Original
scientific text, codes and identifiers retain their original language; localized
pedagogy is separate. Error explanations/actions preserve the exact raw reason.

Raw X is excluded from exports. Names, observation IDs, PCA coordinates, metadata,
source references and declarations can still be sensitive. Review source rights
and the actual file before sharing. HTML remains offline, script-free and CSP
restricted. Rendering an export grants no publication permission.
