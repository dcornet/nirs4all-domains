"""Transport-only qualification runner over the native Rust structural protocol.

Requires already qualified explicit alpha.4 task JSON, never changes raw data or
previous outputs. No numeric fitting, PCA, clustering, ARI or metric fallback.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from check_structure_report import check


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def compact(report):
    result={k:report[k] for k in ['protocol_version','engine_version','context','data_origin','input_provenance','status','reason','provider','configuration','population','classification','classification_evidence','held_out_assignment','shortcut_risk_evidence','test_target_accessed','limitations']}
    result['settings']=[]
    for setting in report['settings']:
        entry={k:setting[k] for k in ['parameters','status','reason','failure','comparison_to_primary']}
        fit=setting['reference']
        entry['reference']=None if fit is None else {'pca':{k:v for k,v in fit['pca'].items() if k!='fitted_state'},'n_clusters':fit['hdbscan']['n_clusters'],
            'noise_fraction':fit['noise_fraction'],'physical_labels':dict(zip(fit['physical_sample_ids'],fit['hdbscan']['labels'],strict=True)),
            'cluster_persistence':fit['hdbscan']['cluster_persistence'],'membership_strengths':fit['hdbscan']['membership_strengths'],
            'outlier_scores':fit['hdbscan']['outlier_scores'],'hierarchy_nodes':len(fit['hdbscan']['hierarchy']),
            'nonfinite_diagnostics':fit['hdbscan']['nonfinite_diagnostics']}
        entry['stability']={k:v for k,v in setting['stability'].items() if k not in ['co_membership_pairs','sample_successful_inclusions']}
        entry['resampling_membership_sha256']=hashlib.sha256(json.dumps([{'draw':r['draw'],'components':r['selected_components'],'physical_ids':r['physical_sample_ids']} for r in setting['replicates']],sort_keys=True).encode()).hexdigest()
        entry['fit_failures']=[{k:r[k] for k in ['draw','selected_components','physical_sample_ids','status','reason','failure']} for r in setting['replicates'] if r['fit'] is None]
        result['settings'].append(entry)
    native=report['native_comparison'];result['native_comparison']={k:v for k,v in native.items() if k!='value'}
    if native['value'] is not None:
        result['native_comparison']['value']={k:v for k,v in native['value'].items() if k!='acquisition_fit'}
        f=native['value']['acquisition_fit'];result['native_comparison']['value']['acquisition_fit_summary']={'n_acquisitions':len(f['observation_ids']),
            'n_clusters':f['hdbscan']['n_clusters'],'noise_fraction':f['noise_fraction'],'pca':{k:v for k,v in f['pca'].items() if k!='fitted_state'}}
    else:result['native_comparison']['value']=None
    return result


def run(args):
    output=Path(args.out)
    if output.exists():raise ValueError('A new pilot output directory is required')
    output.mkdir(parents=True)
    baseline=Path(args.baseline_root)
    held=[*baseline.rglob('report.json'),baseline/'predictive-sanity.json',*baseline.rglob('*train-refit-bootstrap.json')]
    before={str(p).replace('\\','/'):sha(p) for p in held}
    summary={'protocol_version':'domains.structure_pilot.v0.1','engine_version':'0.1.0-alpha.5','config_sha256':sha(args.config),
        'runner_sha256':sha(__file__),'domains_binary_sha256':sha(args.binary),'methods_binary_sha256':sha(args.methods_library),
        'baseline_file_hashes_before':before,'tasks':{},'canonical_regression':{}}
    tasks=[(name,str(Path('tests/fixtures/structure')/(name+'.json')),False) for name in ['separated','density','continuum','diffuse','small','nuisance','duplicates','independent_y']]
    tasks.append(('ecosis',args.ecosis_task,True))
    if args.shootout_task:tasks.append(('shootout',args.shootout_task,True))
    for name,task,replay in tasks:
        for suffix in ['', '-repeat'] if replay else ['']:
            destination=output/(name+suffix)
            completed=subprocess.run([args.binary,'structure',task,'--config',args.config,'--out',str(destination),'--methods-library',args.methods_library])
            if completed.returncode not in (0,2) or not (destination/'report.json').exists():raise RuntimeError('Structural CLI did not emit its result')
            check(read(destination/'report.json'))
        report=read(output/name/'report.json')
        if replay and (output/name/'report.json').read_bytes()!=(output/(name+'-repeat')/'report.json').read_bytes():raise AssertionError('Structural replay differs')
        summary['tasks'][name]={**compact(report),'input_task_sha256':sha(task),'report_sha256':sha(output/name/'report.json'),'byte_identical_replay':replay}
        write(output/'qualification-checkpoint.json',summary)
        print(f"{name}: {report['classification']}",flush=True)
    for policy in ['grouped_native','technical_mean']:
        task=baseline/'seed-17'/(policy+'-task.json');dest=output/('coverage-'+policy)
        subprocess.run([args.binary,'analyze',str(task),'--out',str(dest),'--methods-library',args.methods_library],check=True)
        old=read(baseline/'seed-17'/policy/'report.json');new=read(dest/'report.json')
        previous={m['metric_id']:m['value'] for m in old['metrics']};current={m['metric_id']:m['value'] for m in new['metrics']}
        keys=['coverage.effective_dimension','domain.centroid_distance','domain.dispersion_ratio','coverage.test_outside_fraction']
        assert all(previous[k]==current[k] for k in keys)
        assert old['fit']==new['fit']
        summary['canonical_regression'][policy]={'scalar_metrics_unchanged':True,'fitted_state_unchanged':True,'new_report_sha256':sha(dest/'report.json')}
    after={str(p).replace('\\','/'):sha(p) for p in held};assert before==after
    summary['all_alpha4_baselines_unchanged']=True
    write(output/'qualification.json',summary)
    lines=['# Structural pilot comparison','','| Task | Physical units | Components | Classification | Clusters | Noise | Median ARI incl. / excl. noise | Successful draws |','|---|---:|---:|---|---:|---:|---|---:|']
    for name,r in summary['tasks'].items():
        primary=r['settings'][0] if r['settings'] else None;ref=primary['reference'] if primary else None;s=primary['stability'] if primary else {}
        ari=lambda k:s.get(k,{}).get('value',{}).get('median') if isinstance(s.get(k,{}).get('value',{}),dict) else None
        lines.append(f"| {name} | {r['population'].get('n_physical_samples')} | {r['population'].get('n_dependency_components')} | {r['classification']} | {ref['n_clusters'] if ref else 'unavailable'} | {ref['noise_fraction'] if ref else 'unavailable'} | {ari('ari_including_noise')} / {ari('ari_excluding_noise')} | {s.get('successful_draws',0)} |")
    lines+=['','All fits use train only; all stability votes use physical means and whole dependency components. Test HDBSCAN assignment and predictive-reliance conclusions remain unavailable. Canonical alpha.4 fitted states/scalars and all held baseline bytes are unchanged.']
    (output/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['binary','methods-library','config','ecosis-task','baseline-root','out']:parser.add_argument('--'+name,required=True)
    parser.add_argument('--shootout-task')
    run(parser.parse_args())
