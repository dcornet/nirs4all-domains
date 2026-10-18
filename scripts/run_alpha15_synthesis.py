"""Confidential cross-source synthesis of actual existing execution receipts."""
from collections import Counter
import argparse
import csv
from pathlib import Path

from alpha15_common import Context, read
from nirs4all_domains.cohort import reconcile
from nirs4all_domains.dependence import state
from nirs4all_domains.storage import atomic_json, digest, fingerprint
from nirs4all_domains.synthesis import compare, describe


def collect(context):
    entries = [{'catalog_id': e['dataset_id'], 'content_version': e['content_version'],
        'local_analysis_allowed': e['access_analysis_eligible'], 'permissions': e['permissions'],
        'screening_receipt': e['receipt_id']} for e in context.audit['entries']]
    views, executions, profiles, provenance = {}, {}, {}, []
    for entry in context.audit['entries']:
        for source in entry['sources']:
            key = entry['dataset_id']+'/'+source['source_id']
            dims = source['dimensions']; exists = source['matrix_availability']['exists']
            views[key] = {'view_id': key, 'catalog_id': entry['dataset_id'], 'source_id': source['source_id'],
                'content_sha256': None, 'complete_X_available': exists, 'family': entry['family'],
                'modality': dims['reviewed_modality'], 'n_observations': dims['n_observations'], 'n_bands': dims['n_variables'],
                'study': {'verified': False, 'citation_lead': entry['original_study']},
                'population': {'verified': False}, 'xy_mapping_verified': False, 'target_unit_verified': False,
                'physical_reference_closure_verified': False, 'exact_folds_frozen': False,
                'retained_isolation_verified': False, 'supervised_budget_admitted': False,
                'exact_publication_approved': False}
            executions[key] = {'execution_id': 'unexecuted:'+key, 'view_id': key, 'content_sha256': None,
                'status': 'not_executed', 'reason': 'NO_VERIFIED_EXECUTION_RECEIPT', 'receipt_verified': False}
    def register(key, sha, status, reason, artifact, payload=None, origin=None):
        assert key in views, 'EXECUTED_VIEW_OUTSIDE_PINNED_CATALOG'
        authorization = next(e for e in entries if e['catalog_id'] == views[key]['catalog_id'])
        if not authorization['local_analysis_allowed']:
            provenance.append({'view_id': key, 'historical_artifact': str(artifact),
                'historical_status': status, 'current_use': 'unavailable',
                'reason': 'CURRENT_ANALYSIS_AUTHORIZATION_NOT_ADMITTED'})
            status, reason, payload = 'unavailable', 'CURRENT_ANALYSIS_AUTHORIZATION_NOT_ADMITTED', None
        # Prespecified precedence: alpha12 < alpha13 < alpha14. Same-content
        # duplicates retain provenance, never count as additional source views.
        previous = executions[key]
        if previous['status'] != 'not_executed':
            provenance.append({'view_id': key, 'superseded_execution': previous,
                'same_content': previous['content_sha256'] == sha, 'selection': 'chronological_protocol_precedence_not_outcomes'})
        views[key]['content_sha256'] = sha
        executions[key] = {'execution_id': origin+':'+key, 'view_id': key, 'content_sha256': sha,
            'status': status, 'reason': reason, 'receipt_verified': True, 'artifact_sha256': digest(artifact),
            'artifact_path': str(artifact), 'protocol_origin': origin}
        if payload is not None: profiles[key] = payload
        elif key in profiles: del profiles[key]
    matrix = read('docs/benchmarks/alpha12/structural-matrix.json')
    frozen = {e['dataset_id']: e for e in read('docs/benchmarks/alpha12/input-freeze.json')['entries']}
    for entry in matrix['entries']:
        key = entry['dataset_id']+'/'+entry['source_id']; freeze = frozen[entry['dataset_id']]
        reps = {}; paths = []
        for rep in ['raw', 'snv']:
            p = Path('docs/benchmarks/alpha12/profiles')/(entry['dataset_id']+'.'+rep+'.json')
            if p.exists():
                value = read(p)
                if value['status'] == 'computed': reps[rep] = value['value']; paths.append(p)
        status = 'computed' if len(reps) == 2 else 'partial' if reps else 'unavailable'
        register(key, freeze.get('input_csv_sha256'), status, None if status == 'computed' else 'HISTORICAL_PROFILE_INCOMPLETE',
            'docs/benchmarks/alpha12/structural-matrix.json', {'representations': reps,
                'representation_agreement': entry['representation_agreement']} if reps else None, 'alpha12')
    for entry in read('docs/benchmarks/alpha13/x-only-extension.json')['records']:
        reps = {}
        for rep, ref in entry['profiles'].items():
            assert digest(ref['path']) == ref['sha256']
            value = read(ref['path'])
            if value['status'] == 'computed': reps[rep] = value['value']
        register(entry['dataset_id']+'/'+entry['source_id'], entry['source_content_sha256'],
            'computed' if len(reps) == 2 else 'partial', None if len(reps) == 2 else 'HISTORICAL_PROFILE_INCOMPLETE',
            'docs/benchmarks/alpha13/x-only-extension.json', {'representations': reps,
                'representation_agreement': entry['representation_agreement']}, 'alpha13')
    observed = {r['source_receipt_id']: r for r in read(context.store.root/'profile-execution.json')['records']}
    for source in context.freeze['sources']:
        key = source['admission']['source_scope'].split('/')[0]+'/'+source['source_id']
        execution = observed.get(source['source_receipt_id'])
        if execution is None: continue
        if execution['status'] == 'computed':
            data = context.store.get(execution['receipt_id'])['payload']
            assert data['contract']['source'] == source
            artifact = context.store.evidence/(execution['receipt_id']+'.json')
            register(key, source['source_sha256'], 'computed', None, artifact, data, 'alpha14')
        else:
            register(key, source['source_sha256'], 'failed', execution['reason'],
                context.store.root/'profile-execution.json', origin='alpha14')
    hierarchy_path = 'docs/benchmarks/alpha12/source-hierarchy.json'
    hierarchy = read(hierarchy_path)
    relations = []
    for node in hierarchy['nodes']:
        key = node['dataset_id']+':'+node.get('source_id', 'X')
        matching = [v for v in views.values() if v['catalog_id'] == node['dataset_id']]
        population = node.get('physical_population', {})
        for view in matching:
            view['historical_identity_evidence'] = node
            if node.get('original_keys_verified') is True and population.get('status') == 'computed':
                view['population'] = {'verified': True, 'id': population['value']['namespace'],
                    'evidence_sha256': digest(hierarchy_path), 'scope': population['value']['scope']}
    for relation in hierarchy['relationships']:
        left = [v['view_id'] for v in views.values() if v['catalog_id'] == relation['left']]
        right = [v['view_id'] for v in views.values() if v['catalog_id'] == relation['right']]
        for a in left:
            for b in right:
                relations.append({'view_ids': [a, b], 'status': 'unknown_possible',
                    'historical_source_relation': relation,
                    'reason': 'PACKAGE_OR_REFERENCE_RELATION_RETAINED_WITHOUT_INVENTING_PHYSICAL_PAIRING'})
    cohort = reconcile(entries, list(views.values()), list(executions.values()), relations)
    cohort['execution_precedence'] = ['alpha12', 'alpha13', 'alpha14']
    cohort['superseded_receipts'] = provenance
    # The reconciled identity remains that of the full scientific contract.
    cohort['cohort_id'] = fingerprint({k: v for k, v in cohort.items() if k != 'cohort_id'})
    return cohort, profiles


