"""Paired retained-X projection, with byte-identical training fitted state."""
import copy
import csv
import json
from pathlib import Path
import subprocess
from nirs4all_domains.bank import file_plan
from nirs4all_domains.storage import StageStore, atomic_json, digest, fingerprint
from run_alpha11_litter import BASE, PUBLIC, ROOT


def main():
    from n4m._ffi import library_path
    mean=ROOT/'litter/mean-task-v2.json';old_path=next((ROOT/'scratch').glob('*/P2/*/coverage/report.json'))
    old=json.loads(old_path.read_text());task=json.loads(mean.read_text())
    with (BASE/'ground_spec.csv').open() as f:ground={r['ID']:r for r in csv.DictReader(f)}
    for r in task['observations']:
        if r['partition']=='test':
            key=r['sample_id'];r['x']=[float(ground[key][str(int(w))]) for w in task['axis']]
            r['observation_id']='litter:ground:'+key;r['metadata']['preparation']='ground';r['y']=None
    task['context']['source_id']='intact_train_ground_retained'
    admission=json.loads((PUBLIC/'litter-admission.json').read_text())
    contract={'task':{'task_id':fingerprint([admission['admission_id'],'domains.repeated_design.v0.1'])},
              'protocol':'domains.alpha11.transfer_geometry.v0.1','input_sha256':fingerprint(task),
              'reference_report_sha256':digest(old_path),'protocol_sha256':digest('docs/ALPHA11_TRANSFER_GEOMETRY_PROTOCOL.md'),
              'runner_sha256':digest(__file__)}
    policy=json.loads(Path('configs/bank/storage-policy-alpha11.json').read_text())
    store=StageStore('results/alpha9-perten-keyed/state',ROOT/'scratch',ROOT/'evidence',Path.cwd(),policy)
    def run(folder):
        source=folder/'paired-task.json';atomic_json(source,task)
        subprocess.run([str(Path('target/debug/n4domains.exe').resolve()),'analyze',str(source),'--out',str(folder/'coverage'),
            '--methods-library',str(Path(library_path()).resolve())],check=True,capture_output=True)
        report=json.loads((folder/'coverage/report.json').read_text())
        if report['fit']!=old['fit'] or report['test_target_accessed']:raise ValueError('PAIRED_HELDOUT_X_CHANGED_TRAINING_FIT')
        ids=['domain.centroid_distance','domain.dispersion_ratio','coverage.test_outside_fraction']
        def extract(r):return [{k:v for k,v in m.items() if k in ['metric_id','status','reason','value','population','parameters','unit']} for m in r['metrics'] if m['metric_id'] in ids]
        return {'protocol':contract['protocol'],'same_training_fit_exact':True,'fit_x_sha256':report['fit']['fit_x_sha256'],
            'n_train_intact':298,'n_paired_retained':24,'intact_support':extract(old),'ground_support':extract(report),
            'report_sha256':digest(folder/'coverage/report.json'),'scope':'Additional post-response X-only explanatory probe; no calibration of failure probability',
            'test_target_accessed':False}
    receipt,result=store.run(contract,'P2',file_plan(mean,16*2**20,65536,1),run)
    if result is None:raise RuntimeError(receipt)
    atomic_json(PUBLIC/'transfer-geometry.json',result);print(json.dumps({'status':receipt['status'],'cache_hit':receipt['cache_hit'],'training_fit_exact':result['same_training_fit_exact']}))


if __name__=='__main__':main()
