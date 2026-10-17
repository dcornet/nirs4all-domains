"""Fresh native design replay plus exact historical preservation; no full rerun."""
import json
from pathlib import Path

from nirs4all_domains.repeated import run_design
from nirs4all_domains.storage import atomic_json, digest


def main():
    from n4m._ffi import library_path
    from threadpoolctl import threadpool_limits
    root=Path('.audit/alpha11');public=Path('docs/benchmarks/alpha11')
    task=json.loads((root/'litter/mean-task-v2.json').read_text())
    frozen=json.loads((public/'litter-evaluation.json').read_text())
    transfer=json.loads((root/'litter/transfer.json').read_text())
    old=json.loads((public/'litter-model-results.json').read_text())['models']['pls_raw_v1']['designs'][0]
    spec=old['value']['specification']
    with threadpool_limits(limits=1):new=run_design(task,frozen,17,spec,library_path(),transfer)
    if new['status']!='computed' or old['value']['oof']!=new['value']['oof']:raise ValueError('FRESH_NATIVE_OOF_REPLAY_DIFFERS')
    if [r['artifact_sha256'] for r in old['value']['lineage']]!=[r['artifact_sha256'] for r in new['value']['lineage']]:raise ValueError('FRESH_ARTIFACT_REPLAY_DIFFERS')
    protected=json.loads(Path('docs/audit/alpha11-frozen-output-hashes.json').read_text())
    assert all(Path(p).exists() and digest(p)==h for p,h in protected.items())
    proof={'protocol':'domains.repeated_design.v0.1','evaluation_id':frozen['evaluation_id'],'design_id':'17','model':spec['id'],
        'exact_oof_replayed':len(new['value']['oof']),'exact_transfer_predictions_replayed':sum(r['transfer_prediction'] is not None for r in new['value']['oof']),
        'selected_artifacts_exact':True,'model_fits':30,'protected_files_verified':len(protected),'test_target_accessed':False}
    atomic_json(public/'replay.json',proof);print(json.dumps(proof))


if __name__=='__main__':main()
