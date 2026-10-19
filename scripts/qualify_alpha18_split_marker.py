"""One documented no-membership marker correction, before any target decode."""
from alpha18_common import Context
from nirs4all_domains import full_bank
from nirs4all_domains.storage import fingerprint,atomic_json,digest

c=Context();f=c.load('campaign-freeze.json');assert not (c.root/'reference-progress.json').exists()
assert not (c.root/'scope-marker-continuation.json').exists()
full_bank.NO_SPLIT.add('historical_splits_documented_not_applied')
entries={e['dataset_id']:e for e in f['entries']};scopes={}
for q in f['qualification']:
    if q['result']['reason']!='ValueError:UNRECOGNIZED_NATIVE_SPLIT_MEMBERSHIP':continue
    source=next(s for s in f['sources'] if s['view_id']==q['view_id'])
    scope=full_bank.metadata_scope(entries[source['dataset_id']],source)
    scopes[q['view_id']]=scope
value={'parent_freeze_id':f['freeze_id'],'scopes':scopes,
       'marker':'historical_splits_documented_not_applied',
       'evidence':'Identical constant marker in canonical M, catalog applied=false with documented_origin explicitly saying historical grouping/split terms are metadata only. No row carries train/test membership.',
       'target_numeric_cells_decoded':0,'model_fits':0,'controller_sha256':digest(__file__)}
value['continuation_id']=fingerprint(value);c.save('scope-marker-continuation.json',value)
atomic_json('docs/campaign/split-marker-continuation.json',{k:v for k,v in value.items() if k!='scopes'}|{'new_qualified_views':list(scopes),'new_scope_counts':{k:len(s['development_indices']) for k,s in scopes.items()}})
print('CORRECTED_NO_MEMBERSHIP_MARKER',len(scopes))
