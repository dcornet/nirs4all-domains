"""Freeze identity-only exploratory PLS/Ridge proposals; never decode numerical Y."""
import csv
from importlib.metadata import version
from pathlib import Path
import json
import yaml

from alpha17_common import Context, read
from nirs4all_domains.confrontation import ANCHORS
from nirs4all_domains.predictive import group_folds
from nirs4all_domains.storage import digest, fingerprint


def projection(path, names):
    import pandas as pd
    with path.open(encoding='utf-8-sig') as stream:
        first = stream.readline()
    separator = ';' if first.count(';') > first.count(',') else ','
    fields = next(csv.reader([first],delimiter=separator))
    chosen = [n for n in names if n in fields]
    table = pd.read_csv(path, sep=separator, usecols=chosen, dtype=str, keep_default_na=False) if chosen else None
    return fields, table.to_dict('records') if table is not None else []


def development_scope(links, descriptor):
    """Preserve documented source partitions even when not auto-applied by IO."""
    labels={'train':'train','training':'train','calibration':'train',
            'test':'retained','validation':'retained','val':'retained','retained':'retained'}
    role={}
    for row in links:
        values=[row[k].strip().lower() for k in ['partition','split','split_original'] if row.get(k,'').strip()]
        if not values:
            if descriptor.get('splits'):
                raise ValueError('DOCUMENTED_SOURCE_SPLIT_MEMBERSHIP_REQUIRED')
            role[row['observation_id']]='train'
        else:
            if any(v not in labels for v in values) or len({labels[v] for v in values})!=1:
                raise ValueError('EXPLICIT_CONSISTENT_SOURCE_PARTITION_LABEL_MAPPING_REQUIRED')
            role[row['observation_id']]=labels[values[0]]
    owners={}
    for row in links:
        key=row.get('sample_id')
        if key:
            if key in owners and owners[key]!=role[row['observation_id']]:
                raise ValueError('DECLARED_SAMPLE_DEPENDENCY_CROSSES_RETAINED_SCOPE')
            owners[key]=role[row['observation_id']]
    development=[r for r in links if role[r['observation_id']]=='train']
    retained=[r['observation_id'] for r in links if role[r['observation_id']]=='retained']
    return development,retained,'Source-defined retained membership sealed before numeric target access; IO applied flag does not change scope.'


