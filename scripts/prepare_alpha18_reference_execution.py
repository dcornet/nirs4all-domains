"""Bind the operational reference controller after X-only evidence is complete."""
from pathlib import Path
from importlib.metadata import version
from alpha18_common import Context
from nirs4all_domains.storage import digest,atomic_json

c=Context();assert not (c.root/'reference-progress.json').exists()
descriptors=c.load('X-available-descriptor-freeze.json');scope=c.load('scope-marker-continuation.json');sem=c.load('target-semantics.json')
retained=c.load('historical-retained-continuation.json')
from n4m._ffi import library_path
assert version('nirs4all-methods')=='1.3.6' and version('dag-ml')=='0.3.41'
library_sha=digest(library_path());assert library_sha=='096bae41ffc5e4f6ec8d73b0ca43f0cec83f66dda806b2d43b2d893ba07db164'
paths=['scripts/run_alpha18_campaign.py','scripts/alpha18_worker_entry.py','scripts/alpha18_common.py','scripts/run_alpha18_stress.py','docs/ALPHA18_STRESS_ESTIMANDS.md']
value={'descriptor_freeze_id':descriptors['descriptor_freeze_id'],
       'scope_continuation_id':scope['continuation_id'],'semantics_id':sem['semantics_id'],
       'historical_retained_continuation_id':retained['continuation_id'],
       'stress_selection_id':c.load('stress-freeze-v2.json')['freeze_id'],
       'controllers':{p:digest(p) for p in paths},'library_sha256':library_sha,
       'target_numeric_cells_decoded':0,'model_fits':0,'scientific_work_is_serial':True,
       'smoke_sources':['ohpl_beer_nir','ohpl_soil_nir','ucph_tablet_nir','manure21_nir_all_y','ossl_jovic_visnir_soil_all_y'],
       'storage':c.guard()}
c.save('reference-operational-freeze.json',value)
atomic_json('docs/campaign/reference-operational-freeze.json',value)
print('REFERENCE_OPERATIONAL_FREEZE_BEFORE_NUMERIC_TARGET_ACCESS')
