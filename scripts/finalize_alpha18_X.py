"""Retain usable single-representation evidence before decoding any new Y."""
from pathlib import Path
from alpha18_common import Context,read
from nirs4all_domains.dependence import state
from nirs4all_domains.storage import digest,fingerprint,atomic_json
from nirs4all_domains.synthesis import describe,validate_states

c=Context();f=c.load('campaign-freeze.json');original=c.load('X-descriptor-freeze.json')
assert not (c.root/'reference-progress.json').exists()
assert not (c.root/'X-available-descriptor-freeze.json').exists()
rows=original['rows'][:];seen={(r['view_id'],r['representation']) for r in rows}
for ref in c.load('X-progress.json'):
    if not ref.get('artifact_path'):continue
    assert digest(ref['artifact_path'])==ref['artifact_sha256'];v=read(ref['artifact_path'])
    if v['result']['status']=='computed':continue
    source=next(s for s in f['sources'] if s['view_id']==v['view_id'])
    partial=v.get('partial_rows',[])
    if not partial:
        partial=[describe(v['view_id'],rep,p,state(reason='PAIRED_REPRESENTATION_INCOMPLETE'),family=source['family'],modality=source['modality']) for rep,p in v.get('partial_profiles',{}).items()]
    for r in partial:
        key=(r['view_id'],r['representation'])
        if key not in seen:rows.append(r);seen.add(key)
value={'parent_descriptor_freeze_id':original['descriptor_freeze_id'],
       'rows':rows,'target_accessed':False,'model_fits':0,
       'row_fingerprints':{r['view_id']+':'+r['representation']:fingerprint(r) for r in rows}}
value['descriptor_freeze_id']=fingerprint(value);validate_states(value)
c.save('X-available-descriptor-freeze.json',value)
atomic_json('docs/campaign/descriptor-freeze.json',{
    'descriptor_freeze_id':value['descriptor_freeze_id'],'parent_descriptor_freeze_id':original['descriptor_freeze_id'],
    'source_representation_profiles':len(rows),'target_numeric_cells_decoded':0,'model_fits':0,
    'completed_profiles_not_recomputed':True,'partial_representation_evidence_retained':True})
print('FROZEN_AVAILABLE_X_PROFILES',len(rows),'SOURCE_VIEWS',len({r['view_id'] for r in rows}))
