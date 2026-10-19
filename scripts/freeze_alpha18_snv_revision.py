"""Bind semantic-corrected stress targets and known plot protection before fits."""
from alpha18_common import Context
from nirs4all_domains.storage import digest,fingerprint,atomic_json

c=Context();assert not (c.root/'stress-progress.json').exists() and not (c.root/'SNV-stress-progress.json').exists()
old=c.load('SNV-stress-extension-freeze.json');selection=c.load('stress-freeze-v3.json')
v={**old,'parent_extension_id':old['extension_id'],'controller_sha256':digest('scripts/run_alpha18_stress.py'),
   'selection_id':selection['freeze_id'],'task_ids':[p['task_id'] for p in selection['plans']],
   'declared_plot_freeze_id':c.load('group-sensitivity-freeze-v2.json')['freeze_id'],
   'reason':'Numeric-code/context targets were corrected from metadata before any stress model outcome; all prior unexecuted freezes are retained. Plot links preserve known experimental context.',
   'new_stress_outcomes_observed':False}
v.pop('extension_id');v['extension_id']=fingerprint(v);c.save('SNV-stress-extension-freeze-v2.json',v)
atomic_json('docs/campaign/SNV-stress-extension-freeze-v2.json',v)
print('SEMANTIC_CORRECTED_RAW_SNV_STRESS_FREEZE_BOUND')
