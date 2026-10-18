"""Pinned metadata/stat-only screening. Full details stay outside Git.

No target/metadata cell or spectral file is opened. Catalog governance is a lead,
not source authorization. Run again with a distinct audit name when evidence
changes; this does not retroactively rewrite an earlier decision.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import yaml

from nirs4all_domains.privacy import PrivateStore, opaque_id
from nirs4all_domains.storage import atomic_json, digest, fingerprint


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private-config',type=Path,required=True)
    parser.add_argument('--audit-name',default='screening-initial')
    args=parser.parse_args()
    if args.audit_name not in {'screening-initial','screening-rights-reviewed'}:
        raise ValueError('OPAQUE_AUDIT_NAME_REQUIRED')
    config=json.loads(args.private_config.read_text(encoding='utf-8'))
    store=PrivateStore(config['root'],Path.cwd())
    destination=store.root/(args.audit_name+'.json')
    if destination.exists():raise ValueError('IMMUTABLE_SCREENING_EXISTS')
    inventory_path=Path('docs/benchmarks/alpha13/source-diversity-inventory.json')
    inventory=json.loads(inventory_path.read_text(encoding='utf-8'))
    assert len(inventory['entries'])==164
    old=json.loads(Path('docs/benchmarks/alpha13/source-admissions.json').read_text())
    admitted={a['specification']['dataset_id']:a for a in old['admissions']}
    source_root=Path(config['source_root'])
    rows=[]
    for entry in inventory['entries']:
        name=entry['dataset_id'];descriptor=Path('.audit/datasets/catalog/datasets')/(name+'.yaml')
        if digest(descriptor)!=entry['descriptor_sha256_observed']:
            raise ValueError('PINNED_DESCRIPTOR_CHANGED')
        metadata=yaml.safe_load(descriptor.read_text(encoding='utf-8'))
        receipt=opaque_id()
        rights={k:{'status':'unknown','evidence_receipts':[]} for k in
                ['access','analysis','publish_aggregates','redistribute_raw']}
        reasons=['ORIGINAL_SOURCE_PERMISSION_NOT_VERIFIED']
        old_evidence=None
        if name in admitted:
            old_evidence={'path':'docs/benchmarks/alpha13/source-admissions.json',
                          'sha256':digest('docs/benchmarks/alpha13/source-admissions.json'),
                          'admission_id':admitted[name]['admission_id']}
            spec=admitted[name]['specification']
            for key,old_key in [('access','access'),('analysis','local_analysis'),
                                ('publish_aggregates','publish_statistics'),('redistribute_raw','redistribute_raw')]:
                rights[key]={'status':spec['permissions'][old_key]['status'],
                             'evidence_receipts':[receipt] if spec['permissions'][old_key]['evidence'] else []}
            reasons=[]
        elif entry['catalog_tier']=='public' and entry['rights'].get('status')=='computed':
            # Historical public authorization remains scoped to its exact view.
            old_evidence=entry['rights']
            for key in ['access','analysis','publish_aggregates']:
                rights[key]={'status':'allowed','evidence_receipts':[receipt]}
            reasons=[]
        if name=='corn_eigenvector_nir':
            reasons=['OWNER_DECISION_RETAINS_PENDING_RIGHTS'];rights={k:{'status':'requires_owner_approval','evidence_receipts':[]} for k in rights}
        sources=[]
        for source in entry['sources']:
            path=source_root/name/(source['source_id']+'.csv')
            sources.append({'source_id':source['source_id'],'dimensions':source,
                'matrix_availability':{'exists':path.is_file(),'bytes':path.stat().st_size if path.is_file() else None,
                                       'locator':str(path),'source_bytes_opened':False},
                'modality_eligible':source['reviewed_modality'] in ['NIR','VIS-NIR','VIS_NIR','reflectance_nirs'],
                'geometry_work_qualified':source['n_observations']*source['n_variables']<=10000000 and
                    source['pca_full_population_work']<=250000000 and
                    source['n_variables']**2*min(20,source['n_observations']-1,source['n_variables'])<=250000000,
                'cost':{'existing_cache_bytes':path.stat().st_size if path.is_file() else None,
                        'new_source_bytes':None,'persistent_evidence_upper_bytes':1048576,
                        'source_scratch_upper_bytes':8192,'pca_fits_for_raw_snv':2,'hdbscan_attempts':4}})
        previous_public=old_evidence is not None
        rows.append({'receipt_id':receipt,'dataset_id':name,'catalog_tier':entry['catalog_tier'],
            'content_version':entry['catalog_content_version'],'descriptor_sha256':digest(descriptor),
            'original_study':{'citation':metadata.get('citation'),'publications':metadata.get('publications',[]),
                'identity_verified':False,'independent_population_verified':False},
            'source_origins':entry['original_source_locators'],'family':entry['family'],'sources':sources,
            'permissions':rights,'permission_basis':old_evidence,'catalog_governance_not_authorization':metadata.get('governance',{}),
            'admission_tier':'A' if previous_public and not reasons else 'C',
            'access_analysis_eligible':not reasons,'reasons':reasons,
            'confidentiality':{'status':'source_specific_review_required' if not previous_public else 'historical_public_scope_only',
                'contractual_restrictions':'unknown' if not previous_public else 'prior_admitted_scope',
                'human_or_sensitive_restrictions':'unknown' if not previous_public else 'prior_admitted_scope',
                'participation_disclosure':'not_approved' if not previous_public else 'already_public'},
            'overlap':{'status':'not_identifiable','reason':'VIEW_PACKAGE_OR_SAME_MODALITY_DOES_NOT_ESTABLISH_INDEPENDENCE',
                       'value':None},
            'physical_reference_dependencies':{'status':'unavailable','reason':'NO_NEW_ORIGINAL_KEY_CLOSURE_AUDIT','value':None},
            'supervised_eligibility':{'status':'unavailable','reason':'RIGHTS_DEPENDENCY_TASK_AND_BUDGET_GATES_REQUIRED','value':None},
            'prior_characterization':'historical_evidence_only' if previous_public else 'not_newly_executed',
            'target_accessed':False,'model_performance_used':False})
    private=[e for e in rows if e['catalog_tier']=='private']
    assert len(private)==122
    result={'protocol':'domains.alpha14.screening.v0.1','visibility':'local_private',
        'receipt_id':opaque_id(),'baseline':'dd4496718f449cd8d02839fa7b33ac155fbbcccb',
        'pinned_inventory_sha256':digest(inventory_path),'catalog_revision':inventory['catalog_revision'],
        'entries':rows,'denominators':{'screened_catalog_entries':len(rows),'screened_private_entries':len(private),
            'rights_eligible_private_entries':sum(e['access_analysis_eligible'] for e in private),
            'newly_executed_private_sources':0,'new_private_publication_approved':0},
        'private_tiers':dict(Counter(e['admission_tier'] for e in private)),
        'source_bytes_accessed':0,'target_accessed':False,'new_scientific_fits':0,
        'script_sha256':digest(__file__)}
    atomic_json(destination,{'audit':result,'authentication':store.authenticate(result)})
    print(json.dumps({'screened_catalog_entries':len(rows),'screened_private_catalog_entries':len(private),
                      'detailed_report':'protected local evidence root','source_bytes_accessed':0,'public_export_created':False}))


if __name__=='__main__':main()
