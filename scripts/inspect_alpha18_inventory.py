"""Print catalog-level planning summaries, never raw rows or local locators."""
from collections import Counter
from alpha18_common import Context

c=Context();v=c.load('inventory.json')
print('TARGETS_BY_ENTRY',Counter(t['dataset_id'] for t in v['tasks'] if t['metadata_eligible']))
print('M_HEADERS',Counter(tuple(e.get('metadata_headers',[])) for e in v['entries'] if e['analysis_authorized']))
print('SPLIT_DECLARATIONS',[(e['dataset_id'],e['declared_splits']) for e in v['entries'] if e['declared_splits']])
print('PERMISSION',Counter(s['aggregate_permission'] for s in v['sources']))
print('X_SHAPES',[(s['view_id'],s.get('n_observations'),s.get('n_bands')) for s in v['sources'] if s['X_plan']=='compute'])
