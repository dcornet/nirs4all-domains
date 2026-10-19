"""Freeze categorical-code exclusions and source-derived endpoint cautions."""
from pathlib import Path
import yaml
from alpha18_common import Context
from nirs4all_domains.storage import atomic_json,fingerprint,digest

c=Context();f=c.load('campaign-freeze.json');assert not (c.root/'reference-progress.json').exists()
assert not (c.root/'target-semantics.json').exists()
records=[]
for task in f['tasks']:
    if not task['metadata_eligible']:continue
    name=task['dataset_id'];d=yaml.safe_load((Path('.audit/datasets/catalog/datasets')/(name+'.yaml')).read_text(encoding='utf-8'))
    target=task['target'].lower()
    code=target in {'class_index','class_label','raw_label','species','year','latitude','longitude','lat','lon','replicate','spectralrep','idvar','dimensions','feature_count_per_dimension'}
    classification=d.get('domain')=='timeseries' and any('timeseriesclassification.com' in str(s.get('locator','')) for s in d.get('origin_sources',[]))
    predicted='prediction' in str(d.get('name','')).lower()
    derived=target in {'ndvi','ndwi','pri'}
    records.append({'task_id':task['task_id'],'excluded':code or classification,
                    'reason':'CANONICAL_CLASSIFICATION_LABEL_NOT_CONTINUOUS_REFERENCE' if classification else 'IDENTIFIER_CATEGORY_OR_EXPERIMENTAL_COUNTER' if code else None,
                    'target_evidence':'source_declares_trait_predictions' if predicted else 'declared_spectral_index' if derived else 'catalog_quantitative_outcome_assay_independence_unverified',
                    'independent_assay_validated':False})
value={'parent_freeze_id':f['freeze_id'],'records':records,'numeric_target_cells_decoded':0,
       'selection_uses':'Catalog domain/origin/role/type/name; no target values or scores.',
       'controller_sha256':digest(__file__)}
value['semantics_id']=fingerprint(value);c.save('target-semantics.json',value)
atomic_json('docs/campaign/target-semantics.json',value)
print('SEMANTIC_EXCLUSIONS',sum(r['excluded'] for r in records),'QUALIFIED_METADATA_TASKS',sum(not r['excluded'] for r in records))