def synthesize(context, cohort, profiles, folder):
    rows = []
    by_id = {v['view_id']: v for v in cohort['views']}
    for key, data in sorted(profiles.items()):
        view = by_id[key]
        for rep, profile in data['representations'].items():
            rows.append(describe(key, rep, profile, data['representation_agreement'],
                family=view['family'], modality=view['modality'],
                population=view['population'].get('id') if view['population'].get('verified') else None))
    result = compare(rows, cohort['cohort_id'])
    import jsonschema
    jsonschema.validate(result, read('schemas/cross-dataset-synthesis.v1.schema.json'))
    columns = sorted({k for r in rows for k in r['metrics']})
    table = folder/'comparative-matrix.csv'
    with table.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['view_id', 'representation', 'family', 'modality', 'n', 'p']+
            [x for k in columns for x in [k, k+'_status', k+'_reason']])
        for row in rows:
            writer.writerow([row['view_id'], row['representation'], row['family'], row['modality'], row['n_observations'], row['n_bands']]+
                [value for key in columns for value in [row['metrics'].get(key, {}).get(x) for x in ['value', 'status', 'reason']]])
    result['artifact_manifest'] = figures(result, folder)
    result['artifact_manifest'].append({'path': str(table), 'sha256': digest(table), 'role': 'protected_comparative_matrix'})
    # Additional artifacts are referenced separately so the closed scientific
    # schema remains identical to the qualified module's result contract.
    artifacts = result.pop('artifact_manifest')
    return {'synthesis': result, 'artifacts': artifacts}


