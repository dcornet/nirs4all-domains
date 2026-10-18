"""Pre-outcome, metadata/stat-only proposal for missing full-source X profiles."""
from collections import Counter
from pathlib import Path

from alpha17_common import Context
from nirs4all_domains.storage import fingerprint


def main():
    c=Context();name='NEXT_X_CAMPAIGN_PLAN.json'
    if (c.root/name).exists():
        c.load(name);print('ALPHA17_NEXT_X_PLAN_REUSED; NOT_AUTHORIZED');return
    audit=c.auth(c.store.root/'screening-rights-reviewed.json','audit')
    profiled={r['view_id'] for r in c.phase('synthesis-v2')['synthesis']['rows']}
    candidates=[]
    for e in audit['entries']:
        if e['access_analysis_eligible'] is not True:continue
        for s in e['sources']:
            key=e['dataset_id']+'/'+s['source_id'];d=s['dimensions'];path=Path(s['matrix_availability']['locator'])
            n,p=d['n_observations'],d['n_variables']
            if key in profiled or not s['modality_eligible'] or not path.is_file():continue
            if not (16<=n<=1200 and 20<=p<=2500 and path.stat().st_size<=4194304):continue
            if min(n,256)*n*p>200000000:continue
            candidates.append({'view_id':key,'family':e['family'],'matrix':str(path),
                'matrix_bytes':path.stat().st_size,'mtime_ns':path.stat().st_mtime_ns,
                'n_observations':n,'n_bands':p,'axis_unit':d['axis_unit'],
                'descriptor_sha256':e['descriptor_sha256'],'permissions':e['permissions'],
                'selection_uses_model_outcomes':False,'source_hash_before_execution':'required; not claimed measured at metadata-only planning'})
    selected=[];families=Counter()
    while candidates and len(selected)<8:
        candidates.sort(key=lambda x:(families[x['family']],x['matrix_bytes'],x['view_id']))
        chosen=candidates.pop(0);selected.append(chosen);families[chosen['family']]+=1
    assert sum(x['matrix_bytes'] for x in selected)<=33554432
    packet={'protocol':'domains.alpha17.bounded_X_extension.v0.1','sources':selected,
        'owner_approved':False,'new_reservation_envelope_bytes':len(selected)*2097152,
        'additional_combined_upper_bytes':134217728,'workspace_ceiling':16289597121,
        'campaign_ceiling':805306368,'maximum_serial_tasks':1,'task_reservation_bytes':2097152,
        'task_scratch_bytes':1048576,'task_essential_evidence_bytes':1048576,
        'whole_participating_input_bytes':sum(x['matrix_bytes'] for x in selected),
        'new_PCA_fit_upper':len(selected)*2,'new_HDBSCAN_attempt_upper':len(selected)*4,
        'numeric_target_cells_to_decode':0,'supervised_model_fits':0,'B60_refits':0,
        'query_product_budget_per_view':200000000,'maximum_query_observations':256,
        'all_reference_observations_and_axes_retained':True,
        'provider':'Existing domains.unsupervised.v0.1 / Methods1.3.6 / Preflight provider; no changed numerical protocol.',
        'estimated_wall_upper_seconds':7200,'estimated_RAM_upper_bytes':1073741824,
        'estimate_status':'Operational stop limits, not measured source-specific native peaks.',
        'rules':['Freeze whole source hashes/providers before computing; changed source fails preflight.',
            'No refit of already completed views, no response-based source selection, no B60.',
            'Ordinary aggregates follow source permissions; unknown publication rights do not block authorized local X analysis.',
            'Retain failures, all observations and missing metrics; no numerical fallback.',
            'No deletion, migration, ledger reset, per-fold X copy or ceiling increase.']}
    packet['plan_id']=fingerprint(packet);c.save(name,packet);c.guard()
    print('ALPHA17_BOUNDED_X_EXTENSION_PROPOSED; NO_EXECUTION_AUTHORIZED')


if __name__=='__main__':
    try:main()
    except Exception:
        print('ALPHA17_X_EXTENSION_PLAN_REFUSED; DETAILS_REMAIN_LOCAL');raise SystemExit(2) from None
