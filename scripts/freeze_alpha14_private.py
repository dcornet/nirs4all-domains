"""Owner-scoped full-bank admission and prospective source/cost selection.

Only permitted provided X files are fingerprinted, after the rights decision.
No X cells/targets or model outcomes are decoded; all details stay outside Git.
"""
from collections import Counter,defaultdict
import hmac
import json
from pathlib import Path

from nirs4all_domains.privacy import PrivateStore,PROTOCOL,authorize,opaque_id,fail
from nirs4all_domains.storage import atomic_json,digest,fingerprint,tree_bytes


def main():
    config=json.loads(Path('.audit/alpha14/private-root.json').read_text())
    store=PrivateStore(config['root'],Path.cwd())
    output=store.root/'execution-freeze.json'
    if output.exists():fail('IMMUTABLE_PRIVATE_INPUT_FREEZE_EXISTS')
    approval=json.loads(Path('.audit/alpha14/budget-approval.json').read_text())
    policy=json.loads(Path('configs/bank/storage-policy-alpha14.json').read_text())
    assert approval['owner_approved'] is True and approval['workspace_ceiling']==policy['workspace_max_bytes']
    owner=json.loads((store.root/'owner-local-analysis-attestation.json').read_text())
    assert hmac.compare_digest(owner['authentication'],store.authenticate(owner['attestation']))
    attest=owner['attestation'];evidence=attest['receipt_id']
    initial=json.loads((store.root/'screening-initial.json').read_text())
    assert hmac.compare_digest(initial['authentication'],store.authenticate(initial['audit']))
    rows=initial['audit']['entries']
    original=json.loads((store.root/'source-rights/rights-review.json').read_text())['audit']
    leads={e['dataset_id']:e for e in original['records']}
    perten=json.loads(Path('docs/benchmarks/alpha9/perten-admission.json').read_text())
    prior=set(json.loads(Path('docs/benchmarks/alpha12/input-freeze.json').read_text())['stability_subset'])
    previous_names={'ucph_tablet_nir','ohpl_soil_nir','perten_cereals_nir'}
    candidates=[]
    for entry in rows:
        name=entry['dataset_id']
        if entry['catalog_tier']!='private':continue
        entry['original_permission_review']=leads.get(name,{'status':'unknown','reason':'NO_NEW_PRIMARY_DOCUMENT_CLEARANCE; OWNER_LOCAL_SCOPE_RECORDED_SEPARATELY'})
        present=[s for s in entry['sources'] if s['matrix_availability']['exists']]
        if name in attest['explicit_exclusions']:
            entry['reasons']=['OWNER_DECISION_RETAINS_PENDING_RIGHTS'];entry['access_analysis_eligible']=False;continue
        if not present:
            entry['reasons']=['NOT_IN_OWNER_PROVIDED_LOCAL_CACHE'];entry['access_analysis_eligible']=False;continue
        for k in ['access','analysis']:
            entry['permissions'][k]={'status':'allowed','evidence_receipts':[evidence]}
        if name=='perten_cereals_nir':
            for k,old in [('publish_aggregates','publish_statistics'),('redistribute_raw','redistribute_raw')]:
                entry['permissions'][k]={'status':perten['specification']['permissions'][old]['status'],
                    'evidence_receipts':[entry['receipt_id']]}
            entry['permission_basis']={'path':'docs/benchmarks/alpha9/perten-admission.json','sha256':digest('docs/benchmarks/alpha9/perten-admission.json')}
        entry['admission_tier']='A' if name in previous_names else 'B'
        entry['access_analysis_eligible']=True;entry['reasons']=[]
        entry['confidentiality'].update(local_X_handling='authorized_under_owner_attestation',
            publish_aggregates='not_newly_granted',targets_metadata='not_used_in_this_campaign')
        entry['supervised_eligibility']={'status':'unavailable','reason':'NO_EXACT_ORIGINAL_REFERENCE_DEPENDENCY_TASK_AND_SEPARATE_PILOT_BUDGET_CLOSURE','value':None}
        for source in present:
            source['new_execution_decision']='not_selected'
            if name in previous_names:
                source['new_execution_decision']='historical_source_not_repeated';continue
            if not source['modality_eligible']:
                source['new_execution_decision']='outside_qualified_physical_NIR_modality';continue
            if not source['geometry_work_qualified']:
                source['new_execution_decision']='full_source_work_budget_not_qualified';continue
            if source['dimensions']['n_observations']<2:
                source['new_execution_decision']='insufficient_source_observations';continue
            path=Path(source['matrix_availability']['locator'])
            if not source['source_id'].startswith('X') or path.name!=source['source_id']+'.csv':
                source['new_execution_decision']='spectral_only_locator_not_qualified';continue
            # Owner-supplied and permitted bytes only, not unadmitted resources.
            spec={'protocol':PROTOCOL,'visibility':'local_private','receipt_id':opaque_id(),
                'source_scope':name+'/'+source['source_id'],
                'permissions':{k:{'status':'allowed' if k in ['access','analysis'] else 'unknown',
                    'evidence_receipt':evidence if k in ['access','analysis'] else None}
                    for k in ['access','analysis','publish_aggregates','redistribute_raw']},
                'sensitive_handling':{'status':'allowed','evidence_receipt':evidence},'participation_public':False}
            authorize(spec)
            candidates.append({'entry':entry,'source_record':source,'admission':spec,'matrix':str(path.resolve()),
                'authorized_cache_root':config['source_root'],'source_id':source['source_id'],
                'identity_evidence':'observation_identity_only',
                'evidence_upper_bytes':4*1024*1024-65536,'scratch_upper_bytes':16384,
                'shape':[source['dimensions']['n_observations'],source['dimensions']['n_variables']],
                'study_scope':'unverified-original-study:'+name,'population_scope':'owner-provided-source:'+name,
                'source_receipt_id':opaque_id(),'evidence_receipt_id':opaque_id(),
                'axis_unit':source['dimensions']['axis_unit'],
                'original_axis_qualification':{'status':'unavailable','reason':'COMPLETE_CANONICAL_DECLARED_AXIS; ORIGINAL_NUMERIC_CORRESPONDENCE_NOT_REVERIFIED','value':None},
                'original_study_independence_verified':False,'canonical_source_family':entry['family']})
    families=['soil','grain','food','pharmaceutical','unresolved','vegetation','spectral_library']
    groups=defaultdict(list)
    for c in candidates:groups[c['entry']['family']].append(c)
    for g in groups.values():g.sort(key=lambda c:(c['source_record']['dimensions']['pca_full_population_work'],c['source_record']['matrix_availability']['bytes'],c['entry']['dataset_id'],c['source_id']))
    chosen=[];charged=0
    while any(groups.values()) and len(chosen)<24:
        for family in families:
            if not groups[family]:continue
            c=groups[family].pop(0);size=c['source_record']['matrix_availability']['bytes']
            if charged+size>128*1024*1024:
                c['source_record']['new_execution_decision']='participating_cache_envelope_exceeded';continue
            charged+=size;chosen.append(c);c['source_record']['new_execution_decision']='frozen_for_private_X_screening'
            if len(chosen)==24:break
    deep=[];seen=set()
    for c in chosen:
        family=c['entry']['family']
        if len(deep)<3 and family not in seen and c['shape'][0]>=30:
            c['deep_selected']=True;deep.append(c['source_receipt_id']);seen.add(family)
        else:c['deep_selected']=False
    sources=[]
    for c in chosen:
        c.pop('entry');c.pop('source_record');c['source_sha256']=digest(c['matrix']);sources.append(c)
    old_inputs=json.loads(Path('.audit/alpha13/input-locators.json').read_text())
    participating=sorted(set([c['matrix'] for c in sources]+[v['matrix'] for v in old_inputs.values()]))
    for c in sources:c['other_participating_files']=participating
    # Reserve 4 MiB per profile source and 2 MiB per B60 condition. This is
    # conservative cumulative scheduler accounting, not claimed actual evidence.
    upper=sum(c['evidence_upper_bytes']+c['scratch_upper_bytes'] for c in sources)+len(deep)*4*3*1024*1024
    assert upper<=approval['new_reservation_envelope']
    assert tree_bytes([Path.cwd(),store.root,*participating])+upper<=policy['workspace_max_bytes']
    freeze={'protocol':'domains.alpha14.private_inputs.v0.1','visibility':'local_private','receipt_id':opaque_id(),
        'owner_admission_receipt':evidence,'sources':sources,'deep_source_receipts':deep,
        'source_selection':'At most 24, cost-ordered round robin over fixed material families; retain complete sources/axes; exclude historical admitted views and prior owner holds. No X result or Y used.',
        'deep_selection':'First eligible source per distinct family in the frozen order, at most three; no replacement after inspecting profiles.',
        'cache_participating_upper_bytes':128*1024*1024,'selected_cache_bytes':charged,
        'new_reservation_upper_bytes':upper,'pca_reference_upper':2*len(sources),'pca_stability_upper':240*len(deep),
        'geometry_protocol_sha256':digest('docs/ALPHA12_UNSUPERVISED_PROTOCOL.md'),
        'power_design_ref':{'path':'docs/benchmarks/alpha13/revised-design-freeze.json','sha256':digest('docs/benchmarks/alpha13/revised-design-freeze.json')},
        'hypotheses_sha256':digest('docs/ALPHA12_HYPOTHESIS_REGISTER.md'),
        'falsification_sha256':digest('docs/benchmarks/alpha13/falsification-contract.json'),
        'runner_sha256':digest(__file__),'target_accessed':False,'model_performance_used':False}
    atomic_json(output,{'freeze':freeze,'authentication':store.authenticate(freeze)})
    audit={'protocol':'domains.alpha14.screening.v0.2','visibility':'local_private','entries':rows,
        'counts':{'catalog_screened':len(rows),'private_screened':122,'private_authorized_entries':sum(e['access_analysis_eligible'] for e in rows if e['catalog_tier']=='private')},
        'owner_admission_receipt':evidence,'independent_study_count':None,'publication_of_new_private_participation':'not_approved',
        'source_bytes_decoded':0,'target_accessed':False}
    atomic_json(store.root/'screening-rights-reviewed.json',{'audit':audit,'authentication':store.authenticate(audit)})
    print(json.dumps({'status':'private_admission_and_execution_plan_frozen','details':'protected local root',
                      'target_accessed':False,'new_private_public_artifacts':0}))


if __name__=='__main__':main()