def figures(result, folder):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['svg.hashsalt'] = 'domains-alpha15-protected'
    rows = result['rows']; metrics = ['pc1_fraction', 'effective_dimension', 'noise_8', 'neighbor_cv', 'proximity_0.01', 'raw_snv_ari']
    output = []
    def save(fig, name):
        fig.tight_layout(); p = folder/(name+'.svg'); fig.savefig(p); plt.close(fig)
        output.append({'path': str(p), 'sha256': digest(p), 'role': name})
    fig, ax = plt.subplots(figsize=(9, 4))
    for i, rep in enumerate(['raw', 'snv']):
        counts = [sum(r['representation'] == rep and r['metrics'][m]['status'] == 'computed' for r in rows) for m in metrics]
        ax.bar([x+i*.38 for x in range(len(metrics))], counts, .38, label=rep)
    ax.set_xticks([x+.19 for x in range(len(metrics))], metrics, rotation=25, ha='right');ax.set_ylabel('Source views with computed descriptor');ax.legend()
    ax.set_title('Availability; source views are not independent studies');save(fig, 'descriptor-availability')
    fig, axes = plt.subplots(2, 3, figsize=(12, 7))
    for metric, ax in zip(metrics, axes.flat):
        changes = next(p for p in result['paired_representation_changes'] if p['metric'] == metric)['matched_views']
        ax.scatter([r['raw'] for r in changes], [r['snv'] for r in changes], s=14, alpha=.6)
        ax.set(xlabel='raw', ylabel='SNV', title=metric)
    fig.suptitle('Within-source representation changes; no outcome-based selection');save(fig, 'paired-representations')
    fig, axes = plt.subplots(2, 3, figsize=(12, 7))
    for metric, ax in zip(metrics, axes.flat):
        for rep in ['raw', 'snv']:
            eligible = [r for r in rows if r['representation'] == rep and r['metrics'][metric]['status'] == 'computed']
            ax.scatter([r['n_observations'] for r in eligible], [r['metrics'][metric]['value'] for r in eligible], s=14, label=rep)
        ax.set(xlabel='n observations (log scale)', ylabel=metric, xscale='log');ax.legend(fontsize=7)
    fig.suptitle('Sample-size support; descriptive and unadjusted');save(fig, 'sample-size-support')
    fig, axes = plt.subplots(2, 3, figsize=(12, 7))
    for metric, ax in zip(metrics, axes.flat):
        for rep in ['raw', 'snv']:
            eligible = [r for r in rows if r['representation'] == rep and r['metrics'][metric]['status'] == 'computed']
            ax.scatter([r['n_bands'] for r in eligible], [r['metrics'][metric]['value'] for r in eligible], s=14, label=rep)
        ax.set(xlabel='p spectral bands (log scale)', ylabel=metric, xscale='log');ax.legend(fontsize=7)
    fig.suptitle('Spectral-width support; unknown population overlap retained');save(fig, 'spectral-width-support')
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    labels = list(__import__('nirs4all_domains.synthesis', fromlist=['PRIMARY']).PRIMARY)+['n_observations', 'n_bands']
    for rep, ax in zip(['raw', 'snv'], axes):
        matrix = [[float('nan')]*len(labels) for _ in labels]
        for item in result['relationships']:
            if item['representation'] != rep or item['association']['status'] != 'computed':continue
            screens = item['association']['value']['screens']; level = sum(s['exceeds'] for s in screens)
            i,j = labels.index(item['left']), labels.index(item['right']);matrix[i][j] = matrix[j][i] = level
        ax.imshow(matrix, vmin=0, vmax=3, cmap='viridis');ax.set_xticks(range(len(labels)), labels, rotation=90, fontsize=6);ax.set_yticks(range(len(labels)), labels, fontsize=6);ax.set_title(rep+' |r| threshold levels 0–3')
    fig.suptitle('Native strict .50/.80/.95 screens; blank = unavailable; no signed r');save(fig, 'descriptor-relationships')
    return output


def main():
    parser = argparse.ArgumentParser();parser.add_argument('--phase', choices=['cohort', 'synthesis'], required=True);args = parser.parse_args()
    context = Context()
    inputs = {'audit': fingerprint(context.audit), 'freeze': fingerprint(context.freeze),
        'profile_execution': digest(context.store.root/'profile-execution.json'),
        'public_alpha12': digest('docs/benchmarks/alpha12/structural-matrix.json'),
        'public_alpha13': digest('docs/benchmarks/alpha13/x-only-extension.json'),
        'source_hierarchy': digest('docs/benchmarks/alpha12/source-hierarchy.json'), 'adapter_revision': 2}
    cohort, profiles = collect(context)
    if args.phase == 'cohort':
        context.run('cohort-v2', inputs, lambda folder: cohort)
    else:
        prior = context.run('cohort-v2', inputs, lambda folder: cohort)
        assert prior == cohort
        context.run('synthesis-v2', {'cohort_id': cohort['cohort_id'], 'synthesis_module': digest('bridges/python/nirs4all_domains/synthesis.py')},
            lambda folder: synthesize(context, cohort, profiles, folder))
    print('ALPHA15_PROTECTED_'+args.phase.upper()+'_COMPLETE; NO_PUBLIC_SCIENTIFIC_EXPORT')


if __name__ == '__main__':
    try: main()
    except Exception as exc:
        try: Context().save('synthesis-controller-failure.json', {'type': type(exc).__name__, 'detail': str(exc)})
        except Exception: pass
        print('ALPHA15_PROTECTED_SYNTHESIS_REFUSED; DETAILS_RETAINED_LOCALLY');raise SystemExit(2)
