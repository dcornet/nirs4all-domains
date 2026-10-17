"""Freeze original keyed litter admission, then run bounded native grouped refits."""
import argparse
import csv
import json
import math
import os
from pathlib import Path
import subprocess
import time

from nirs4all_domains.admission import DIMENSIONS, freeze_admission, verify_admission
from nirs4all_domains.bank import schema_check
from nirs4all_domains.dependence import development_rows
from nirs4all_domains.repeated import freeze, run_design, summarize_designs, PROTOCOL
from nirs4all_domains.storage import StageStore, atomic_json, digest, fingerprint
from run_alpha10_multifamily import peak_memory

ROOT=Path('.audit/alpha11')
PUBLIC=Path('docs/benchmarks/alpha11')
DATASET='ecosis_intact_and_ground_leaf_litter_spectra_from_cedar_creek_reflectance_nirs'
BASE=ROOT/'datasets-cache/alpha11-litter/raw/original-v1'


def immutable(path,value):
    if path.exists():
        if json.loads(path.read_text())!=value:raise ValueError('IMMUTABLE_ALPHA11_RECORD_CHANGED:'+str(path))
    else:atomic_json(path,value)


def original(name):
    with (BASE/name).open(encoding='utf-8-sig') as f:
        reader=csv.DictReader(f);axis=[c for c in reader.fieldnames if c.isdigit()];rows=list(reader)
    if len({r['ID'] for r in rows})!=len(rows):raise ValueError('DUPLICATE_ORIGINAL_KEY')
    for r in rows:
        if r['ID']!='_'.join(r[k] for k in ['plot','individual','species','number']):raise ValueError('ORIGINAL_ENCODED_ID_CONTRADICTION')
    return axis,{r['ID']:r for r in rows}


def inputs():
    for r in json.loads((ROOT/'litter-origin.json').read_text())['files']:
        if digest(r['path'])!=r['sha256']:raise ValueError('ORIGINAL_SOURCE_CHANGED')
    axis,rows=original('intact_spec.csv');other,ground=original('ground_spec.csv')
    if axis!=other:raise ValueError('ORIGINAL_PAIRED_AXES_DIFFER')
    return assemble(axis,rows,ground)


