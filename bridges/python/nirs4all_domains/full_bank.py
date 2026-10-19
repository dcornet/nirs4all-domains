"""Small same-export/identity adapter and native fixed-model campaign transport.

No solver, metric, covariance, distance or summary kernel is implemented here.
"""
import csv
import math
from pathlib import Path

from .dependence import state
from .predictive import group_folds, native_summary
from .storage import fingerprint,digest

PROTOCOL = 'domains.bank_reference.v0.1'
ALIGNMENT_PROTOCOL = 'domains.same_export.v0.2'
KEYS = ('observation_id', 'sample_id', 'ID_sample')
GROUPS = ('sample_id', 'ID_sample', 'Leaf_ID', 'joint_id', 'batch',
          'source_sample_id', 'validation_component_id', 'reference_id')
CONTEXTS = ('bone_type', 'Experiment', 'Water_treatment', 'cereal_type',
            'crop', 'product_type', 'batch', 'instrument', 'scan_lab',
            'scan_model_name', 'scan_preparation', 'site', 'source_site',
            'country_iso3166', 'source_Stage', 'source_state')
TRAIN = {'train', 'training', 'calibration', 'cal', 'development', 'dev'}
RETAINED = {'test', 'testing', 'validation', 'val', 'holdout', 'retained'}
NO_SPLIT = {'', 'all', 'none', 'nan', 'unspecified', 'not_available', 'no_split',
            'no_original_split', 'not_defined', 'not_provided', 'unsplit',
            'by_batch_grouping_documented_not_applied', 'no_native_split'}
NO_SPLIT.add('historical_splits_documented_not_applied')


def aligned_order(x_ids, m_ids, y_ids, *, owner_attested, same_export, n_y):
    """Return Y row positions for X order; counts alone never authorize alignment."""
    if len(x_ids) != len(set(x_ids)) or not x_ids:
        raise ValueError('UNIQUE_OBSERVATION_KEYS_REQUIRED')
    if m_ids is not None and (len(m_ids) != len(x_ids) or set(m_ids) != set(x_ids)):
        raise ValueError('X_M_IDENTITY_CONFLICT')
    if y_ids is not None:
        if len(y_ids) != len(set(y_ids)) or set(y_ids) != set(x_ids):
            raise ValueError('X_Y_IDENTITY_CONFLICT')
        index = {v:i for i,v in enumerate(y_ids)}
        return [index[v] for v in x_ids], 'explicit_keys'
    if not owner_attested or not same_export or n_y != len(x_ids):
        raise ValueError('SAME_EXPORT_ATTESTATION_AND_COUNTS_REQUIRED')
    if m_ids is not None and m_ids != x_ids:
        raise ValueError('UNKEYED_Y_CONFLICTING_X_M_ORDER')
    return list(range(n_y)), 'owner_attested_same_export_order'


def matrix_request(source):
    import pandas as pd
    frame = pd.read_csv(source['matrix'], sep=source['separator'])
    columns = [c for c in frame if c not in KEYS]
    ids = frame['observation_id'].astype(str).tolist() if 'observation_id' in frame else [
        'export-row:'+fingerprint([source['view_id'], i]) for i in range(len(frame))]
    if len(ids) != len(set(ids)):
        raise ValueError('DUPLICATE_OBSERVATION_ID')
    x = frame[columns].values.tolist()
    if not x or not columns or any(not math.isfinite(float(v)) for row in x for v in row):
        raise ValueError('NONFINITE_OR_EMPTY_X')
    try:
        physical = list(map(float, columns))
        ordered = all(map(math.isfinite, physical)) and all(a < b for a,b in zip(physical,physical[1:]))
    except ValueError:
        physical, ordered = None, False
    policy = 'original_ordered_physical_axis' if ordered else 'original_column_order_logical_axis_physical_operations_disabled'
    return {'source_id':source['source_id'], 'observation_ids':ids,
            'identity_evidence':'observation_identity_only', 'spectra':x,
            'axis':physical if ordered else list(range(len(columns))),
            'axis_unit':source['axis_unit'] if ordered else 'feature_index'}, {
                'policy':policy, 'original_labels':list(columns), 'original_unit':source['axis_unit']}


