"""Complete P1/P2 and prespecified metadata controls without rerunning primary fits."""
import argparse
import json
from pathlib import Path
import subprocess

from nirs4all_domains.adaptive import association, spectral_request, x_characterization
from nirs4all_domains.bank import file_plan
from nirs4all_domains.dependence import development_rows, predictive_dependence, state
from nirs4all_domains.registry import compact_tree
from nirs4all_domains.repeated import PROTOCOL
from nirs4all_domains.split_stress import factor_holdout, intervention_audit
from nirs4all_domains.storage import StageStore, atomic_json, digest, fingerprint

ROOT=Path('.audit/alpha11');PUBLIC=Path('docs/benchmarks/alpha11')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['geometry','controls','pddl'])
    args=parser.parse_args()
    from n4m._ffi import library_path
    library=Path(library_path()).resolve();binary=Path('target/debug/n4domains.exe').resolve()
    policy=json.loads(Path('configs/bank/storage-policy-alpha11.json').read_text())
    store=StageStore('results/alpha9-perten-keyed/state',ROOT/'scratch',ROOT/'evidence',Path.cwd(),policy)
    if args.command=='pddl':
        name='ecosis_tabletop_leaf_drydowns_to_relate_leaf_spectra_and_leaf_reflectance_nirs'
        meta=ROOT/'source'/(name+'-package.json');data=json.loads(meta.read_text())['result']
        if data['license_id']!='odc-pddl':raise ValueError('SOURCE_PDDL_CHANGED')
        path=Path(r'D:\VS projects\nirs_db_vf\standardized_datasets')/name/'X.csv'
        contract={'task':{'task_id':fingerprint([name,'X','domains.adaptive_structure.v0.1'])},
            'source_sha256':digest(path),'metadata_sha256':digest(meta),'license':'odc-pddl',
            'binary_sha256':digest(binary),'runner_sha256':digest(__file__),'adapter_sha256':digest('bridges/python/nirs4all_domains/adaptive.py')}
        def run(folder):
            request=spectral_request(path,'X');request['axis_unit']='nm'
            return {'supersedes_record_id':json.loads((PUBLIC/'public'/(name+'.json')).read_text())['record_id'],
                'reason':'Original PDDL public-domain dedication now explicitly audited; first-pass license allow-list was incomplete.',
                'rights':{'license_id':'odc-pddl','source_metadata_sha256':digest(meta)},
                'report':x_characterization(request,binary,library),'test_target_accessed':False}
        receipt,result=store.run(contract,'P2',file_plan(path,4096,196608,1),run)
        if result is None:raise RuntimeError(receipt)
        atomic_json(PUBLIC/'pddl-followup.json',result)
        print(json.dumps({'pddl_status':receipt['status'],'cache_hit':receipt['cache_hit']}));return
    mean_path=ROOT/'litter/mean-task-v2.json';task=json.loads(mean_path.read_text());rows=development_rows(task)
    admission=json.loads((PUBLIC/'litter-admission.json').read_text());frozen=json.loads((PUBLIC/'litter-evaluation.json').read_text())
    task_id=fingerprint([admission['admission_id'],PROTOCOL])
    contract={'task':{'task_id':task_id},'protocol':'domains.alpha11.litter_details.v0.1','evaluation_id':frozen['evaluation_id'],
              'input_sha256':digest(mean_path),'runner_sha256':digest(__file__),'binary_sha256':digest(binary),'library_sha256':digest(library)}
    if args.command=='geometry':
        prepared=[p for p in (ROOT/'litter').glob('*.json') if p.name in ['task.json','task-v2.json','mean-task-v2.json','transfer.json']]
        nbytes=sum(p.stat().st_size for p in prepared)
        # Charge already-created freeze transport conservatively once, including the failed schema attempt.
        plan={'inputs':[{'sha256':fingerprint({p.name:digest(p) for p in prepared}),'bytes':nbytes}],
              'scratch_bytes':4096,'evidence_bytes':32768,'expected_fits':0,'expected_permutations':0,
              'uncertainty':'Conservative journal charge of existing freeze transport; no additional source acquisition or matrix copy.'}
        receipt,value=store.run(contract,'P1',plan,lambda folder:{'files':{p.name:{'bytes':p.stat().st_size,'sha256':digest(p)} for p in prepared},
            'charged_existing_preparation_bytes':nbytes,'test_target_accessed':False})
        if value is None:raise RuntimeError(receipt)
        def geometry(folder):
            output=folder/'coverage'
            subprocess.run([str(binary),'analyze',str(mean_path),'--out',str(output),'--methods-library',str(library)],check=True,capture_output=True)
            report=json.loads((output/'report.json').read_text())
            request={'source_id':'intact-development','observation_ids':[r['physical_sample_id'] for r in rows],
                'identity_evidence':'verified_physical_identity','axis':task['axis'],'axis_unit':task['axis_unit'],'spectra':[r['x'] for r in rows]}
            xonly=x_characterization(request,binary,library)
            primary=xonly['cluster_settings'][0]
            xy=association([str(v) for v in primary['value']['labels']],[r['y'] for r in rows]) if primary['status']=='computed' else state(reason='X_PARTITION_UNAVAILABLE')
            metadata=association([r['metadata']['species'] for r in rows],[r['y'] for r in rows])
            return {'context':task['context'],'n_development':len(rows),'n_declared_components':len({r['independence_group'] for r in rows}),
                'independent_higher_level_group_count':state(reason='GEN_COLLECTION_AND_ASSAY_LINKS_NOT_FULLY_IDENTIFIED'),
                'canonical_status':report['status'],'canonical_metrics':[{k:v for k,v in m.items() if k!='provenance'} for m in report['metrics']],
                'canonical_report_sha256':digest(output/'report.json'),'canonical_protocol':report['protocol_version'],
                'train_only_x_profile':xonly,'x_partition_target_association':xy,'metadata_species_target_association':metadata,
                'test_target_accessed':report['test_target_accessed']}
        receipt,result=store.run(contract,'P2',file_plan(mean_path,16*2**20,524288,2),geometry)
        destination='litter-geometry.json'
    else:
        def controls(folder):
            models=json.loads((PUBLIC/'litter-model-results.json').read_text())
            base=models['models']['pls_raw_v1']['designs'][0]['value'];folds=frozen['designs']['17']['outer']
            spectral={'outer_fold_set':folds,'oof':[{**r,'null_prediction':r['null']} for r in base['oof']],'lineage':base['lineage']}
            factor={'field':'species','available_at_prediction':True,'source':'original keyed litter species code'}
            result=predictive_dependence(task,library,factor,seed=17,outer_folds=3,inner_folds=3,max_components=3,draws=100,spectral=spectral)
            config={'inner_folds':3,'seed':17,'factor':'species','min_swappable_fraction':.5,'min_swappable_components':6}
            audit={kind:intervention_audit(rows,folds,config,kind) for kind in ['global','within_factor']}
            holdout=factor_holdout(rows,'species',3,3,17)
            return {'factor':'species','matched_dependence':compact_tree(result),'factor_holdout':holdout,
                'training_target_intervention_audit':audit,'size_control':state(reason='NO_ADMISSIBLE_TRUE_SPECIES_HOLDOUT_TO_MATCH'),
                'model_fits_upper':30,'new_spectral_fits':0,'spectral_reuse_evaluation_id':frozen['evaluation_id'],
                'group_support_scope':'24 declared plot/context blocks, not 24 verified independent biological populations',
                'test_target_accessed':False}
        receipt,result=store.run(contract,'P3',file_plan(mean_path,4096,786432,30),controls)
        destination='litter-controls.json'
    if result is None:raise RuntimeError(receipt)
    atomic_json(PUBLIC/destination,result)
    atomic_json(ROOT/(destination.replace('.json','-receipt.json')),receipt)
    print(json.dumps({'stage':destination,'status':receipt['status'],'cache_hit':receipt['cache_hit'],'bytes':(PUBLIC/destination).stat().st_size}))


if __name__=='__main__':main()
