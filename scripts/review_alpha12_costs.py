"""Admit only the five already frozen remaining cases using measured sentinel cost."""
import json
from pathlib import Path
import shutil
from nirs4all_domains.storage import atomic_json,digest,tree_bytes


def main():
    root=Path('.audit/alpha12');public=Path('docs/benchmarks/alpha12')
    frozen=json.loads((public/'input-freeze.json').read_text())
    journal=json.loads(Path('results/alpha9-perten-keyed/state/journal.json').read_text())
    stages=[r for r in journal['runs'].values() if r.get('contract',{}).get('phase')=='structural-resampling']
    assert len(stages)==160 and all(r['status']=='computed' for r in stages)
    summaries=[r for r in journal['runs'].values() if r.get('contract',{}).get('phase')=='structural-stability-summary']
    assert len(summaries)==8 and all(r['status']=='computed' for r in summaries)
    callbacks=sum(r['duration_seconds'] for r in stages)
    start_times=[(root/'scratch'/r['execution_id']/'P3'/str(r['attempt'])).stat().st_ctime for r in stages]
    span=max(t+r['duration_seconds'] for t,r in zip(start_times,stages,strict=True))-min(start_times)
    profiles=2*sum(e['status']=='computed' for e in frozen['entries'])-len(list((public/'profiles').glob('*.json')))
    reservation=profiles*(1048576+4096)+20*(655360+655360)+20*(262144+4096)+4*(1048576+4096)+2*1048576
    occupied=tree_bytes([Path.cwd()]);policy=json.loads(Path('configs/bank/storage-policy-alpha12.json').read_text())
    locators=json.loads((root/'input-locators.json').read_text())
    largest_external=max(sum(Path(v[k]).stat().st_size for k in ('matrix','metadata') if not Path(v[k]).is_relative_to(Path.cwd())) for v in locators.values())
    fixed_validation_allowance=268435456
    physical_new_science_allowance=33554432
    free={v:shutil.disk_usage(v+':/').free for v in ['C','D']}
    admissible=(journal['reserved_campaign_bytes']+reservation<=policy['campaign_bytes']
        and occupied+fixed_validation_allowance+physical_new_science_allowance+largest_external<=policy['workspace_max_bytes']
        and all(v>=policy['reserve_free_bytes'] for v in free.values()))
    result={'freeze_id':frozen['freeze_id'],'sentinel_draws_completed':160,'sentinel_summaries_completed':8,
        'native_callback_seconds':callbacks,'observed_sentinel_admission_span_seconds':span,
        'span_scope':'First-to-last admitted draw, excluding initial admission and final summary; not full launch runtime.',
        'remaining_primary_profiles':profiles,'estimated_additional_reservations':reservation,
        'campaign_reserved_bytes':journal['reserved_campaign_bytes'],'campaign_ceiling':policy['campaign_bytes'],
        'workspace_unique_bytes':occupied,'workspace_ceiling':policy['workspace_max_bytes'],
        'fixed_validation_allowance':fixed_validation_allowance,'new_science_physical_byte_allowance':physical_new_science_allowance,
        'largest_existing_external_source_footprint':largest_external,
        'free_bytes':free,'sentinel_driver_sha256':digest('scripts/run_alpha12_stability.py'),
        'remaining_driver_sha256':digest('scripts/run_alpha12_stability_batched.py'),
        'remaining_prespecified_cases_admitted':admissible,
        'selection_basis':'Measured time/storage only; the seven-source selection, data, seeds and thresholds remain unchanged.',
        'transport_protocol':'domains.alpha12.batched_resume.v0.1','deletions':0,'migrations':0}
    atomic_json(root/'sentinel-cost-review.json',result)
    print(json.dumps(result))
    if not admissible:raise RuntimeError('REMAINING_PRESPECIFIED_CAMPAIGN_NOT_ADMITTED')


if __name__=='__main__':main()