def metadata_scope(entry, source, *, export_contract=None):
    """Read only keys/split/context fields, never reference or outcome columns."""
    import pandas as pd
    if not source.get('source_id') or not entry.get('dataset_id') or entry.get('dataset_id')!=source.get('dataset_id') or not entry.get('content_version') or entry.get('content_version')!=source.get('content_version'):
        raise ValueError('DECLARED_SHARED_DATASET_CONTENT_NAMESPACE_REQUIRED')
    contract=export_contract or entry.get('same_export_contract',{})
    common_export=bool(contract.get('export_id')) and contract.get('order_preserved') is True and all(
        contract.get(k)==source.get(k) for k in ['dataset_id','content_version','source_id'])
    attested=contract.get('owner_attested') is True
    unkeyed_metadata=entry.get('metadata_available',True) and bool(entry.get('metadata_headers')) and 'observation_id' not in entry['metadata_headers']
    if 'observation_id' not in source['headers'] or 'observation_id' not in entry['target_headers'] or unkeyed_metadata:
        if not common_export or not attested:raise ValueError('EXPLICIT_SAME_EXPORT_ATTESTATION_REQUIRED')
        paths={'X':source['matrix'],'Y':entry['target_path']}
        if entry.get('metadata_available',True):paths['M']=entry['metadata_path']
        if any(contract.get('sha256',{}).get(k)!=digest(path) for k,path in paths.items()):raise ValueError('SAME_EXPORT_FILE_BINDING_MISMATCH')
    n = source['n_observations']
    xcols = [k for k in ['observation_id'] if k in source['headers']]
    if xcols:
        x_ids = pd.read_csv(source['matrix'], sep=source['separator'], usecols=xcols, dtype=str).fillna('')['observation_id'].tolist()
    else:
        x_ids = ['export-row:'+fingerprint([source['view_id'], i]) for i in range(n)]
    if len(x_ids)!=n:raise ValueError('DECLARED_X_ROW_COUNT_MISMATCH')
    mh = entry.get('metadata_headers', [])
    columns = [k for k in ['observation_id',*GROUPS,*CONTEXTS,'split_original','source_split','split'] if k in mh]
    columns = list(dict.fromkeys(columns))
    m = pd.read_csv(entry['metadata_path'], sep=entry['metadata_separator'], usecols=columns, dtype=str).fillna('') if columns else None
    if m is not None and len(m)!=n:raise ValueError('X_M_ROW_COUNT_MISMATCH')
    m_ids = m['observation_id'].tolist() if m is not None and 'observation_id' in m else None
    yh = entry['target_headers'];y_ids = None
    if 'observation_id' in yh:
        y_ids = pd.read_csv(entry['target_path'],sep=entry['target_separator'],usecols=['observation_id'],dtype=str).fillna('')['observation_id'].tolist()
    order,basis = aligned_order(x_ids,m_ids,y_ids,owner_attested=attested,same_export=common_export,n_y=entry['target_rows'])
    if m_ids is not None:
        m = m.set_index('observation_id').loc[x_ids].reset_index()
    rows = m.to_dict('records') if m is not None else [{} for _ in x_ids]
    partitions=[]
    for row in rows:
        values={str(row.get(k,'')).strip().lower() for k in ['split_original','source_split','split']}-NO_SPLIT
        if not values:partitions.append('development');continue
        if not values <= TRAIN|RETAINED:
            raise ValueError('UNRECOGNIZED_NATIVE_SPLIT_MEMBERSHIP')
        if values & TRAIN and values & RETAINED:
            raise ValueError('CONTRADICTORY_NATIVE_SPLIT_MEMBERSHIP')
        partitions.append('retained' if values & RETAINED else 'development')
    # Identity connectivity is task policy, not a numerical kernel. Missing keys
    # never connect two unrelated observations.
    parent=list(range(n))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    used=[]
    for key in GROUPS:
        seen={};repeated=False
        for i,row in enumerate(rows):
            val=str(row.get(key,'')).strip()
            if not val or val.lower() in ['nan','none','na']:continue
            if val in seen:parent[find(i)]=find(seen[val]);repeated=True
            else:seen[val]=i
        if repeated:used.append(key)
    groups=['component:'+fingerprint([source['view_id'],find(i)]) for i in range(n)]
    retained_groups={groups[i] for i,p in enumerate(partitions) if p=='retained'}
    development=[i for i,p in enumerate(partitions) if p=='development' and groups[i] not in retained_groups]
    return {'observation_ids':x_ids,'Y_order':order,'alignment':basis,'groups':groups,
            'group_columns':used,'n_retained':partitions.count('retained'),
            'development_indices':development,'n_purged_retained_component':sum(p=='development' and groups[i] in retained_groups for i,p in enumerate(partitions)),
            'contexts':{k:[r.get(k,'') for r in rows] for k in CONTEXTS if k in columns},
            'biological_independence_verified':False}


def target_values(entry, target, scope):
    """Filter retained membership BEFORE float conversion, including invalid cells."""
    wanted={scope['Y_order'][i]:i for i in scope['development_indices']};out={};missing=0
    with Path(entry['target_path']).open(encoding='utf-8-sig',newline='') as stream:
        for pos,row in enumerate(csv.DictReader(stream,delimiter=entry['target_separator'])):
            if pos not in wanted:continue
            cell=row[target].strip()
            if cell.lower() in ['', 'nan','na','none','null']:
                missing+=1;continue
            value=float(cell)
            if not math.isfinite(value):raise ValueError('NONFINITE_NONMISSING_TARGET')
            out[wanted[pos]]=value
    return out,missing


