"""Record the completed diverse smoke batch without changing its outcomes."""
from collections import Counter
from alpha18_common import Context,read
from nirs4all_domains.storage import atomic_json,digest

c=Context();f=c.load('reference-operational-freeze.json');names=set(f['smoke_sources'])
refs=[];values=[]
for r in c.load('reference-progress.json'):
    if not r.get('artifact_path'):continue
    v=read(r['artifact_path'])
    if v['view_id'].rsplit('/',1)[0] not in names:continue
    assert digest(r['artifact_path'])==r['artifact_sha256'];refs.append(r);values.append(v)
proof={'schema_version':1,'operational_freeze_id':f['descriptor_freeze_id'],
    'source_entries':len({v['view_id'] for v in values}),'source_target_tasks':len(values),
    'scientific_task_states':dict(Counter(v['result']['status'] for v in values)),
    'model_fit_attempts':sum(v['model_fit_attempts'] for v in values),
    'model_fit_successes':sum(v['model_fit_successes'] for v in values),
    'known_failure':'One source has nonfinite X; its 52 target descriptions remain available but no primary PLS/Ridge fit is attempted.',
    'retained_target_decoded':False,'protocol_changed_after_smoke':False,
    'role':'Executable transport/model qualification and initial scientific coverage; no accuracy-based dataset selection.'}
assert proof['source_entries']==5 and proof['model_fit_successes']==66
c.save('smoke-validation.json',proof|{'artifacts':refs})
atomic_json('docs/campaign/smoke-validation.json',proof)
print('FIVE_SOURCE_SMOKE_66_NATIVE_FITS_VERIFIED')
