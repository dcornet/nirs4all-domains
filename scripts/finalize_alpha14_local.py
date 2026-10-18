"""Assemble the confidential report locally. No private values reach stdout/Git."""
from collections import Counter
import hmac
import json
from pathlib import Path
import shutil
import sys

from nirs4all_domains.privacy import PrivateStore,opaque_id,fail
from nirs4all_domains.storage import StageStore,atomic_json,digest,encoded,tree_bytes


def availability_supplement():
    """Add explicit scope/version/missingness without rewriting scientific evidence."""
    cfg=json.loads(Path('.audit/alpha14/private-root.json').read_text());store=PrivateStore(cfg['root'],Path.cwd())
    envelope=json.loads((store.root/'confidential-release-report.json').read_text());report=envelope['report']
    assert hmac.compare_digest(envelope['authentication'],store.authenticate(report))
    rows=[]
    for source in report['source_reports']:
        catalog=next(e for e in report['catalog_screening']['entries'] if e['dataset_id']==source['dataset_id'])
        rows.append({'source_receipt_id':source['source_receipt_id'],'dataset_id':source['dataset_id'],
            'source_id':source['source_id'],'catalog_content_version':catalog['content_version'],
            'catalog_descriptor_sha256':catalog['descriptor_sha256'],'executed_X_content_sha256':source['source_sha256'],
            'target':None,'split_policy':'complete-source descriptive X; no prospective evaluation scope admitted',
            'split_support':{'status':'unavailable','reason':'NO_FROZEN_ORIGINAL_KEYED_TRAIN_EVALUATION_CONTRACT','value':None},
            'metadata_agreement':{'status':'unavailable','reason':'NO_AUTHORIZED_ORIGINAL_KEYED_FACTOR_CONTRACT','value':None},
            'target_association':{'status':'unavailable','reason':'X_ONLY_SCOPE_NO_TARGET_DECODING','value':None},
            'structural_stability':{'status':'computed','reason':None,'value':source['stability_execution']}
                if source.get('stability_execution',{}).get('status')=='computed' else
                {'status':'unavailable','reason':'PRESPECIFIED_SOURCE_NOT_SELECTED_OR_REFERENCE_UNAVAILABLE','value':None},
            'supervised_pilot':{'status':'unavailable','reason':'ORIGINAL_DEPENDENCIES_TASK_AND_SEPARATE_BUDGET_NOT_ADMITTED','value':None}})
    value={'visibility':'local_private','protocol':'domains.alpha14.source_availability.v0.1',
        'parent_report_receipt':report['receipt_id'],'sources':rows,'scientific_results_changed':False}
    atomic_json(store.root/'source-availability-contract.json',{'supplement':value,'authentication':store.authenticate(value)})
    path=store.root/'CONFIDENTIAL_REPORT.md';text=path.read_text(encoding='utf-8')
    addition='\n## Explicit versions and unavailable stages\n\nSee source-availability-contract.json for the exact catalog/observed-X identity crosswalk, target-free scope and explicit split/metadata/target/pilot missingness. No original scientific value is changed.\n'
    if addition not in text:path.write_text(text+addition,encoding='utf-8')
    assert sum((store.root/p).stat().st_size for p in ['confidential-release-report.json','CONFIDENTIAL_REPORT.md','source-availability-contract.json'])+4096<=4194304
    print(json.dumps({'status':'private_scope_and_version_supplement_completed','scientific_results_changed':False}))


