"""Bind all five prespecified stress tasks to the raw/SNV factorial contrast."""
from alpha18_common import Context
from nirs4all_domains.storage import digest,fingerprint,atomic_json

c=Context();assert not (c.root/'stress-progress.json').exists() and not (c.root/'SNV-stress-progress.json').exists()
assert not (c.root/'SNV-stress-extension-freeze.json').exists()
old=c.load('reference-operational-freeze.json')
assert digest('.audit/alpha18-stress-controller-raw-first.py')==old['controllers']['scripts/run_alpha18_stress.py']
selection=c.load('stress-freeze-v2.json');assert len(selection['plans'])==5
value={'protocol':'domains.bank_stress_snv.v0.1','selection_id':selection['freeze_id'],
       'task_ids':[p['task_id'] for p in selection['plans']],
       'controller_sha256':digest('scripts/run_alpha18_stress.py'),
       'prior_raw_controller_sha256':digest('.audit/alpha18-stress-controller-raw-first.py'),
       'plan_sha256':digest('docs/ALPHA18_SNV_STRESS_PLAN.md'),
       'additional_model_fits_upper':30,'additional_diagnostic_PCA_upper':15,'additional_reservation_bytes':5242880,
       'ceiling_increase_bytes':0,'new_stress_outcomes_observed':False,
       'selection_changed_using_model_scores':False}
value['extension_id']=fingerprint(value);c.save('SNV-stress-extension-freeze.json',value)
atomic_json('docs/campaign/SNV-stress-extension-freeze.json',value);print('FIVE_TASK_SNV_STRESS_EXTENSION_FROZEN_BEFORE_STRESS_OUTCOMES')
