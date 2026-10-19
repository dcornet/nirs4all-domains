"""Summarize existing execution receipts; no data decoding or scientific refit."""
from pathlib import Path
from alpha18_common import Context,read
from nirs4all_domains.storage import atomic_json,digest


def main():
    c=Context();stages={};evidence={}
    for phase in ['X','reference']:
        name=phase+'-worker-observations.json';runs=c.load(name)
        stages[phase]={'worker_processes':len(runs),
            'worker_wall_seconds':sum(r['wall_seconds'] for r in runs),
            'nonzero_worker_exits':sum(r['exit_code']!=0 for r in runs)}
        evidence[name]=digest(c.root/name)
    x=[read(r['artifact_path']) for r in c.load('X-progress.json') if r.get('artifact_path')]
    stages['X'].update(source_attempts=len(x),
        maximum_sum_of_separate_python_and_native_peak_high_water_marks_bytes=max(sum(r['peak_bytes'].values()) for r in x))
    for phase,name in [('reference','reference-progress.json'),('raw_stress','stress-progress.json'),
                       ('SNV_stress','SNV-stress-progress.json'),('declared_plot','group-sensitivity-progress.json')]:
        rows=[read(r['artifact_path']) for r in c.load(name) if r.get('artifact_path')]
        stages.setdefault(phase,{})
        stages[phase].update(task_receipts=len(rows),
            summed_task_wall_seconds=sum(r.get('wall_seconds',0) for r in rows),
            maximum_process_lifetime_peak_bytes=max(r.get('peak_resident_bytes',0) for r in rows),
            pipeline_model_attempts=sum(r.get('model_fit_attempts',0) for r in rows),
            successful_native_fit_predictions=sum(r.get('model_fit_successes',0) for r in rows))
        evidence[name]=digest(c.root/name)
    v={'protocol':'domains.scientific_resource_receipts.v1','stages':stages,
       'resource_receipt_sha256':evidence,'current_storage':c.guard(),
       'measurement_scope':'Existing receipt timings include task/worker overhead. Process peaks are lifetime high-water marks, not per-model allocations. X is a conservative sum of separate process peaks, not a measured simultaneous peak.',
       'timing_limit_scope':'Worker limit is 8 cumulative hours; null-only continuation and engineering/validation timings are not complete scientific wall-time measurements.',
       'raw_stress_watchdog':'Initial helper had concurrent ctypes faults; all five raw artifacts completed and final OS lifetime peaks were below 2 GiB. Do not claim a clean continuously enforced raw-stress run. See memory-watchdog-continuation.json.',
       'null_only_tasks':len(c.load('null-progress.json')),'null_only_model_fits':0,
       'historical_reused_X_profiles':56,'new_model_execution':False}
    c.save('scientific-execution-resources.json',v)
    atomic_json('docs/campaign/scientific-execution-resources.json',v)
    print('EXISTING_SCIENTIFIC_RESOURCE_RECEIPTS_SUMMARIZED')


if __name__=='__main__':main()