def assemble(axis,rows,ground):
    """Partition from identity metadata before any numeric reference comparison."""
    groups=sorted({r['plot'] for r in rows.values()},key=lambda g:fingerprint([17,'litter:plot:'+g]))
    retained=set(groups[:math.ceil(.2*len(groups))])
    shared=set(rows)&set(ground)
    for s in shared:
        if any(rows[s][k]!=ground[s][k] for k in ['plot','individual','species','number']):raise ValueError('PAIRED_METADATA_OR_REFERENCE_CONTRADICTION')
        if rows[s]['plot'] not in retained and rows[s]['Nmass']!=ground[s]['Nmass']:raise ValueError('PAIRED_DEVELOPMENT_REFERENCE_CONTRADICTION')
    task={'schema_version':1,'context':{'dataset_id':DATASET,'content_version':'original-2024-alpha11-keyed-v1','source_id':'intact',
            'target_id':'Nmass','split_id':'plot-block-sealed17-refit17_31_47'},'data_origin':'user_provided','axis':list(map(float,axis)),
          'axis_unit':'nm','signal_unit':'source reflectance','target_unit':'percent nitrogen dry mass; source Nmass %',
          'policy':{'independence_unit':'group','representation':'technical_mean','seed':17,'pca_max_components':20,
                    'pca_variance_fraction':.95,'pca_backend':'flexible'},'observations':[]}
    for key,r in sorted(rows.items()):
        # Partition precedes target-cell access. Original logical assays remain source scoped.
        train=r['plot'] not in retained
        task['observations'].append({'observation_id':'litter:intact:'+key,'sample_id':key,'physical_sample_id':'litter:'+key,
            'independence_group':'litter:plot:'+r['plot'],'individual_id':'litter:'+r['plot']+':'+r['individual']+':'+r['species'],
            'partition':'train' if train else 'test','x':[float(r[c]) for c in axis],
            'y':float(r['Nmass']) if train else None,'reference_id':'litter:Nmass:'+key,'reference_status':'exact',
            'reference_unit':task['target_unit'],'metadata':{'species':r['species'],'plot':r['plot'],'individual':r['individual'],
            'instrument':'Spectral Evolution PSR+ 3500','campaign':'litter-2024'}})
    transfer={'litter:'+s:[float(ground[s][c]) for c in axis] for s in sorted(shared) if rows[s]['plot'] not in retained}
    audit={'n_intact':len(rows),'n_ground':len(ground),'n_paired':len(shared),'missing_ground_keys':sorted(set(rows)-set(ground)),
           'extra_ground_keys':sorted(set(ground)-set(rows)),'n_declared_plot_contexts':len(groups),'retained_groups':sorted(retained),
           'n_development':sum(r['partition']=='train' for r in task['observations']),
           'n_retained':sum(r['partition']=='test' for r in task['observations']),'n_transfer_development':len(transfer),
           'axis_sha256':fingerprint(axis),'paired_reference_exact':True,'test_target_accessed':False,
           'paired_reference_check_scope':'development numeric values only; retained identity keys only',
           'limits':['GEN collection-period provenance is incomplete; all GEN observations stay one conservative block.',
                     'MPLS trees share one residential-site block. Numeric plots are experimental units, not independent source studies.',
                     'Logical assay ownership is keyed; assay batch/event IDs and precision are unavailable.']}
    return task,transfer,audit


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['freeze','run','replay'])
    args=parser.parse_args()
    from n4m._ffi import library_path
    library=Path(library_path()).resolve();binary=Path('target/debug/n4domains.exe').resolve()
    task,transfer,audit=inputs();policy=json.loads(Path('configs/bank/storage-policy-alpha11.json').read_text())
    folder=ROOT/'litter';folder.mkdir(parents=True,exist_ok=True);PUBLIC.mkdir(parents=True,exist_ok=True)
    task_path=folder/'task-v2.json';mean_path=folder/'mean-task-v2.json'
    specs=[{'id':'pls_raw_v1','engine':'methods','method':'models.pls.pls_regression','preprocessing':'raw','grid':{'n_components':[1,2,3]}},
           {'id':'ridge_tuned_v1','engine':'methods','method':'models.regularized.ridge','preprocessing':'raw','grid':{'alpha':[.0001,.01,1,100,10000]}},
           {'id':'pls_snv_v1','engine':'methods','method':'models.pls.pls_regression','preprocessing':'snv','grid':{'n_components':[1,2,3]}}]
    runtime_path=ROOT/'qualified-model-runtime.json'
    if args.command=='freeze' and (PUBLIC/'litter-admission.json').exists():
        admitted=json.loads((PUBLIC/'litter-admission.json').read_text());verify_admission(admitted)
        if json.loads(task_path.read_text())!=task:raise ValueError('ISOLATED_SOURCE_ADAPTER_CHANGED_SANITIZED_TASK')
        immutable(PUBLIC/'litter-original-audit-isolated.json',audit)
        print(json.dumps({'existing_admission_preserved':True,'isolated_task_exact':True,'paired_reference_scope':audit['paired_reference_check_scope']}));return
    if runtime_path.exists() and args.command!='freeze':
        from importlib.metadata import version
        if version('dag-ml')!='0.3.41' or version('nirs4all-methods')!='1.3.6':raise ValueError('QUALIFIED_PROVIDER_VERSION_CHANGED')
        admitted=json.loads((PUBLIC/'litter-admission.json').read_text());verify_admission(admitted)
        runtime=json.loads(runtime_path.read_text())
        if any(digest(p)!=h for p,h in runtime['scientific_sources'].items()):raise ValueError('QUALIFIED_NUMERICAL_CONTROLLER_CHANGED')
        if digest(runtime['executed_runner_archive'])!=runtime['executed_runner_sha256']:raise ValueError('EXECUTED_CONTROLLER_ARCHIVE_CHANGED')
        if json.loads(task_path.read_text())!=task:raise ValueError('ISOLATED_SOURCE_ADAPTER_CHANGED_SANITIZED_TASK')
        legacy=runtime['qualified_contract']
        if legacy['task']['task_id']!=fingerprint([admitted['admission_id'],PROTOCOL]):raise ValueError('QUALIFIED_ADMISSION_CHANGED')
        if digest(mean_path)!=legacy['input_sha256'] or digest(library)!=legacy['library_sha256'] or fingerprint(transfer)!=legacy['transfer_sha256']:
            raise ValueError('QUALIFIED_SOURCE_CONTENT_OR_PROVIDER_CHANGED')
        store=StageStore('results/alpha9-perten-keyed/state',ROOT/'scratch',ROOT/'evidence',Path.cwd(),policy)
        def no_refit(folder):raise ValueError('QUALIFIED_CHECKPOINT_MISSING; NEW_FITTING_REQUIRES_A_NEW_EXECUTION_CONTRACT')
        plan={'inputs':[],'scratch_bytes':0,'evidence_bytes':0,'expected_fits':0,'expected_permutations':0,'uncertainty':'Verified exact legacy checkpoint, no refit.'}
        receipt,result=store.run(legacy,'P3',plan,no_refit)
        if result is None or not receipt['cache_hit'] or digest(PUBLIC/'litter-model-results.json')!=runtime['model_results_sha256']:
            raise ValueError('QUALIFIED_MODEL_CHECKPOINT_NOT_REUSED')
        atomic_json(ROOT/'guarded-model-cache-hit.json',{'cache_hit':True,'execution_id':receipt['execution_id'],'scientific_sources_verified':runtime['scientific_sources'],
            'source_adapter_scope':audit['paired_reference_check_scope'],'test_target_accessed':False})
        print(json.dumps({'cache_hit':True,'execution_id':receipt['execution_id'],'no_model_refit':True}));return
    if args.command=='freeze':
        origin=json.loads((ROOT/'litter-origin.json').read_text());source_hashes={r['name']:r['sha256'] for r in origin['files']}
        admission=freeze_admission({'dataset_id':DATASET,'catalog_revision':'e68d1befb6cb8245799e83d4b4e4c41e66287689',
            'content_version':task['context']['content_version'],'source_hashes':source_hashes,
            'scientific_reference':['https://data.ecosis.org/dataset/85ca4a2e-0a61-4ef7-9e0f-ffa6ea1c2c22','10.5061/dryad.hdr7sqvrk'],
            'permissions':{k:{'status':'allowed','evidence':['Official EcoSIS cc-by license, package metadata pinned in original acquisition.',
                'Attribution: Shan Kothari, Sarah Hobbie, Jeannine Cavender-Bares; Intact- and ground-leaf litter spectra from Cedar Creek and Minneapolis.']} for k in DIMENSIONS},
            'source_id':'intact','target':{'name':'Nmass','semantic_role':'quantitative_measurement','meaning':'Litter nitrogen concentration',
                'unit':task['target_unit'],'evidence':['Original metadata_fields.csv: Nmass, %, Percent nitrogen']},
            'identities':{'original_sample_keys':{'status':'verified','evidence':['Original ID equals plot_individual_species_number, unique in each source.']},
                'source_reference_alignment':{'status':'verified','evidence':['Spectra, source ID and Nmass share one original keyed CSV record; no standardized Y.csv used.']},
                'reference_scope':'logical original sample/Nmass; shared laboratory batch precision unknown'},
            'dependencies':{'rule':'whole original plot; GEN and MPLS conservative contexts, plus original individual and reference links','audit':audit},
            'factors':{'species':'original species code','plot':'original metadata_fields plot definition'},'representation':'singleton source-averaged intact spectrum, complete 2001-band axis',
            'split':{'rule':'identity-only sealed 20% plot blocks then grouped repeated nested CV','seed':17,'memberships':[{'id':r['physical_sample_id'],'component':r['independence_group'],'partition':r['partition']} for r in task['observations']]},
            'independent_units':31,'missing_fields':['assay events and precision','GEN collection provenance','independent source-population replicates'],
            'budget':{'policy_sha256':digest('configs/bank/storage-policy-alpha11.json'),'model_fits_upper':324,'scratch_upper_bytes':48*2**20,
                      'evidence_upper_bytes':2*2**20,'estimated_peak_memory_bytes':800*2**20,'estimated_seconds':300},
            'review_evidence':['Original open package and metadata definitions; independent litter material/study versus Perten and CA2023.',
                               'Paired missing key inventoried before scores; all 322 intact observations retained.']})
        if admission['status']!='admitted':raise ValueError(admission['reasons'])
        schema_check(admission,'task-admission');immutable(PUBLIC/'litter-admission.json',admission)
        immutable(PUBLIC/'litter-original-audit.json',audit);immutable(task_path,task)
        if not mean_path.exists():
            subprocess.run([str(binary),'represent',str(task_path),'--out',str(mean_path),'--methods-library',str(library)],check=True)
        mean=json.loads(mean_path.read_text());frozen=freeze(mean,specs,transfer_hash=fingerprint(transfer))
        immutable(PUBLIC/'litter-evaluation.json',frozen)
        immutable(folder/'transfer.json',transfer)
        print(json.dumps({'admission':admission['status'],'evaluation_id':frozen['evaluation_id'],**audit}))
        return
    admission=json.loads((PUBLIC/'litter-admission.json').read_text());verify_admission(admission)
    if {r['name']:r['sha256'] for r in json.loads((ROOT/'litter-origin.json').read_text())['files']}!=admission['specification']['source_hashes']:raise ValueError('ADMITTED_SOURCE_CHANGED')
    mean=json.loads(mean_path.read_text());frozen=json.loads((PUBLIC/'litter-evaluation.json').read_text())
    store=StageStore('results/alpha9-perten-keyed/state',ROOT/'scratch',ROOT/'evidence',Path.cwd(),policy)
    contract={'task':{'task_id':fingerprint([admission['admission_id'],PROTOCOL])},'evaluation_id':frozen['evaluation_id'],
              'input_sha256':digest(mean_path),'transfer_sha256':fingerprint(transfer),'controller_sha256':digest(__file__),
              'bridge_sha256':digest('bridges/python/nirs4all_domains/repeated.py'),'library_sha256':digest(library),
              'providers':{'Methods':'1.3.6/ABI2.19','DAG-ML':'0.3.41'},'protocol':PROTOCOL}
    plan={'inputs':[{'path':str(mean_path.resolve()),'sha256':digest(mean_path),'bytes':mean_path.stat().st_size}],
          'scratch_bytes':4096,'evidence_bytes':2*2**20,'expected_fits':324,'expected_permutations':0,
          'uncertainty':'3 grouped seeds, 3 outer/inner folds, PLS3/Ridge5/SNVPLS3. Native states in memory; same fitted models predict both preparations.'}
    def run(scratch):
        from threadpoolctl import threadpool_limits
        began=time.perf_counter();models={}
        with threadpool_limits(limits=1):
            for spec in frozen['specifications']:
                results=[run_design(mean,frozen,s,spec,library,transfer) for s in [17,31,47]]
                models[spec['id']]={'designs':results,'refit_variation':summarize_designs(results)}
                print(json.dumps({'model':spec['id'],'states':[r['status'] for r in results]}),flush=True)
        return {'evaluation_id':frozen['evaluation_id'],'models':models,'elapsed_seconds':time.perf_counter()-began,
                'peak_resident_bytes':peak_memory(),'memory_scope':'OS Python process lifetime high-water RSS; native kernels in process',
                'model_fits_upper':324,'test_target_accessed':False}
    receipt,result=store.run(contract,'P3',plan,run)
    atomic_json(folder/'model-receipt.json',receipt)
    if result is None:raise RuntimeError(receipt)
    immutable(PUBLIC/'litter-model-results.json',result)
    print(json.dumps({'status':receipt['status'],'cache_hit':receipt['cache_hit'],'seconds':result['elapsed_seconds'],'peak':result['peak_resident_bytes']}))


if __name__=='__main__':main()
