"""Bind the qualified explicit-fold seam after primary execution has ended."""
from alpha18_common import Context
from nirs4all_domains.storage import digest,fingerprint,atomic_json
from pathlib import Path

c=Context();f=c.load('campaign-freeze.json')
assert len(c.load('reference-worker-observations.json'))==71
original_hashes={Path(k).as_posix():v for k,v in f['controller_sha256'].items()}
assert digest('.audit/alpha18-full-bank-primary-first.py')==original_hashes['bridges/python/nirs4all_domains/full_bank.py']
v={'protocol':'domains.bank_declared_plot_sensitivity.v0.1',
   'primary_core_sha256':digest('.audit/alpha18-full-bank-primary-first.py'),
   'current_core_sha256':digest('bridges/python/nirs4all_domains/full_bank.py'),
   'plan_sha256':digest('docs/ALPHA18_GROUP_SENSITIVITY_PLAN.md'),
   'selection_id':c.load('group-sensitivity-freeze-v2.json')['freeze_id'],
   'targeted_qualification':'Six focused tests pass, including explicit two-fold native execution, split-component rejection and singleton R2 unavailable with finite RMSE.',
   'primary_source_archived':True,'completed_primary_results_changed':False,
   'new_native_solver_or_kernel':False,'default_reference_design_unchanged':True,
   'singleton_scoring_guard_corrected':True}
v['continuation_id']=fingerprint(v);c.save('group-explicit-fold-code-continuation.json',v)
atomic_json('docs/campaign/group-explicit-fold-code-continuation.json',v)
print('EXPLICIT_FOLD_NATIVE_TRANSPORT_QUALIFIED_AND_BOUND')