def folds_for(indices, scope, task_id):
    rows=[{'physical_sample_id':scope['observation_ids'][i],'independence_group':scope['groups'][i]} for i in indices]
    # Legacy field names below are DAG transport aliases; no physical claim.
    if len(rows)<12:raise ValueError('FEWER_THAN_TWELVE_AVAILABLE_DEVELOPMENT_OBSERVATIONS')
    return group_folds(rows,3,18,'bank:'+task_id)


def scores(y, predictions, null):
    from n4m.metrics.scoring import rmse,mae,r2
    yy=[[v] for v in y];pp=[[v] for v in predictions]
    null_rmse=float(rmse(yy,[[v] for v in null]));error=float(rmse(yy,pp))
    result={'rmse':state(error),'mae':state(float(mae(yy,pp))),
            'null_rmse':state(null_rmse),'skill':state(1-error/null_rmse) if null_rmse>0 else state(reason='ZERO_NULL_RMSE')}
    sd=native_summary(y)['sd']
    result['r2']=state(float(r2(yy,pp))) if sd is not None and sd>0 else state(reason='CONSTANT_OR_SINGLETON_EVALUATION_TARGET')
    return result


def fit_predict(x, y, train, evaluation, family, components):
    from n4m.roles import PLSRegression,Ridge
    if set(train)&set(evaluation):raise ValueError('TRAIN_EVALUATION_IDENTITY_OVERLAP')
    if native_summary([y[i] for i in train])['sd']==0:raise ValueError('CONSTANT_TRAIN_TARGET')
    model=PLSRegression(n_components=components,center_x=True,scale_x=False,center_y=True,scale_y=False) if family=='pls' else Ridge(alpha=1.,center_x=True,scale_x=False,center_y=True)
    model.fit([x[i] for i in train],[[y[i]] for i in train])
    pred=model.predict([x[i] for i in evaluation]).reshape(-1).tolist()
    if len(pred)!=len(evaluation) or not all(map(math.isfinite,pred)):raise ValueError('INVALID_NATIVE_PREDICTION')
    return pred


def reference_task(x, y, scope, task, *, folds=None):
    indices=sorted(y)
    if folds is None:
        folds=folds_for(indices,scope,task['task_id'])
    else:
        # Explicit stronger context designs reuse the same fixed native models.
        # Validate complete observation coverage and the ACTUAL declared groups,
        # rather than trusting only the caller's FoldSet sample_groups mapping.
        from .dependence import validate_folds
        rows=[{'physical_sample_id':scope['observation_ids'][i],'independence_group':scope['groups'][i]} for i in indices]
        validate_folds(rows,folds)
    byid={s:i for i,s in enumerate(scope['observation_ids'])}
    components=min(3,len(x[0]),min(len(f['train_sample_ids']) for f in folds['folds'])-1)
    if components<1:raise ValueError('INSUFFICIENT_TRAINING_SHAPE')
    output={'n_development':len(scope['development_indices']),'n_evaluated':len(indices),
            'n_groups':len({scope['groups'][i] for i in indices}), 'group_columns':scope['group_columns'],
            'evaluation_scope':'declared_component_CV' if scope['group_columns'] else 'potentially_optimistic_observation_CV',
            'biological_independence_verified':False,'n_retained_excluded':scope['n_retained'],
            'n_purged_retained_component':scope['n_purged_retained_component'],
            'target_summary':native_summary(y.values()),'components':components,'families':{},'model_fit_attempts':0,'model_fit_successes':0}
    for family in ['pls','ridge']:
        fp=[];oof=[]
        for f in folds['folds']:
            train=[byid[s] for s in f['train_sample_ids']];ev=[byid[s] for s in f['validation_sample_ids']]
            summary=native_summary([y[i] for i in train]);null=[summary['mean']]*len(ev)
            output['model_fit_attempts']+=1
            try:
                p=fit_predict(x,y,train,ev,family,components);output['model_fit_successes']+=1
                metric=scores([y[i] for i in ev],p,null)
                oof.extend([[i,pred,base] for i,pred,base in zip(ev,p,null)])
                fp.append({'fold_id':f['fold_id'],'result':state(metric),'n_train':len(train),'n_evaluation':len(ev),
                           'n_train_groups':len({scope['groups'][i] for i in train}),
                           'target_extrapolation_count':sum(y[i]<summary['min'] or y[i]>summary['max'] for i in ev)})
            except Exception as error:fp.append({'fold_id':f['fold_id'],'result':state(reason=type(error).__name__+':'+str(error),status='failed'),'n_train':len(train),'n_evaluation':len(ev)})
        pooled=state(scores([y[i] for i,_,_ in oof],[p for _,p,_ in oof],[v for _,_,v in oof])) if len(oof)==len(indices) else state(reason='INCOMPLETE_OOF_FAMILY',status='failed')
        output['families'][family]={'folds':fp,'pooled':pooled,'oof':oof}
    output['fold_fingerprint']=fingerprint(folds)
    return output
