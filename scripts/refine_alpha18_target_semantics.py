"""Metadata-only target validity correction; executed diagnostics remain intact."""
import copy
from alpha18_common import Context
from nirs4all_domains.storage import atomic_json,digest,fingerprint

c=Context();f=c.load('campaign-freeze.json');old=c.load('target-semantics.json')
assert not (c.root/'target-semantics-v2.json').exists()
tasks={t['task_id']:t for t in f['tasks']};records=copy.deepcopy(old['records'])
ids={'sample_number','number','individual','plant','leafnumber','leaf_number','reading','room','house_num','genotype'}
context={'easting','northing','doy','time','pot_size','temperature','tref','p_atm','li6400_measurement_temperature_degc','sample_height'}
ambiguous={'count','freeze','flash','original_extract'}
changed=[]
for r in records:
    t=tasks[r['task_id']];name=t['target'].lower();previous=copy.deepcopy(r)
    if name in ids:
        r.update(excluded=True,reason='NUMERIC_IDENTIFIER_COUNTER_OR_CATEGORY_CODE',target_evidence='numeric_identifier_or_category_code')
    elif name in ambiguous:r['target_evidence']='numeric_treatment_or_counter_meaning_unverified'
    elif name in context:r['target_evidence']='quantitative_context_or_location_diagnostic'
    elif name.endswith('_qc'):r['target_evidence']='quality_flag_or_quality_controlled_measurement_unverified'
    elif name.startswith(('modelled_','plsr_')) or 'plsr_temperature' in name:r['target_evidence']='source_model_derived_endpoint'
    if r!=previous:changed.append({'task_id':r['task_id'],'dataset_id':t['dataset_id'],'target':t['target'],'prior':previous,'current':copy.deepcopy(r)})
value={'protocol':'domains.bank_target_semantics.v0.2','parent_semantics_id':old['semantics_id'],
       'records':records,'changed':changed,'basis':'Full catalog target-name/role audit; no predictive scores or new numeric target cells used.',
       'timing':'Retrospective semantic validity correction during the raw reference campaign, prospectively applied before deeper fits. All executed diagnostic results are preserved.',
       'controller_sha256':digest(__file__)}
value['semantics_id']=fingerprint(value);c.save('target-semantics-v2.json',value)
atomic_json('docs/campaign/target-semantics-v2.json',value)
print('SEMANTICALLY_EXCLUDED',sum(r['excluded'] for r in records),'RECLASSIFIED_RECORDS',len(changed))
