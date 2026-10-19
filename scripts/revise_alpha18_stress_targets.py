"""Correct deeper target semantics before ANY structural-stress outcome."""
import copy
from alpha18_common import Context
from alpha18_target_selection import eligible_tasks
from nirs4all_domains.storage import atomic_json,digest,fingerprint

c=Context();f=c.load('campaign-freeze.json');old=c.load('stress-freeze-v2.json')
assert not (c.root/'stress-progress.json').exists() and not (c.root/'SNV-stress-progress.json').exists()
assert not (c.root/'stress-freeze-v3.json').exists()
sem={r['task_id']:r for r in c.load('target-semantics-v2.json')['records']};plans=[];changes=[]
for plan in old['plans']:
    tasks=eligible_tasks(f,plan['view_id'],sem)
    if not tasks:continue
    new=copy.deepcopy(plan);new.update(task_id=tasks[0]['task_id'],target=tasks[0]['target'])
    plans.append(new);changes.append({'view_id':plan['view_id'],'original_target':plan['target'],'revised_target':new['target']})
value={'parent_selection_id':old['freeze_id'],'plans':plans,'changes':changes,
       'semantics_id':c.load('target-semantics-v2.json')['semantics_id'],
       'target_priority_sha256':digest('scripts/alpha18_target_selection.py'),
       'selection_basis':'Same metadata-selected source/context populations, semantic chemical/physiological then morphology priority. No predictive scores or stress outcomes used.',
       'new_stress_outcomes_observed':False,'controller_sha256':digest(__file__)}
value['freeze_id']=fingerprint(value);c.save('stress-freeze-v3.json',value)
atomic_json('docs/campaign/stress-selection-v3.json',{k:v for k,v in value.items() if k!='plans'}|{'tasks':[{k:p[k] for k in ['view_id','task_id','target','factor','n_context_levels','n_declared_components']} for p in plans]})
print('SEMANTIC_STRESS_TARGET_CORRECTION',changes)