def build(context, entry):
    name = entry['dataset_id'];root = Path(context.cfg['source_root'])/name
    descriptor = Path('.audit/datasets/catalog/datasets')/(name+'.yaml')
    metadata = yaml.safe_load(descriptor.read_text(encoding='utf-8'))
    paths = [root/(entry['source_id']+'.csv'),root/'M.csv',root/'Y.csv']
    result = {'dataset_id':name,'source_id':entry['source_id'], 'descriptor_sha256':digest(descriptor),
        'status':'not_frozen','blockers':[], 'real_fitting_authorized':False}
    if not all(p.is_file() for p in paths):
        result['blockers']=['REQUIRED_CANONICAL_TABLE_UNAVAILABLE'];return result
    context.guard(paths=[str(p) for p in paths])
    existing = context.load('candidate-inputs.json') if (context.root/'candidate-inputs.json').exists() else []
    context.save('candidate-inputs.json',sorted(set(existing)|{str(p) for p in paths}))
    keys = ['observation_id','sample_id','partition','split','split_original']
    xfields,xkeys = projection(paths[0],keys[:2]);mfields,links = projection(paths[1],keys)
    yfields,ykeys = projection(paths[2],['sample_id'])
    result['content'] = {p.name:{'path':str(p),'bytes':p.stat().st_size,'sha256':digest(p)} for p in paths}
    assert result['content'][paths[0].name]['sha256'] == entry['source_content_sha256'], 'PROFILE_TO_CANONICAL_X_CONTENT_CHANGED'
    if not links or not xkeys or not ykeys or any(not r.get('observation_id') or not r.get('sample_id') for r in links):
        result['blockers']=['EXPLICIT_CANONICAL_X_M_Y_KEYS_REQUIRED_NO_POSITIONAL_JOIN'];return result
    byobs = {r['observation_id']:r for r in links}
    if len(byobs)!=len(links) or len({r.get('sample_id') for r in ykeys})!=len(ykeys):
        result['blockers']=['UNIQUE_OBSERVATION_AND_TARGET_KEYS_REQUIRED'];return result
    if 'observation_id' not in xfields or {r['observation_id'] for r in xkeys}!=set(byobs):
        result['blockers']=['CANONICAL_X_TO_METADATA_OBSERVATION_KEYS_NOT_VERIFIED'];return result
    if {r['sample_id'] for r in links}!={r['sample_id'] for r in ykeys}:
        result['blockers']=['CANONICAL_TARGET_KEY_MEMBERSHIP_MISMATCH'];return result
    targets = [v for v in metadata['variables'] if v.get('role')=='target' and v['name'] in yfields]
    if not targets:
        result['blockers']=['DECLARED_QUANTITATIVE_TARGET_COLUMN_REQUIRED'];return result
    # Source descriptor declaration order, frozen before numerical Y access.
    target = targets[0]
    if target.get('type','').lower() not in ['float','float64','numeric','continuous','number','double']:
        result['blockers']=['DECLARED_CONTINUOUS_TARGET_REQUIRED'];return result
    try:
        development,retained,role=development_scope(links,metadata)
    except ValueError as error:
        result['blockers']=[str(error)];return result
    if len(development)<15:
        result['blockers']=['INSUFFICIENT_DEVELOPMENT_SUPPORT'];return result
    # Reuse the identity allocator. These transient legacy field aliases mean
    # observation/CV keys only, and supply no physical-independence assertion.
    units=[{'physical_sample_id':r['observation_id'],'independence_group':r['sample_id']} for r in development]
    outer=group_folds(units,5,17,'alpha17:reference',allocation='shuffle')
    inner={f['fold_id']:group_folds([r for r in units if r['physical_sample_id'] in f['train_sample_ids']],
        3,17,f['fold_id']+':inner',allocation='shuffle') for f in outer['folds']}
    result.update(status='identity_plan_frozen_numeric_qualification_pending',target={'column':target['name'],
        'declared_semantics':target,'unit':target.get('unit',target.get('units')),
        'unit_status':'documented' if target.get('unit') or target.get('units') else 'unspecified_canonical_units'},
        development_observation_ids=[r['observation_id'] for r in development],retained_observation_ids=retained,
        target_access_role=role,canonical_key_map=links,outer_folds=outer,inner_folds=inner,
        design='canonical_sample_key_CV_physical_dependencies_unresolved',
        independence_claim=False,known_same_sample_keys_kept_whole=True,
        anchors=ANCHORS,model_fit_upper_bound=sum(len(v['folds'])*8+2 for v in inner.values()),
        runtime_estimate_seconds=1800,peak_RAM_estimate_bytes=1073741824,
        estimate_status='Conservative operational limits, not measured on this task; stop on exceedance.',
        numerical_qualification_before_fit=['Finite development target values and non-identifier quantitative declaration',
            'Complete axes and finite development X through public Datasets/Methods providers',
            'Known verified dependency links preserved; unresolved physical ownership explicitly reported',
            'Retained target values never decoded for selection; fold-local fit/select/refit/null'],
        H1_H5_scope='Within-dataset exploratory predictive skill only; no supported stress contrast frozen.',
        actual_new_model_fits=0)
    result['proposal_id']=fingerprint(result)
    return result


def main():
    from n4m import library_path
    c=Context();path=c.root/'EXPLORATORY_FIT_PROPOSAL.json'
    if path.exists():
        c.load(path.name);print('ALPHA17_IDENTITY_PROPOSAL_ALREADY_PRESENT; NO_FITS');return
    entries=read('docs/benchmarks/alpha13/x-only-extension.json')['records']
    tasks=[build(c,e) for e in entries]
    packet={'tasks':tasks,'source_selection':'Two alpha13 extension views fixed by soil/pharmaceutical diversity and existing X qualification, without Y or performance.',
        'providers':{p:version(p) for p in ['nirs4all-methods','dag-ml','nirs4all-datasets']},
        'methods_library_sha256':digest(library_path()),'approved_real_fits':False,
        'new_reservations_proposed_bytes':16777216,'workspace_ceiling_increase_proposed':0,
        'campaign_ceiling_increase_proposed':0,'serial_execution':True,
        'per_task_reservation_bytes':8388608,'per_task_evidence_bytes':4194304,
        'estimated_runtime_upper_seconds':3600,'RAM_stop_bytes':1073741824,
        'new_X_characterization_or_B60':False,'TabPFN':False,
        'decision':'Request owner approval only after inspecting actual frozen identity plans and blockers.'}
    c.save(path.name,packet);c.preservation()
    print('ALPHA17_IDENTITY_PROPOSAL_PREPARED; NUMERIC_TARGETS_NOT_DECODED; NO_FITS')


if __name__=='__main__':
    try:main()
    except Exception:
        print('ALPHA17_IDENTITY_PROPOSAL_REFUSED; DETAILS_REMAIN_LOCAL')
        raise SystemExit(2) from None