def main():
    cfg=json.loads(Path('.audit/alpha14/private-root.json').read_text());store=PrivateStore(cfg['root'],Path.cwd())
    policy=json.loads(Path('configs/bank/storage-policy-alpha14.json').read_text())
    approval=json.loads(Path('.audit/alpha14/budget-approval.json').read_text())
    freeze=json.loads((store.root/'execution-freeze.json').read_text())['freeze']
    inventory=json.loads((store.root/'screening-rights-reviewed.json').read_text())['audit']
    profiles=json.loads((store.root/'profile-execution.json').read_text())
    deep=json.loads((store.root/'stability-execution.json').read_text())
    diagnosis=json.loads((store.root/'failed-source-diagnosis.json').read_text())['diagnosis']
    assert len(profiles['records'])==len(freeze['sources'])
    assert {r['source_receipt_id'] for r in deep['records']}==set(freeze['deep_source_receipts'])
    # One shared metadata allocation covers atomic identity/journal replacement
    # throughout this serial campaign. These temporary bytes were not included
    # in the initial source-local scratch estimates. Retain that correction and
    # reserve conservatively within the already approved 256 MiB envelope.
    mapping=store.identities/'mapping.json';mapping_bytes=mapping.stat().st_size if mapping.exists() else 0
    journal=Path('results/alpha9-perten-keyed/state/journal.json')
    assert mapping_bytes+journal.stat().st_size<64*1024*1024
    correction={'task':{'task_id':store.authenticate(['alpha14-shared-atomic-metadata-buffer'])},
        'visibility':'local_private','protocol':'domains.alpha14.shared_metadata_budget.v0.1'}
    scheduler=StageStore(journal.parent,store.root/'metadata-scratch',store.root/'metadata-evidence',Path.cwd(),policy)
    plan={'inputs':[],'scratch_bytes':64*1024*1024,'evidence_bytes':4*1024*1024,'expected_fits':0,'expected_permutations':0,
          'uncertainty':'Conservative shared atomic mapping/journal buffer allocation. Source-local estimates originally omitted full shared rewrites; correction stays inside existing approved aggregate ceiling.'}
    from nirs4all_domains.storage import fingerprint
    before=json.loads(journal.read_text());old=before['runs'].get(fingerprint(correction)+':P0')
    if not (old and old['status']=='computed') and before['reserved_campaign_bytes']-approval['previous_campaign_reserved']+68*1024*1024>approval['new_reservation_envelope']:
        fail('PRIVATE_METADATA_RESERVATION_REQUIRES_REVIEW')
    participating=freeze['sources'][0]['other_participating_files'] if freeze['sources'] else []
    assert tree_bytes([Path.cwd(),store.root,*participating])+68*1024*1024<policy['workspace_max_bytes']
    receipt,value=scheduler.run(correction,'P0',plan,lambda folder:{'visibility':'local_private','status':'accounting_corrected',
        'shared_mapping_bytes':mapping_bytes,'shared_journal_bytes':journal.stat().st_size,'reserved_shared_buffer_bytes':64*1024*1024,
        'scientific_fits_added':0,'historical_outputs_changed':False})
    assert value is not None
    metadata_accounting=value
    rows=[];fitted=0;hdbscan=0;settings=[]
    diagnoses={r['source_receipt_id']:r for r in diagnosis['records']}
    for source in freeze['sources']:
        observed=next(r for r in profiles['records'] if r['source_receipt_id']==source['source_receipt_id'])
        name=source['admission']['source_scope'].split('/')[0]
        entry=next(e for e in inventory['entries'] if e['dataset_id']==name)
        row={'dataset_id':name,'source_id':source['source_id'],'source_receipt_id':source['source_receipt_id'],
            'dimensions':source['shape'],'family':source['canonical_source_family'],'status':observed['status'],
            'reason':observed['reason'],'admission':source['admission'],'source_sha256':source['source_sha256'],
            'original_study':entry['original_study'],'original_axis_qualification':source['original_axis_qualification'],
            'physical_reference_dependencies':entry['physical_reference_dependencies'],
            'independent_study_qualified':False,'supervised_eligibility':entry['supervised_eligibility']}
        if observed['status']=='computed':
            record=store.get(observed['receipt_id']);data=record['payload'];representations={}
            assert data['contract']['source']==source
            for rep,profile in data['representations'].items():
                representations[rep]={'pca':profile['pca'],'cluster_summaries':[
                    {k:v for k,v in s['value'].items() if k!='labels'} if s['status']=='computed' else s
                    for s in profile['cluster_settings']],
                    'neighborhood_scope':{k:v for k,v in profile['query_design'].items() if k!='ids'},
                    'full_axis_proximity':profile['neighborhoods']['value']['full_axis']['relative_proximity'],
                    'neighbor_distance_summary':profile['neighborhoods']['value']['full_axis']['normalized_nearest_summary']}
            row.update(representations=representations,representation_agreement=data['representation_agreement'],
                evidence_receipt=observed['receipt_id'],evidence_sha256=digest(store.evidence/(observed['receipt_id']+'.json')),
                finding={'observation':'Descriptive full-source raw/SNV geometry, partitions and neighborhoods computed.',
                    'confidence':'Conditional on exact declared X and qualified numerical providers; original axis/physical closure remains limited.',
                    'consequence':'May support structural-susceptibility hypotheses; no demonstrated shortcut or independent-study confirmation.',
                    'action':'Retain private evidence; resolve original identities and disclosure permissions before stronger claims.'})
            fitted+=data['new_pca_fits'];hdbscan+=data['hdbscan_attempts']
        else:
            local=diagnoses[source['source_receipt_id']];row['diagnosis']=local
            assert local['diagnosis'] in {'DECLARED_AXIS_NOT_STRICTLY_INCREASING','FULL_SOURCE_CONTAINS_NONFINITE_VALUES_NO_ROW_THINNING_ALLOWED'}
            # Under this exact executed controller both diagnoses occur before
            # stream.profile is invoked: no PCA/HDBSCAN attempt was made.
            row['pca_hdbscan_attempts']=0
            row['finding']={'observation':local['diagnosis'],'confidence':'Verified unchanged source transport diagnosis.',
                'consequence':'Complete-source protocol is unavailable for this view; not a favorable geometry result.',
                'action':local['action']}
        if source['deep_selected']:
            item=next(r for r in deep['records'] if r['source_receipt_id']==source['source_receipt_id'])
            row['stability_execution']=item
            if item['status']=='computed':
                value=json.loads(Path(item['local_path']).read_text());assert digest(item['local_path'])==item['sha256']
                row['stability']={k:value[k] for k in ['overall_classification','per_setting_classifications','parameter_ari','pca_refits','hdbscan_attempts']}
                row['stability']['conditions']={key:({'status':condition['status'],'reason':condition['reason'],'value':
                    {**condition['value'],'settings':[{**setting,'value':{k:v for k,v in setting['value'].items() if k not in ['pair_panel','planned_panel']}}
                        if setting['status']=='computed' else setting for setting in condition['value']['settings']]}}
                    if condition['status']=='computed' else condition) for key,condition in value['conditions'].items()}
                settings.extend(value['per_setting_classifications'])
        rows.append(row)
    ledger=json.loads(journal.read_text())
    delta=ledger['reserved_campaign_bytes']-approval['previous_campaign_reserved']
    assert delta<=approval['new_reservation_envelope'] and ledger['reserved_campaign_bytes']<=policy['campaign_bytes']
    files=freeze['sources'][0]['other_participating_files'] if freeze['sources'] else []
    used=tree_bytes([Path.cwd(),store.root,*files])
    # Conservative metadata-atomic peak allowance, separate from measured
    # between-stage file use; not an OS-enforced hard quota.
    peak_upper=used+mapping_bytes+journal.stat().st_size+4*1024*1024
    assert peak_upper<policy['workspace_max_bytes']
    memory={'status':'unavailable','reason':'NO_WORKER_OR_NATIVE_PEAK_OBSERVER_ATTACHED; DO_NOT_SUBSTITUTE_LAUNCHER_PEAK','value':None}
    report={'protocol':'domains.alpha14.confidential_release.v0.1','visibility':'local_private','receipt_id':opaque_id(),
        'all_164_entries_screened':len(inventory['entries'])==164,'private_source_data_in_public_repository':False,
        'catalog_screening':inventory,'source_reports':rows,
        'counts':{'catalog':164,'public_catalog':42,'private_catalog':122,
            'private_local_analysis_qualified_entries':sum(e['access_analysis_eligible'] for e in inventory['entries'] if e['catalog_tier']=='private'),
            'selected_new_source_views':len(rows),'completed_new_source_views':sum(r['status']=='computed' for r in rows),
            'failed_new_source_views':sum(r['status']!='computed' for r in rows),
            'reference_PCA_fits':fitted,'reference_HDBSCAN_attempts':hdbscan,
            'stability_PCA_refits':sum(r.get('pca_refits',0) for r in deep['records']),
            'stability_HDBSCAN_attempts':sum(r.get('hdbscan_attempts',0) for r in deep['records']),
            'stability_setting_classifications':dict(Counter(settings)),
            'independent_confirmation_studies':0,'new_supervised_fits':0,'private_publication_approved':0},
        'hypotheses':'Frozen H1-H5; no new Y, supervised association or generalization response used.',
        'identity_maps_separate':str(store.identities),'secrets_separate':str(store.keys),
        'source_provenance':{'input_freeze_sha256':digest(store.root/'execution-freeze.json'),
            'profile_controller_runtime':profiles['runtime'],'stability_controller_runtime':deep['runtime'],
            'executed_diagnostic_source_archive':str(store.root/'source-archive/before-metadata-correction-diagnose_alpha14_private.py')},
        'resource_use':{'policy':policy,'campaign_reserved_bytes':ledger['reserved_campaign_bytes'],'new_reserved_bytes':delta,
            'combined_measured_bytes':used,'combined_with_metadata_atomic_upper_bytes':peak_upper,
            'protected_evidence_root_bytes':tree_bytes([store.root]),'shared_mapping_bytes':mapping_bytes,
            'C_free_bytes':shutil.disk_usage('C:/').free,'D_free_bytes':shutil.disk_usage('D:/').free,
            'profile_invocation_wall_seconds':profiles['wall_seconds_this_invocation'],'stability_invocation_wall_seconds':deep['wall_seconds'],
            'peak_memory':memory,'source_matrix_copies':0,'shared_metadata_cost_correction':metadata_accounting,
            'measurement_scope':'After scientific execution, before final versioned tooling/package/CI growth; final storage proof is separate.',
            'historical_deletion_or_migration':False},
        'limitations':['Private tier, source views and package citations do not establish independent studies.',
            'Unknown physical/reference/assay closure remains explicit; observation-conditional stability is not biological uncertainty.',
            'Missing complete-source axes/finite values block the frozen protocol; no row thinning or imputation.',
            'No publication of private participation, fingerprints, IDs, source dimensions, per-sample evidence or numerical synthesis is authorized.',
            'No causal shortcut percentage, universal score, differential privacy or anonymity guarantee.']}
    lines=['# CONFIDENTIAL — alpha.14 local scientific report','',
        'Do not publish this file. Full machine-readable evidence: confidential-release-report.json.',
        '', '## Exact local denominators', '', '```json',json.dumps(report['counts'],indent=2),'```','',
        '## Scientific and rights decisions','',
        'All 164 screening records, individual source admissions, original identities, source hashes, geometric findings and study limitations are in the authenticated JSON report.',
        'Mappings and keys are separately protected. No target cells were decoded. No supervised pilot was admitted.','',
        '## Source outcomes','']
    for row in rows:
        lines.extend([f"- {row['dataset_id']} / {row['source_id']}: {row['status']}; "+str(row.get('reason'))])
    lines.extend(['','## Resource use','','```json',json.dumps(report['resource_use'],indent=2),'```','',
        '## Limits','',*('- '+v for v in report['limitations']),''])
    envelope={'report':report,'authentication':store.authenticate(report)}
    markdown='\n'.join(lines)
    assert len(encoded(envelope))+len(markdown.encode('utf-8'))+len(encoded(metadata_accounting))+4096<=policy['evidence_bytes']
    atomic_json(store.root/'confidential-release-report.json',envelope,max_bytes=policy['evidence_bytes'])
    (store.root/'CONFIDENTIAL_REPORT.md').write_text(markdown,encoding='utf-8')
    # This receipt reveals no private source identity, source count or metric.
    atomic_json('.audit/alpha14/local-report-receipt.json',{'receipt_id':report['receipt_id'],
        'status':'verified_local_only','public_private_scientific_exports':0})
    print(json.dumps({'status':'confidential_local_report_completed','public_private_scientific_exports':0}))


if __name__=='__main__':
    try:
        if sys.argv[1:]==['--availability-supplement']:availability_supplement()
        else:main()
    except Exception:
        print(json.dumps({'status':'refused','reason':'CONFIDENTIAL_REPORT_VALIDATION_FAILED'}));raise SystemExit(2)
