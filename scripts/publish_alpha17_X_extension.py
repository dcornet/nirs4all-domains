"""Reuse computed extension rows; publish ordinary source-permitted metrics."""
from collections import Counter
from pathlib import Path

from alpha17_common import Context,read
from run_alpha17_science import compare
from nirs4all_domains.storage import atomic_json,digest
from nirs4all_domains.synthesis import validate_states


def main():
    c=Context();execution=c.load('X-extension-results.json');freeze=c.load('approved-X-execution-freeze.json')
    assert execution['freeze_id']==freeze['freeze_id'] and len(execution['reports'])==8
    sources={s['view_id']:s for s in freeze['sources']};records=[];allowed=[];local=[];run_counts=Counter()
    original_terms={};attributions=[]
    terms=c.load('new-source-public-license-metadata.json')
    for entry in terms['records']:
        if not entry.get('path'):continue
        assert digest(entry['path'])==entry['sha256']
        metadata=read(entry['path'])['result']
        if metadata.get('license_id')=='cc-nc' and metadata.get('license_url')=='http://creativecommons.org/licenses/by-nc/2.0/':
            original_terms[entry['view_id']]=entry
            attributions.append({'view_id':entry['view_id'],'title':metadata['title'],'creators':metadata['author'],
                'source':entry['url'],'license':'CC-BY-NC-2.0','license_url':'https://creativecommons.org/licenses/by-nc/2.0/',
                'citation':next((x['value'] for x in metadata.get('extras',[]) if x['key']=='Citation'),''),
                'modification':'Derived raw/SNV PCA, cluster and neighborhood summary statistics for noncommercial scientific research; no raw observations redistributed.'})
    for item in execution['reports']:
        assert digest(item['artifact_path'])==item['artifact_sha256']
        value=read(item['artifact_path']);s=sources[value['view_id']]
        permission=s['permissions']['publish_aggregates'];published=permission['status']=='allowed' and bool(permission['evidence_receipts'])
        publication_permission='allowed' if published or value['view_id'] in original_terms else permission['status']
        published=publication_permission=='allowed'
        result=value['result'];reason=None
        if result['status']!='computed':
            reason='SOURCE_AXIS_NOT_STRICTLY_INCREASING' if 'DECLARED_AXIS_NOT_STRICTLY_INCREASING' in result['reason'] else 'NATIVE_STARTUP_DLL_DEPENDENCIES_MISSING_BEFORE_SCIENTIFIC_FIT'
        record={'view_id':value['view_id'],'execution_state':result['status'],
            'result':{'status':result['status'],'reason':reason,'value':result['value'] if published else None},
            'aggregate_permission':publication_permission,'ordinary_metrics_published':published and result['status']=='computed',
            'native_PCA_requests':value['native_PCA_requests'],'completed_PCA_profiles':value['completed_PCA_profiles'],
            'observed_python_plus_native_lifetime_peak_upper_bytes':sum(value['peak_bytes'].values()),
            'wall_seconds':value['wall_seconds']}
        if result['status']=='computed':
            local+=result['value']
            if published:allowed+=result['value']
            else:record['result']={'status':'unavailable','reason':'AGGREGATE_PUBLICATION_PERMISSION_UNRESOLVED','value':None}
        records.append(record);run_counts[result['status']]+=1
    old=c.load('science.json');prior_science=read(old['artifact_path']);old_rows=prior_science['all_authorized_rows']
    original_allowed=set(prior_science['public_contributing_views'])
    all_public_rows=[r for r in old_rows if r['view_id'] in original_allowed]+allowed
    summary={'protocol':'domains.alpha17.bounded_X_extension.v0.1','approved_revision':3,
        'scope':'Existing authorized bank; full source X, ordinary permitted aggregates; no Y or supervised fit.',
        'coverage':{'planned_views':8,'computed_views':run_counts['computed'],'failed_views':run_counts['failed'],
            'public_computed_views':len(allowed)//2,'combined_existing_and_new_characterized_views':len({r['view_id'] for r in old_rows+local}),
            'combined_public_computed_views':len(all_public_rows)//2,
            'source_view_accounting':{'declared':171,'computed':53+run_counts['computed'],'failed':11+run_counts['failed'],'unavailable':4,'not_executed':103-8}},
        'native_execution':{'completed_PCA_profiles':sum(r['completed_PCA_profiles'] for r in records),
            'PCA_requests_including_startup_failures':sum(r['native_PCA_requests'] for r in records),
            'completed_profiles_fixed_cluster_attempts':sum(r['completed_PCA_profiles']*2 for r in records),
            'new_reservation_bytes':16777216,'campaign_reserved_bytes':c.guard()['campaign_reserved_bytes'],
            'supervised_fits':0,'numeric_target_cells_decoded':0,'B60_refits':0},
        'views':records,'extension_comparison':compare(allowed),
        'updated_public_bank_comparison':compare(all_public_rows),
        'licensing':{'source_attributions':attributions,
            'scope':'Two newly resolved source grants permit attributed noncommercial derived-statistics publication. These result rows retain CC BY-NC 2.0 terms; repository software licensing is unchanged. NGEE aggregate permission remains unresolved.'},
        'limitations':['Three computed source views do not establish three independent studies.',
            'The extension still has failed and unexecuted views; convenience and publication subsets are not a representative bank sample.',
            'Two source axes fail the existing strictly increasing-axis contract. No silent sorting, dropped bands or numeric repair.',
            'Three initial native-startup failures are retained; the child DLL search directory was corrected only for subsequent views.',
            'Query-design support and missing exact full moments remain explicit; no arbitrary substitutes.',
            'PCA request counts include three failed native starts with no evidence of a numerical fit.',
            'Reported RAM sums Python and native lifetime peaks, a conservative bound rather than a simultaneous resident measurement.'],
        'H1_H5_changed':False,'independent_generalization':False}
    validate_states(summary);atomic_json('docs/benchmarks/alpha17/X-extension-summary.json',summary)
    c.save('X-extension-publication-receipt.json',{'path':'docs/benchmarks/alpha17/X-extension-summary.json',
        'sha256':digest('docs/benchmarks/alpha17/X-extension-summary.json'),
        'published_views':[r['view_id'] for r in records if r['ordinary_metrics_published']],
        'full_authorized_comparison':compare(old_rows+local)})
    c.preservation()
    print('ALPHA17_NEW_X_SCIENCE_PUBLISHED; FAILED_VIEWS_RETAINED; SOURCE_PERMISSIONS_REUSED')


if __name__=='__main__':
    try:main()
    except Exception as error:
        try:Context().save('X-publication-failure.json',{'type':type(error).__name__,'detail':str(error)})
        except Exception:pass
        print('ALPHA17_X_PUBLICATION_REFUSED; DETAILS_REMAIN_LOCAL');raise SystemExit(2) from None
