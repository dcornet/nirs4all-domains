"""Scientific interpretation tables from completed shared numeric evidence."""
from collections import Counter
from pathlib import Path
import json
from alpha18_common import Context,read
from nirs4all_domains.predictive import native_summary
from nirs4all_domains.storage import atomic_json


def cell(v):return f'{v:.5g}' if isinstance(v,(int,float)) else str(v)


def main():
    c=Context();root=Path('docs/campaign');s=read(root/'status.json');con=read(root/'confrontation.json');ex=read(root/'experiment-matrix.json');local=c.load('local-confrontation.json')
    joined=con['joined_source_views'];families={}
    for family in ['pls','ridge']:
        vals=[r['skill_across_targets'][family]['value']['median'] for r in joined if r['skill_across_targets'][family]['status']=='computed']
        families[family]={'n_source_views':len(vals),'summary':native_summary(vals) if vals else None,'n_worse_than_null':sum(v<0 for v in vals)}
    contrary=[]
    negative=[]
    for r in joined:
        pc=r['descriptors']['pc1_fraction']
        for family in ['pls','ridge']:
            skill=r['skill_across_targets'][family]
            if skill['status']=='computed' and skill['value']['median']<0:
                row={'view_id':r['view_id'],'family':family,'raw_PC1':pc['value'] if pc['status']=='computed' else None,'median_CV_skill':skill['value']['median']}
                negative.append(row)
                if pc['status']=='computed' and pc['value']>=.95:contrary.append(row)
    delta=[]
    for r in con['stress_tasks']:
        if r['result']['status']!='computed':continue
        v=r['result']['value']
        for family,dd in v['deterioration'].items():
            if dd['status']=='computed':delta.append({'view_id':r['view_id'],'target':r['target'],'factor':v['factor'],'family':family,'n_evaluation':v['n_evaluation'],'n_train_size_control':v['regimes']['size_control']['n_train'],'D_RMSE':dd['value']['D_RMSE'],'D_skill':dd['value']['D_skill']})
    findings=[{'observation':f"Complete paired X profiles increased from 56 to {s['computed_source_views']}, while every one of 171 views is accounted for.",
               'confidence':'High for execution and frozen source identities; descriptive geometry is observation-conditional.',
               'consequence':'Broader structural diversity is measurable without assuming biological independence.',
               'action':'Use the full descriptor matrix; retain cost, nonfinite-data and low-n limitations explicitly.'},
              {'observation':f"{s['reference_task_counts'].get('computed',0)} source/target tasks have complete fixed-model reference results; negative scores and failed folds are retained.",
               'confidence':'Native executable outcomes under frozen scopes; target meaning, missingness and physical dependencies remain source-specific.',
               'consequence':'We can compare model response with pre-outcome descriptors, rather than infer predictive usefulness from X geometry alone.',
               'action':'Separate ordinary CV skill from matched stress deterioration; compare unit-free outcomes across targets.'},
              {'observation':f"The post-hoc raw-PC1 >= .95 / negative-median-skill screen finds {len(contrary)} cases; {len(negative)} source/family records have negative median skill overall.",
               'confidence':'Descriptive post-hoc counterexample screen, not a preregistered H1-H5 decision rule.',
               'consequence':'An empty threshold screen is a null result for that screen, not evidence that high concentration certifies generalization or low shortcut risk.',
               'action':'Preserve the null screen, all negative-skill cases and the directly observed stress/pipeline contrasts.'},
              {'observation':f"{len(delta)} public source/family matched stress pairs are available; no independently confirmed study-level descriptor/fragility relationship exists.",
               'confidence':'Exploratory paired evaluation; training composition and target support still limit causal interpretation.',
               'consequence':'Neither a convenience bank nor many targets/folds establishes independent scientific replication.',
               'action':'Use the paired effects as exploratory evidence and register later independent study validation separately.'}]
    findings.extend([
        {'observation':'None of the six available descriptor screens exceeds absolute Pearson correlation .50 with median primary-task CV skill for either fixed model.',
         'confidence':'Native fixed-threshold descriptive tests on 15 to 35 permitted source views; no signed coefficient, adjustment or independent study inference.',
         'consequence':'These screens provide no evidence of a strong linear source-view association with ordinary CV skill. They do not test every form of predictive usefulness or registered deterioration endpoint.',
         'action':'Retain the null screens and test prespecified matched fragility endpoints with independent study support.'},
        {'observation':'SNV increases matched stress deterioration for both models on aquatic-leaf LMA, reduces it on tablets, and has opposite signs for PLS and Ridge on leaf nitrogen.',
         'confidence':'Executed raw/SNV contrasts with identical evaluation IDs, exact training-size controls and a common null denominator; small exploratory context populations.',
         'consequence':'Preprocessing sensitivity depends on both source context and estimator; no universal SNV correction or scalar shortcut ranking follows.',
         'action':'Preserve estimator-by-pipeline interactions and extend matched, prospectively specified context comparisons.'},
        {'observation':'Whole-plot CV worsens both fixed models on pressed-leaf nitrogen, but improves PLS and worsens Ridge on the Plant_Age task; NASA-leaf EWT changes are close to zero.',
         'confidence':'Five metadata-selected declared-plot tasks, common evaluation observations; training sizes and compositions differ and plots are not independently verified biological units.',
         'consequence':'Grouping effects are heterogeneous; a stronger declared grouping does not guarantee a uniform direction or magnitude of score change.',
         'action':'Retain small, negative and estimator-opposed effects; use matched-size designs before interpreting grouping effects causally.'}])
    evidence={'schema_version':1,'findings':findings,'public_view_skill_summaries':families,'high_PC1_negative_skill_cases':contrary,'negative_skill_source_families':negative,'matched_stress_pairs':delta,'independent_confirmation':False}
    atomic_json(root/'scientific-findings.json',evidence)
    lines=['# Full-bank structural characterization and exploratory model confrontation','',
        'The campaign now links frozen X-only descriptors to actual fixed-model outcomes across a diverse existing bank. These are exploratory comparisons; no universal shortcut score or independently validated generalization claim is produced.','',
        '## Scientific coverage','',
        f"All **164 catalog entries / 171 source views** and **2,054 declared source/target tasks** are inventoried. Complete raw/SNV profiles cover **{s['computed_source_views']}/171** views ({s['computed_source_views']}/163 locally analysis-authorized views), up from 56. The 56 exact prior profiles were reused, not refitted. New X attempts: 95; 81 succeeded, 14 failed. Eight failures have nonfinite X; six are two-observation views rejected by the current CLI entry contract. The latter is a local adapter limitation, not proof of invalid data. Twelve larger views are resource-deferred, and eight views remain outside the preserved analysis authorization. No source observation or band was removed to meet a numeric threshold.", '',
        f"Reference task accounting: `{json.dumps(s['reference_task_counts'],sort_keys=True)}`. Native reference fitting: **{s['model_fit_successes']} finite fit/predict completions / {s['model_fit_attempts']} pipeline model attempts**, including diagnostic executions. Mathematical pre-fit guards can reject an attempt before a native fit call. The primary quantitative subset has **{s['completed_primary_quantitative_tasks']} complete tasks / {s['primary_quantitative_fit_successes']} successful fits**. All tasks retain actual eligibility, target population, missingness, failure and publication states in the [experiment matrix](campaign/experiment-matrix.md). Five numeric classification labels were excluded before decoding outcomes. A subsequent full target-name audit corrected further identifiers/counters and separated context, model-derived and unresolved QC endpoints. Already executed diagnostics remain visible and count as execution, but do not enter the primary quantitative synthesis. Selection uses metadata meaning, not favorable scores. Source-declared predicted traits and spectral indices also remain visible outside the primary screens.", '',
        f"Full local confrontation joins **{s['all_authorized_joined_source_views']} source views**; **{s['public_joined_source_views']}** have permitted public numeric outcomes and descriptors. All authorized private-tier sources enter the same scientific workflow. Unknown publication terms restrict only outgoing numbers, not local analysis. Local full matrices, comparison screens and outcomes remain in the existing protected evidence store. Counts of sources, targets and folds are not counts of independent studies.", '',
        '## What the data show','',
        '| Observation | Confidence | Consequence | Action |','|---|---|---|---|']
    for finding in findings:lines.append('| '+' | '.join(finding[k] for k in ['observation','confidence','consequence','action'])+' |')
    lines+=['','Per-view medians use the SAME complete primary quantitative target tasks for both families. Partial/failed cases remain in the full matrix, with their successful family results. Target mixtures differ across views and original assay origins are not fully verified. Values below zero are worse than the fold-local training mean. These are source-view distributions, without study-level confidence intervals. Raw unscaled X and fixed Ridge alpha=1 imply different effective regularization across source intensity units; these are results for the frozen pipelines, not optimized estimator potential.','',
        '| Fixed model | Source views | Median skill | IQR | Views with negative median skill |','|---|---:|---:|---|---:|']
    for family,record in families.items():
        q=record['summary']
        if q:lines.append(f"| {family.upper()} | {record['n_source_views']} | {q['median']:.5g} | {q['q25']:.5g} to {q['q75']:.5g} | {record['n_worse_than_null']} |")
    lines+=['','### Structural variation across the permitted bank','',
        'These native summaries describe source views, without assuming independent studies. n is the number of available metric values, which can be lower than the source count. Exact effective dimension is reported only where the required full moments exist; truncated PCA is not substituted. HDBSCAN uses the frozen min-cluster-size 12 setting. Similar marginal cluster counts do not imply similar memberships.','',
        '| Descriptor | Representation | n | Median | IQR | Range |','|---|---|---:|---:|---|---|']
    distributions=read(root/'descriptor-distributions.json')['distributions']
    for r in distributions:
        if r['metric'] not in ['pc1_fraction','effective_dimension','clusters_12','noise_12','neighbor_cv','raw_snv_ari','raw_snv_overlap']:continue
        if r['metric'].startswith('raw_snv_') and r['representation']=='snv':continue
        if r['summary']['status']!='computed':continue
        q=r['summary']['value'];lines.append(f"| {r['metric']} | {r['representation']} | {int(q['count'])} | {q['median']:.5g} | {q['q25']:.5g} to {q['q75']:.5g} | {q['min']:.5g} to {q['max']:.5g} |")
    lines+=['','Raw and SNV both have median two detected clusters, while median raw/SNV ARI is only .226 and neighborhood overlap .3125. Thus apparently stable cluster counts can conceal substantial representation changes. These are structural observations, without evidence that the changed memberships are shortcut mechanisms.','',
        '![Paired raw/SNV geometry](campaign/representation-geometry.png)','',
        '![Frozen descriptor and fixed-model outcomes](campaign/descriptor-performance.png)','',
        '### Fixed native association screens','',
        'The existing native filter tests strict absolute Pearson thresholds .50/.80/.95. It exposes neither a signed coefficient nor a p-value. These unadjusted source-view screens do not control n/p, target mixtures, study overlap or selection effects.','',
        'Descriptors characterize the complete source X; supervised outcomes use available development targets after sealed exclusions. Missingness can select a different population. Per-task denominators are preserved, and this mismatch limits interpretation of whole-source descriptor/outcome screens.','',
        '| Descriptor | Model | Paired views | abs(r) > .50 | > .80 | > .95 |','|---|---|---:|---|---|---|']
    for r in con['native_absolute_correlation_screens']:
        v=r['result']
        if v['status']=='computed':
            q=v['value'];lines.append(f"| {r['descriptor']} | {r['family']} | {q['n_source_views']} | "+' | '.join(str(a['exceeds']).lower() for a in q['screens'])+' |')
        else:lines.append(f"| {r['descriptor']} | {r['family']} | unavailable | {v['reason']} | - | - |")
    lines+=['','### Contrary cases','',
        'The following post-hoc descriptive screen lists every source/family with raw PC1 >= .95 and negative median target CV skill. It is not a new registered risk threshold, and ordinary skill does not replace a deterioration endpoint.','',
        '| View | Fixed model | Raw PC1 | Median target CV skill |','|---|---|---:|---:|']
    for r in contrary:lines.append(f"| {r['view_id']} | {r['family']} | {r['raw_PC1']:.5g} | {r['median_CV_skill']:.5g} |")
    if not contrary:lines.append('| No matching case in the permitted primary subset | - | - | - |')
    lines+=['','All negative-median-skill source/family records are retained below, without adjusting the .95 screen to obtain a preferred result.','',
        '| View | Fixed model | Raw PC1 | Median target CV skill |','|---|---|---:|---:|']
    for r in negative:lines.append(f"| {r['view_id']} | {r['family']} | {cell(r['raw_PC1'])} | {r['median_CV_skill']:.5g} |")
    lines+=['','## Matched structural stress','',
        'Five source/context populations were selected before primary Y decoding, with historical sealed memberships protected. Final genuine target priority was corrected during the metadata audit after primary fits began and before ANY stress outcome; no predictive scores were used for that correction. These are exploratory comparisons, not untouched target-level confirmation. They preserve known groups, use identical evaluation observations and exact whole-component training-size controls. Full reference, size-control reference and context-excluded training remain separate. A positive D_skill means exclusion worsened error under the SAME size-control null denominator; a negative value is contrary to a simple expectation of deterioration. These effects still combine context, chemistry, training composition and target-range changes.','',
        '| View / target | Context | Model | Evaluation n | Matched training n | D_RMSE (target units) | D_skill |','|---|---|---|---:|---:|---:|---:|']
    for r in delta:lines.append(f"| {r['view_id']} / {r['target']} | {r['factor']} | {r['family']} | {r['n_evaluation']} | {r['n_train_size_control']} | {r['D_RMSE']:.5g} | {cell(r['D_skill']['value']) if r['D_skill']['status']=='computed' else r['D_skill']['reason']} |")
    lines+=['','### Raw/SNV pipeline interaction','',
        'All five previously selected stress tasks also receive the frozen SNV pipeline, without choosing cases using model scores. Exact private fingerprints verify identical training and evaluation memberships; both representations use the same null denominator. I_skill is D_skill_SNV minus D_skill_raw. A positive value means SNV increases stress deterioration relative to its own matched-size reference; it does not simply mean worse SNV accuracy.','',
        '| View / target | Model | I_RMSE | I_skill |','|---|---|---:|---:|']
    for r in con['representation_interactions']:
        if r['result']['status']!='computed':continue
        for family,pair in r['result']['value']['model_interactions'].items():
            if pair['status']=='computed':
                v=pair['value'];lines.append(f"| {r['view_id']} / {r['target']} | {family} | {v['I_RMSE']:.5g} | {cell(v['I_skill']['value']) if v['I_skill']['status']=='computed' else v['I_skill']['reason']} |")
    lines+=['','The [prospective extension](ALPHA18_SNV_STRESS_PLAN.md) adds at most 30 model fits and 15 diagnostic PCAs, with 5 MiB of reservations inside unchanged ceilings. Source-permitted interaction screens are retained in the machine-readable confrontation; four or fewer public source cases cannot validate an independent-study relationship.','']
    lines+=['','Every attempted stress task, including missing pairs and unfavorable values, is in [confrontation.json](campaign/confrontation.json). Train-only PC1 range diagnostics and target extrapolation counts provide limited support evidence; they do not represent full geometric residual coverage or causal shortcut attribution.','',
        '## Declared-plot sensitivity','',
        'Five additional source/target cases were selected by repeated plot metadata and a fixed semantic target priority, without using predictive scores. Experimental plot links are merged with existing components. The primary reference estimates within-context performance; whole-plot CV asks a stronger context question. Both OOF vectors are compared on the same available evaluation observations, with the grouped null as common denominator. Different training populations, sizes and one fixed allocation confound a pure causal interpretation. Plot aliases are declarations, not verified independent biological units.','',
        '| View / target | Model | Common evaluation n | D_RMSE | D_skill |','|---|---|---:|---:|---:|']
    for r in con['declared_plot_sensitivity']:
        if r['result']['status']!='computed':continue
        for family,pair in r['result']['value']['paired_comparison'].items():
            if pair['status']=='computed':
                v=pair['value'];lines.append(f"| {r['view_id']} / {r['target']} | {family} | {v['n_common_evaluation']} | {v['D_RMSE']:.5g} | {cell(v['D_skill']['value']) if v['D_skill']['status']=='computed' else v['D_skill']['reason']} |")
    lines+=['', '[Declared-plot protocol and bounds](ALPHA18_GROUP_SENSITIVITY_PLAN.md) preserve the original primary outcomes and explicit stronger-design limitations.','',
        '## H1-H5: what can and cannot be tested','',
        '| Frozen hypothesis | Current evidence | Remaining scientific limit |','|---|---|---|',
        '| H1: reproducible separation / fragility | Descriptors and paired context outcomes can be confronted exploratorily | Calibrated stability is not available for every paired task; no independent study validation |',
        '| H2: neighborhood overlap / interpolation | Fixed proximity screens and paired stress effects are available | Ordinary CV skill is not genuine-transfer deterioration; whole-source proximity is not train-to-evaluation coverage |',
        '| H3: representation instability / pipeline interaction | Frozen raw/SNV-by-model-by-context interactions on matched populations | Five exploratory tasks and limited publication subset; no independent study validation or universal risk threshold |',
        '| H4: continuous support without discrete groups | Concentration screens and train-only PC1 extrapolation diagnostics | One-PC ranges are limited; context comparisons do not isolate causal continuous-support shifts |',
        '| H5: proximity / unresolved independence | Known components and retained memberships are preserved | No new independently verified physical/assay closure contrast, so the registered response is unavailable |', '',
        'No H1-H5 definition or decision rule was changed after outcomes. The operational fixed-model grids and convenience contexts do not constitute the full later registered anchor/independent-confirmation design. Historical discovery populations remain historical; every new comparison is exploratory. Strong geometry alone is not a low-risk certificate; poor transfer alone does not identify a shortcut mechanism.','',
        '## Local blockers and the next scientific decision','',
        'Nonfinite X prevents the exact raw PLS/Ridge/PCA path on affected views; target descriptions remain available. No unqualified imputation or numerical Python fallback was substituted. Six two-row views need a bounded low-n geometry adapter that separates PCA from clustering requirements. Larger matrices need an explicitly costed extension. Three supervised views lack complete binding to already sealed historical populations; they do not block other views. Unknown physical and assay dependencies constrain independence claims, rather than ordinary admitted exploratory analysis.','',
        'The next computational decision is a prespecified missing-data/low-n technical qualification and broader supported stress contrasts, followed by supervised representation comparisons. Imported original-study evidence can improve interpretation through the [additive study contract](STUDY_EVIDENCE_IMPORT.md), without refitting frozen X descriptors. Do not restart unchanged source-owner investigations. Reserve independent studies and define confirmation designs before viewing their future outcomes.','',
        '## Resources and reproducibility','',
        'The owner authorized increases up to 5 Go per alpha without another approval question. This alpha uses the conservative SI sum: **+4,000,000,000 bytes combined-storage ceiling and +1,000,000,000 bytes cumulative-reservation ceiling = 5,000,000,000 bytes**. Current ceilings are 20,289,597,121 and 1,805,306,368 bytes. This is a ceiling/reservation change, not 5 GB of newly written scientific files. Existing whole export files were counted in participation; no raw acquisition, deletion or migration occurred. See the [concrete resource plan](ALPHA18_RESOURCE_PLAN.md), [execution qualifications](ALPHA18_EXECUTION_NOTES.md) and final [validation/resource measurement](audit/alpha18-validation.json).','',
        'The [existing execution receipts](campaign/scientific-execution-resources.json) record 1,343.314 seconds of new X worker time and 2,490.310 seconds of reference worker time, including worker overhead. The largest conservative sum of separate X Python/native high-water marks is 781,520,896 bytes; the reference process peak is 542,420,992 bytes. Raw/SNV stress adds 48 successful model fit/predict completions and declared-plot CV adds 30. The initial raw-stress watchdog race is explicitly qualified in the execution notes; final OS high-water marks were below 2 GiB, but that run is not presented as clean continuous enforcement. Null-only continuation completes 382 target tasks with zero model fits. These timings do not measure all campaign, null-continuation or engineering time.','',
        'Methods1.3.6, DAG-ML0.3.41 and the qualified native X executable own all numerical operations. Python bridge is 0.1.0a18; unchanged Rust crates remain 0.1.0-alpha.16. Native model parameters are fixed; no favorable-score task selection, broad HPO, TabPFN or B60 prerequisite. Historical artifacts, source restrictions and journal reservations remain intact. Actual local/native/package gates and final-source Windows/Ubuntu CI are recorded separately from scientific fitting.','',
        '[Protocol](ALPHA18_SCIENTIFIC_PROTOCOL.md) · [Stress estimands](ALPHA18_STRESS_ESTIMANDS.md) · [Source attribution](campaign/source-attribution.md) · [Machine-readable findings](campaign/scientific-findings.json) · [Structural matrix](campaign/source-matrix.md)','']
    Path('docs/ALPHA18_SCIENTIFIC_RESULTS.md').write_text('\n'.join(lines),encoding='utf-8')
    # Local report includes every authorized numeric comparison, never exported.
    private=['# Full authorized-bank exploratory confrontation','', 'All authorized source views; ordinary metrics use real catalog names. Raw X/Y, source identities and OOF remain protected. No independent-study confirmation.','',
        '| View | Eligible target tasks | PLS median skill | Ridge median skill |','|---|---:|---:|---:|']
    for r in local['joined_source_views']:
        vals=[cell(r['skill_across_targets'][f]['value']['median']) if r['skill_across_targets'][f]['status']=='computed' else r['skill_across_targets'][f]['reason'] for f in ['pls','ridge']]
        private.append(f"| {r['view_id']} | {r['n_target_tasks']} | {' | '.join(vals)} |")
    (c.root/'FULL_BANK_SCIENTIFIC_REPORT.md').write_text('\n'.join(private)+'\n',encoding='utf-8')
    c.save('scientific-report-measurement.json',c.guard());print('SCIENTIFIC_FINDINGS_REPORT_RENDERED')

if __name__=='__main__':main()
