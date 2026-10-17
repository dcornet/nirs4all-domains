"""No-fit registry/suite/coverage publication over already frozen scientific records."""
from collections import Counter
import json
import os
from pathlib import Path

from nirs4all_domains.adaptive import coverage_record
from nirs4all_domains.bank import schema_check
from nirs4all_domains.dependence import state
from nirs4all_domains.registry import evidence, execution_contract, freeze_suite, task_identity, verify_evidence
from nirs4all_domains.storage import StageStore, atomic_json, digest, fingerprint

ROOT=Path('docs/benchmarks/alpha11');AUDIT=Path('.audit/alpha11')


def ref(path):
    p=Path(path);return {'path':p.as_posix(),'sha256':digest(p)}


def main():
    admission=json.loads((ROOT/'litter-admission.json').read_text());frozen=json.loads((ROOT/'litter-evaluation.json').read_text())
    models=json.loads((ROOT/'litter-model-results.json').read_text());geometry=json.loads((ROOT/'litter-geometry.json').read_text())
    audit=json.loads((ROOT/'litter-original-audit.json').read_text());crop=json.loads((ROOT/'crop-association.json').read_text())
    shortlist={'protocol':'domains.alpha11.source_review.v0.1','selection_basis':'material/source/identity contrast before alpha11 model scores',
        'admitted_source':{'dataset_id':admission['specification']['dataset_id'],'admission_id':admission['admission_id'],
            'physical_unit':'keyed 1.5-3g litter sample, possibly multiple leaves; upstream averaged spectrum',
            'source_study':'Kothari/Hobbie/Cavender-Bares, FAB1 2018 and Minneapolis; published 2024',
            'rights':'Official EcoSIS cc-by; attribution recorded in admission','independence':'31 declared plot/context blocks; GEN provenance and assay batches unresolved',
            'outcome':'Conditional grouped model and paired-preparation challenge; not a certificate of independent biological transfer'},
        'crop_source':{'dataset_id':'ecosis_leaf_spectra_structural_and_biochemical_leaf_traits_of_reflectance_nirs',
            'study':'Ely et al. 2019, 10.1093/jxb/erz061; original 184 spectral leaves and 187 trait records',
            'rights':'Official EcoSIS odc-by; original keyed CSVs verified through Datasets cache',
            'outcome':'X-only and keyed descriptive nitrogen association; no model admission without leaf-to-plant/assay maps'},
        'garrett':{'source':'10.6084/m9.figshare.20506587.v2','rights':'Official Figshare CC BY 4.0',
            'outcome':'pending','reason':'Original source describes MIR; catalog candidate says VISNIR. Exact OSSL/source modality and sample correspondence unverified.',
            'requested_evidence':'OSSL ID_sample to original trial/site/profile/horizon/lab IDs, exact spectral archive and axis, and modality provenance'},
        'historical_sources':{'cartilage':'Original 869 locations/2605 spectra/44 regions/5 joints preserved; donor and assay maps pending, no model fit',
            'corn':'Owner explicitly keeps pending; missing rights justification and original specimen/assay keys',
            'shootout':'Original 655 versus announced 654, empty original row keys; no invented converter error',
            'ucph':'Batch/replicate codes do not establish paired specimen/assay identity'},
        'additional_source_findings':{'litter_missing_ground':'Publication Table 1 explicitly identifies one birch sample omitted for lack of tissue; original key GEN_1_BEPA_7 is retained in intact task',
            'litter_date':'Harvest 2018 per original publication; catalog year 2024 is not assumed to be acquisition year',
            'malaria':'DataCite points to custom dataset terms; original custom-license endpoint returns 403. CC-BY label in local card alone is insufficient.',
            'chembl':'Figshare spectra CC BY 4.0, ChEMBL metadata ShareAlike scope unresolved; full source exceeds dimensional budget and is simulated molecular IR/Raman'},
        'source_evidence':[ref(p) for p in sorted((AUDIT/'source').glob('*.json'))],
        'publication':{'complete':ref(AUDIT/'source/litter-publication-complete.pdf'),'complete_bytes':1494462,
            'initial_partial_bytes_preserved':1048576,'source':'https://shankothari.github.io/Documents/Kotharietal2024CJFR.pdf'},
        'external_messages_sent':0,'upstream_changes':0}
    shortlist['source_isolation_correction_ref']=ref(ROOT/'source-isolation.json')
    shortlist['higher_stage_scope']='Other available target tables remain pending original-key/unit/reference admission; unavailable XY is not evidence of absent Y or weak structural association.'
    shortlist['transport_campaign_namespace']='Frozen litter-2024 is the source-edition transport namespace, not an independently observed acquisition year; collection is 2018.'
    atomic_json(ROOT/'source-review.json',shortlist)
    summaries={name:[{'design_id':d['value']['design_id'],
                **{k:d['value'][k]['value']['rmse']['value'] for k in ['scores','null_scores','transfer_scores','transfer_matched_reference_scores']}}
                    for d in result['designs']] for name,result in models['models'].items()}
    records=[]
    policy=json.loads(Path('configs/bank/storage-policy-alpha11.json').read_text())
    store=StageStore('results/alpha9-perten-keyed/state',AUDIT/'scratch',AUDIT/'evidence',Path.cwd(),policy)
    for transfer in [False,True]:
        spec={'dataset_id':admission['specification']['dataset_id'],'content_version':admission['specification']['content_version'],
            'dataset_revision':fingerprint(admission['specification']['source_hashes']),'source_id':'intact_to_ground' if transfer else 'intact',
            'target_id':'Nmass','representation':'singleton original source-averaged spectra; keyed paired preparation' if transfer else 'technical_mean (singleton original source-averaged spectrum)',
            'split_protocol':'sealed_plot17; grouped_refits17_31_47; new-object preparation transfer' if transfer else 'sealed_plot17; grouped_refits17_31_47',
            'independence_policy':'declared plot/individual/logical-reference closure; GEN and MPLS conservative blocks; higher biology unverified',
            'qualification_protocol':'domains.repeated_design.v0.1'}
        task=task_identity(spec)
        source_files=['bridges/python/nirs4all_domains/'+n+'.py' for n in ['repeated','multifamily','predictive','dependence']]
        execution={'input_sha256':frozen['development_sha256'],'source_content_sha256':fingerprint(admission['specification']['source_hashes']),
            'split_folds_sha256':fingerprint(frozen['designs']),'dependency_policy':spec['independence_policy'],
            'preprocessing':'inner/outer train-only native centering or SNV; no held-out fit','models':frozen['specifications'],
            'protocol':spec['qualification_protocol'],'binaries':{'methods':'096bae41ffc5e4f6ec8d73b0ca43f0cec83f66dda806b2d43b2d893ba07db164'},
            'providers':{'Methods':'1.3.6 ABI2.19','DAG-ML':'0.3.41','Datasets':'0.3.11'},
            'settings':{'evaluation_id':frozen['evaluation_id'],'transfer_hash':frozen['transfer_hash'],'n_development':298,
                'n_paired_evaluation':297 if transfer else None,'pre_score_admission_id':admission['admission_id']},
            'controller_sha256':fingerprint({p:digest(p) for p in source_files})}
        scientific={'task_properties':{'physical_samples':322,'development_samples':298,'retained_samples':24,'n_declared_development_blocks':24,
                'verified_independent_higher_group_count':state(reason='GEN_COLLECTION_AND_ASSAY_LINKS_NOT_IDENTIFIED'),
                'meaningful_target':admission['specification']['target'],'source_axis_bands':2001,'matched_transfer_evaluation':297 if transfer else None},
            'model_response':{'results_ref':ref(ROOT/'litter-model-results.json'),'per_design_rmse':summaries,
                'variation_scope':'Three overlapping fully refitted grouped designs; descriptive sensitivity, not independent replicates or a calibrated new-group distribution'},
            'benchmark_suitability':{'purpose':'paired preparation transfer on held-out physical samples' if transfer else 'conditional within-population estimator comparison',
                'low_dependence':state(reason='STRONG_SPECIES_ASSOCIATION_AND_UNRESOLVED_HIGHER_DEPENDENCIES'),
                'new_biological_population_generalization':state(reason='SOURCE_POPULATION_AND_ASSAY_SUPPORT_INSUFFICIENT')},
            'geometry_ref':ref(ROOT/'litter-geometry.json'),'controls_ref':ref(ROOT/'litter-controls.json'),
            'source_isolation_correction_ref':ref(ROOT/'source-isolation.json'),
            'test_target_accessed':False}
        qualifications={'identity':state(True),'xy_signal':state(True),'independent_support':state(reason='HIGHER_COLLECTION_ASSAY_DEPENDENCIES_UNRESOLVED'),
            'structural_stress':state(True),'reviewed_low_dependence_candidate':state(reason='NOT_ADMITTED')}
        purposes=['transfer_challenge'] if transfer else ['within_population_estimator_comparison','structure_sensitive_challenge']
        result=evidence(task,execution_contract(task,execution),scientific,qualifications,purposes,
            ['Exploratory source/sample-conditional evidence; physical sample bags do not establish independent donor/tree/assay populations.',
             'GEN is 193 observations in one conservative block and can dominate sample-weighted errors; no generalization distribution over unseen biological groups is identified.',
             'Paired preparations are the same population; neither two independent studies nor calibrated instrument transfer.'])
        schema_check(result,'qualification-evidence')
        contract={'task':{'task_id':fingerprint([admission['admission_id'],'domains.repeated_design.v0.1'])},
            'protocol':'domains.alpha11.registry_publish.v0.1','evidence_id':result['evidence_id'],'runner_sha256':digest(__file__)}
        plan={'inputs':[],'scratch_bytes':4096,'evidence_bytes':65536,'expected_fits':0,'expected_permutations':0,
              'uncertainty':'Deterministic validated compact P4 registry publication, no acquisition or numerical fitting.'}
        receipt,published=store.run(contract,'P4',plan,lambda folder:result,lambda value:(verify_evidence(value),schema_check(value,'qualification-evidence')))
        if published!=result:raise ValueError('P4_REGISTRY_PUBLICATION_FAILED:'+str(receipt))
        records.append(published)
        destination=ROOT/('litter-transfer-evidence.json' if transfer else 'litter-evidence.json')
        source=AUDIT/'evidence'/receipt['artifact'];temp=destination.with_suffix('.shared')
        os.link(source,temp);os.replace(temp,destination)
    old_perten=json.loads(Path('docs/benchmarks/alpha10/perten-evidence.json').read_text())
    old_ecosis=json.loads(Path('docs/benchmarks/alpha8/ecosis-evidence.json').read_text())
    for purpose,name in [('within_population_estimator_comparison','within-population'),('structure_sensitive_challenge','structure-challenge'),
                         ('transfer_challenge','transfer'),('candidate_low_structural_dependence','low-dependence-candidate')]:
        suite=freeze_suite([old_perten,old_ecosis,*records],purpose,{'metrics':'task-wise native RMSE/MAE/R2 in original units; no cross-target RMSE aggregation',
            'uncertainty':'separate conditional OOF resampling and repeated fitted-design sensitivity; intended purpose is not an independence certificate'})
        schema_check(suite,'benchmark-suite');atomic_json(ROOT/(name+'-suite.json'),suite)
    entries=[];native=[]
    for p in sorted((ROOT/'public').glob('*.json')):
        old=json.loads(p.read_text());levels=old['levels'].copy();profile=old['structural_susceptibility'];name=old['dataset_id']
        profile_ref=ref(p)
        if name.startswith('ecosis_tabletop'):
            follow=json.loads((ROOT/'pddl-followup.json').read_text());profile=follow['report'];profile_ref=ref(ROOT/'pddl-followup.json')
            levels['X0']=state({'ref':profile_ref,'reason':'PDDL source license separately audited'})
        meta_path=ROOT/'metadata'/(name+'.json');meta=json.loads(meta_path.read_text()) if meta_path.exists() else None
        identity=old['identity_evidence'];independence={'physical':'declared source/sample identity, unverified original ownership',
            'higher_groups':state(reason='ORIGINAL_BIOLOGICAL_AND_ASSAY_DEPENDENCIES_NOT_QUALIFIED')}
        if name==admission['specification']['dataset_id']:
            identity='verified_physical_identity';independence['physical']='322 original composite litter sample IDs; 31 declared plot/context blocks'
            levels.update(X1=state(ref(ROOT/'litter-geometry.json')),XY=state(ref(ROOT/'litter-geometry.json')),
                XYM=state(ref(ROOT/'litter-controls.json')),MODEL=state({'ref':ref(ROOT/'litter-model-results.json'),'scope':'conditional declared-block designs; independently calibrated biological uncertainty unavailable'}))
        elif name=='ecosis_leaf_spectra_structural_and_biochemical_leaf_traits_of_reflectance_nirs':
            identity='verified_physical_identity';independence['physical']='184 original leaf IDs, leaf-to-plant ownership unresolved'
            levels.update(XY=state(ref(ROOT/'crop-association.json')),XYM=state(ref(ROOT/'crop-association.json')))
        elif name.startswith('ecosis_freeze_dried'):
            identity='verified_physical_identity';independence['physical']='Historical original keyed CA2023 sample/plot policy; reference precision unresolved'
            levels.update(X1=state(ref('docs/benchmarks/alpha8/ecosis-evidence.json')),XYM=state(ref('docs/benchmarks/alpha8/ecosis-evidence.json')),
                          MODEL=state({'ref':ref('docs/benchmarks/alpha8/ecosis-evidence.json'),'reuse':'historical, no new fit'}))
        elif name.startswith('cartilage_'):
            identity='verified_physical_identity';independence['physical']='869 verified original locations, 2605 spectra; donor count unknown'
        metadata_status=state({'ref':ref(meta_path),'fields':len(meta.get('fields',{}))}) if meta and meta.get('fields') else state(reason='NO_QUALIFIED_MULTILEVEL_METADATA_AGREEMENT_PROFILE')
        if profile:native.append(profile)
        value=coverage_record(name,old['source_id'],identity,levels,None,profile_ref=profile_ref,target=old['target'],
            metadata_factor_status=metadata_status,independent_unit_evidence=independence,
            computational_cost=old['computational_cost'],model_provider_scope='Methods 1.3.6 / DAG-ML0.3.41 only for admitted MODEL cases',
            source_dimensions=old['source_dimensions'],source_record_id=old['record_id'])
        schema_check(value,'adaptive-coverage');entries.append(value)
    coverage={'protocol':'domains.adaptive_structure.v0.1','catalog_revision':'e68d1befb6cb8245799e83d4b4e4c41e66287689','n_public_catalog_entries':42,
        'counts':{level:dict(Counter(r['levels'][level]['status'] for r in entries)) for level in ['X0','X1','XY','XYM','MODEL']},
        'metadata_profiles':sum(r['metadata_factor_status']['status']=='computed' for r in entries),
        'identity_states':dict(Counter(r['identity_evidence'] for r in entries)),'entries':entries,
        'raw_neighborhood_evaluable_entries':sum(p['near_duplicate_proximity']['status']=='computed' for p in native),
        'raw_neighborhood_entries_with_proximity_at_1e_minus6':sum(p['near_duplicate_proximity']['status']=='computed' and p['near_duplicate_proximity']['value']['tolerance_sensitivity'][2]['n_observations_with_close_neighbor']>0 for p in native),
        'primary_cluster_count_distribution':dict(Counter(str(p['cluster_settings'][0]['value']['n_clusters']) for p in native if p['cluster_settings'][0]['status']=='computed')),
        'x0_elapsed_seconds_sum':sum(p.get('elapsed_seconds',0) for p in native),
        'denominator_scope':'Catalog entry descriptions, not independent studies; preparations/targets/revisions can share objects. No population prevalence is estimated.',
        'all_source_variants_note':'ChEMBL has additional simulated IR/Raman source dimensions; neither qualifies under the full-population dimensional budget.',
        'study_overlap_limits':['CA2023 fresh/freeze/oven views share populations.','CABO versions/absorbance/transmittance and herbarium fresh/pressed/ground views can share specimens.',
            'Alberta leaf/canopy, NASA reflectance/transmittance and Puerto Rico modalities must not count as independent populations.','An original EcoSIS package or a different DOI does not prove independent scientific sampling.'],
        'new_source_review_ref':ref(ROOT/'source-review.json')}
    atomic_json(ROOT/'public-coverage.json',coverage)
    lines=['# Public campaign coverage','',coverage['denominator_scope'],'','| Dataset | X0 | X1 | XY | XYM | MODEL |','|---|---|---|---|---|---|']
    lines.extend('| '+r['dataset_id']+' | '+' | '.join(r['levels'][k]['status'] for k in ['X0','X1','XY','XYM','MODEL'])+' |' for r in entries)
    lines+=['','Exact reasons, source dimensions, identities, providers, measured execution times and content hashes are in [public-coverage.json](public-coverage.json).',
            'Metadata agreement profiles are separate from verified explanatory-factor semantics. HDBSCAN parameter agreement is not resampling stability.']
    (ROOT/'COVERAGE.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    plan={'protocol':'domains.tabpfn.future_selection.v0.1','provider':'nirs4all 1.4.10 TabPFNNIRSRegressor','wrapper_source_sha256':digest(AUDIT/'source/tabpfn_nirs.py'),
        'source_revision':'1aefd473a0ebeef28adc0d808c4a4b0c9c45fa9f','tabpfn_installed':False,'tabpfn_fitted':False,'checkpoint_acquired':False,
        'selection_rule':'Purpose/identity/evidence gates frozen before any TabPFN predictions; no score-based replacement',
        'categories':[{'purpose':'structure_sensitive_challenge','status':'selected','task_id':old_perten['task_id'],'evidence_id':old_perten['evidence_id']},
            {'purpose':'candidate_low_structural_dependence','status':'pending','reason':'No task passes independent support, effective stress and estimator-family robustness gates'},
            {'purpose':'transfer_challenge','status':'pending','candidate_task_id':records[1]['task_id'],'reason':'Litter paired preparation is executable; higher collection/assay independence and deployment scope need further qualification'},
            {'purpose':'controlled_synthetic_mechanism','status':'selected','fixture_sha256':digest('tests/fixtures/dependence/mixed.json'),'domain':'synthetic; never a real-data bank member'}],
        'execution_gates':['Pin exact TabPFN package and checkpoint digest/version, weight license acceptance and publication/deployment scope.',
            'Replace unversioned auto checkpoint; audit ignore_pretraining_limits, sample/feature applicability and device feasibility.',
            'Fresh SG -> supervised OSC -> fixed feature cap -> centering -> TabPFN inside each inner train and outer refit; never full-data OSC.',
            'Frozen n_estimators=16 and seed0 from wrapper, max_features2000 is a wrapper setting, not yet a locally qualified model hard limit.',
            'Review GPU/CPU, RAM/disk/time and group-safe resource counts before installation, weights or fitting.'],
        'scientific_assumption':'No prior claim that foundation models are more or less shortcut-sensitive than classical/adaptive estimators.'}
    plan['suite_id']=fingerprint(plan);atomic_json(ROOT/'tabpfn-future-suite.json',plan)
    print(json.dumps({'counts':coverage['counts'],'metadata_profiles':coverage['metadata_profiles'],'new_task_ids':[r['task_id'] for r in records],
        'raw_proximity_evaluable':coverage['raw_neighborhood_evaluable_entries'],'raw_close':coverage['raw_neighborhood_entries_with_proximity_at_1e_minus6']}))


if __name__=='__main__':main()
