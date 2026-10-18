"""No-refit controlled qualification and prospective revised-design freeze."""
from collections import Counter
import json
from pathlib import Path
from alpha13_common import PUBLIC,run,publish
from generate_unsupervised_fixtures import scenario
from nirs4all_domains.dependence import state
from nirs4all_domains.stability_power import QUALITY,decision_summary
from nirs4all_domains.storage import atomic_json,digest,fingerprint
from nirs4all_domains.unsupervised import compare_partition


def main():
    frozen=json.loads((PUBLIC/'calibration-freeze.json').read_text());full=json.loads((PUBLIC/'controlled-calibration.json').read_text())
    assert full['freeze_id']==frozen['freeze_id'] and full['native_pca_fits']==6498 and full['native_hdbscan_attempts']==12996
    oracle=json.loads((PUBLIC/'oracle-calibration.json').read_text())
    contract={'task':{'task_id':fingerprint(['alpha13','controlled-qualification'])},'phase':'controlled-no-refit-qualification',
        'calibration_sha256':digest(PUBLIC/'controlled-calibration.json'),'oracle_sha256':digest(PUBLIC/'oracle-calibration.json'),
        'runner_sha256':digest(__file__),'freeze_id':frozen['freeze_id'],'power_source_sha256':frozen['power_bridge_sha256']}
    def qualify(folder):
        latent=[];prefix=[];actual_pca=0;actual_hdb=0;failed=0
        clouds={'separated','overlapping','density_imbalance','satellites','snv_erased','snv_enhanced'}
        for mechanism in frozen['deep_mechanisms']:
            fixture=scenario(mechanism);ids=fixture['spectral']['observation_ids'];units=fixture['components']
            reference=json.loads((PUBLIC/'controls'/(mechanism+'.reference.json')).read_text());actual_pca+=reference['pca_fits'];actual_hdb+=reference['hdbscan_attempts']
            for representation,profile in reference['representations'].items():
                recovery=[state(compare_partition(ids,fixture['generating_x_labels'],ids,s['value']['labels'])) if s['status']=='computed' else s
                    for s in profile['cluster_settings']] if mechanism in clouds else state(reason='GENERATOR_INDEX_LABELS_ARE_NOT_DISCRETE_LATENT_CLOUD_TRUTH')
                latent.append({'mechanism':mechanism,'representation':representation,'recovery':recovery,
                    'reference_sha256':digest(PUBLIC/'controls'/(mechanism+'.reference.json'))})
            for seed in frozen['perturbation_seeds']:
                path=PUBLIC/'controls'/(mechanism+'.'+str(seed)+'.json');batch=json.loads(path.read_text());actual_pca+=batch['pca_fits'];actual_hdb+=batch['hdbscan_attempts']
                for condition,entry in batch['conditions'].items():
                    assert len(entry['records'])==60
                    failed+=sum(r['status']!='computed' for r in entry['records'])
                    report=decision_summary(reference['representations'][condition.split('.')[0]],entry['records'][:20],ids,len(set(units.values())),entry['panels'],
                        'First 20 draws with the frozen B60-selected panel; not the historical alpha.12 panel or a separately selected B20 design.')
                    prefix.append({'mechanism':mechanism,'seed':seed,'condition':condition,'first_20_classifications':[
                        s['value']['classification'] if s['status']=='computed' else s['status'] for s in report['settings']],
                        'batch_sha256':digest(path)})
        assert actual_pca==6498 and actual_hdb==12996
        return {'protocol_version':'domains.stability_power.v0.1','freeze_id':frozen['freeze_id'],
            'actual_unique_pca_fits_verified':actual_pca,'actual_hdbscan_attempts_verified':actual_hdb,'failed_draws':failed,
            'latent_cloud_recovery':latent,'prefix_comparisons':prefix,
            'prefix_classifications':dict(Counter(c for r in prefix for c in r['first_20_classifications'])),
            'full_classifications':full['native_classifications'],'oracle':{'B20':oracle['B20'],'B60':oracle['B60']},
            'new_pca_fits':0,'new_hdbscan_fits':0,'target_accessed':False,'model_performance_used':False,
            'scope':'Fixed generator X; settings/perturbations are dependent conditions, not generative or biological replicates. No real prevalence, causal shortcut inference or continuum certificate.'}
    plan={'inputs':[],'scratch_bytes':4096,'evidence_bytes':524288,'expected_fits':0,'expected_permutations':0,'uncertainty':'Existing native partitions plus native ARI/summary; no PCA/HDBSCAN refits.'}
    store,receipt,value=run(contract,'P4',plan,qualify);publish(store,receipt,'controlled-qualification.json')
    revised={'protocol_version':'domains.stability_power.v0.2','calibration_protocol_version':'domains.stability_power.v0.1',
        'calibration_freeze_id':frozen['freeze_id'],'controlled_qualification_sha256':digest(PUBLIC/'controlled-qualification.json'),
        'controlled_calibration_sha256':digest(PUBLIC/'controlled-calibration.json'),'design_power_sha256':frozen['design_power_sha256'],
        'oracle_calibration_sha256':digest(PUBLIC/'oracle-calibration.json'),'power_bridge_sha256':frozen['power_bridge_sha256'],
        'protocol_sha256':frozen['protocol_sha256'],'draw_count':60,'fractions':[.6,.8],'representations':['raw','snv'],
        'min_cluster_sizes':[8,12],'quality_thresholds':QUALITY,'real_resampling_seed':13051,
        'qualification_scope':'Conditional algorithmic partition reproducibility only; per-task planned exposure feasibility and identity/cost admission remain mandatory.',
        'thresholds_relaxed':False,'test_target_accessed':False,'model_performance_used':False,'universal_shortcut_score':None}
    revised['freeze_id']=fingerprint(revised);path=PUBLIC/'revised-design-freeze.json'
    if path.exists():assert json.loads(path.read_text())==revised
    atomic_json(path,revised)
    print(json.dumps({'revised_design_freeze_id':revised['freeze_id'],'controlled_draw_failures':value['failed_draws'],
        'full_classifications':value['full_classifications'],'first_20_classifications':value['prefix_classifications']}))


if __name__=='__main__':main()
