"""Frozen grouped refits; no pooling of overlapping OOF as independent evidence."""
from __future__ import annotations
from collections import Counter
import math

from .dependence import development_rows, score_oof, state, validate_folds
from .multifamily import inner_fit, validate_spec
from .predictive import group_folds, native_summary
from .storage import fingerprint

PROTOCOL="domains.repeated_design.v0.1"


def freeze(task, specs, *, seeds=(17,31,47), outer=3, inner=3, transfer_hash=None):
    rows=development_rows(task)
    groups={r['independence_group'] for r in rows}
    if len(groups)<10:raise ValueError('REPEATED_DESIGN_REQUIRES_TEN_DOCUMENTED_COMPONENTS')
    if len(seeds)!=3 or len(set(seeds))!=3:raise ValueError('THREE_DISTINCT_PRESPECIFIED_SEEDS_REQUIRED')
    for spec in specs:validate_spec(spec)
    designs={}
    for seed in seeds:
        folds=group_folds(rows,outer,seed,f'refit:{seed}')
        validate_folds(rows,folds)
        inners={f['fold_id']:group_folds([r for r in rows if r['physical_sample_id'] in set(f['train_sample_ids'])],
                    inner,seed,f['fold_id']+':inner') for f in folds['folds']}
        designs[str(seed)]={'outer':folds,'inner':inners}
    body={'protocol_version':PROTOCOL,'context':task['context'],'development_sha256':fingerprint(rows),
          'specifications':specs,'designs':designs,'n_components':len(groups),'n_physical_units':len(rows),
          'transfer_hash':transfer_hash,'selection_basis':'source/material/identity support before new model scores',
          'test_target_accessed':False}
    return {**body,'evaluation_id':fingerprint(body)}


def run_design(task,frozen,design,spec,library,transfer=None):
    if frozen['evaluation_id']!=fingerprint({k:v for k,v in frozen.items() if k!='evaluation_id'}):
        raise ValueError('FROZEN_REFIT_DESIGN_CHANGED')
    rows=development_rows(task)
    if fingerprint(rows)!=frozen['development_sha256'] or spec not in frozen['specifications']:
        raise ValueError('FROZEN_REFIT_CONTENT_OR_ESTIMATOR_CHANGED')
    if (fingerprint(transfer) if transfer is not None else None)!=frozen['transfer_hash']:
        raise ValueError('FROZEN_TRANSFER_CONTENT_CHANGED')
    by_id={r['physical_sample_id']:r for r in rows}
    if transfer is not None and (not transfer or not set(transfer)<=set(by_id)):raise ValueError('EXACT_TRANSFER_PHYSICAL_KEYS_REQUIRED')
    folds=frozen['designs'][str(design)]
    validate_folds(rows,folds['outer'])
    predictions,lineage=[],[]
    for fold in folds['outer']['folds']:
        train=[by_id[s] for s in fold['train_sample_ids']];valid=[by_id[s] for s in fold['validation_sample_ids']]
        try:
            fitted,trace=inner_fit(train,folds['inner'][fold['fold_id']],spec,library)
            pred=fitted.predict([r['x'] for r in valid]).reshape(-1).tolist()
            cross_ids=[r['physical_sample_id'] for r in valid if transfer is not None and r['physical_sample_id'] in transfer]
            cross=dict(zip(cross_ids,fitted.predict([transfer[s] for s in cross_ids]).reshape(-1).tolist(),strict=True)) if cross_ids else {}
            if not all(map(math.isfinite,pred+list(cross.values()))):raise ValueError('NONFINITE_PREDICTION')
            baseline=native_summary(r['y'] for r in train)['mean']
            low,high=min(r['y'] for r in train),max(r['y'] for r in train)
            predictions.extend({'physical_sample_id':r['physical_sample_id'],'component_id':r['independence_group'],
                'fold_id':fold['fold_id'],'y':r['y'],'prediction':p,'null':baseline,'transfer_prediction':cross.get(r['physical_sample_id']),
                'outside_training_y_range':not low<=r['y']<=high} for i,(r,p) in enumerate(zip(valid,pred,strict=True)))
            lineage.append({'fold_id':fold['fold_id'],'train_ids_sha256':fingerprint(fold['train_sample_ids']),
                            'inner_folds_sha256':fingerprint(folds['inner'][fold['fold_id']]),**trace})
        except Exception as e:
            return {**state(reason=f'{type(e).__name__}:{e}',status='failed'),'failed_fold_id':fold['fold_id'],
                    'completed_folds':lineage,'partial_oof_count':len(predictions)}
    predictions.sort(key=lambda r:r['physical_sample_id'])
    return state({'evaluation_id':frozen['evaluation_id'],'design_id':str(design),'specification':spec,'oof':predictions,
        'scores':score_oof(predictions,'prediction'),'null_scores':score_oof(predictions,'null'),
        'transfer_scores':score_oof([r for r in predictions if r['transfer_prediction'] is not None],'transfer_prediction') if transfer is not None else state(reason='NO_QUALIFIED_TRANSFER'),
        'transfer_matched_reference_scores':score_oof([r for r in predictions if r['transfer_prediction'] is not None],'prediction') if transfer is not None else state(reason='NO_QUALIFIED_TRANSFER'),
        'transfer_evaluation_ids':[r['physical_sample_id'] for r in predictions if r['transfer_prediction'] is not None],
        'lineage':lineage,'n_independently_challenged_components':len({r['component_id'] for r in predictions}),
        'group_outcomes':[{'component_id':g,'n_physical_units':len(selected),'scores':score_oof(selected,'prediction')}
                          for g in sorted({r['component_id'] for r in predictions})
                          for selected in [[r for r in predictions if r['component_id']==g]]],
        'test_target_accessed':False})


def summarize_designs(results):
    successful=[r['value'] for r in results if r['status']=='computed']
    if len(successful)!=3:return state(reason='THREE_COMPLETE_FITTED_DESIGNS_REQUIRED')
    indexes=[{r['physical_sample_id']:r for r in design['oof']} for design in successful]
    if any(len(k)!=len(d['oof']) for k,d in zip(indexes,successful,strict=True)) or any(set(k)!=set(indexes[0]) for k in indexes):
        raise ValueError('REPEATED_PHYSICAL_ID_POPULATIONS_DIFFER')
    for key in indexes[0]:
        if any((k[key]['component_id'],k[key]['y'])!=(indexes[0][key]['component_id'],indexes[0][key]['y']) for k in indexes):
            raise ValueError('REPEATED_REFERENCE_OR_COMPONENT_CHANGED')
    return state({'conditioning':'Three overlapping completely refitted grouped designs on the same development population; descriptive variation, no confidence interval',
        'n_unique_physical_units':len(indexes[0]),'n_independent_components':len({r['component_id'] for r in indexes[0].values()}),
        'n_designs':3,'not_independent_observation_count':3*len(indexes[0]),
        'rmse_across_designs':native_summary(d['scores']['value']['rmse']['value'] for d in successful),
        'matched_identity_prediction_variation':[{'physical_sample_id':key,'prediction_summary':native_summary(k[key]['prediction'] for k in indexes)} for key in sorted(indexes[0])],
        'selected_hyperparameters':[{'design_id':d['design_id'],'selected':[r['selected'] for r in d['lineage']]} for d in successful],
        'conditional_bootstrap':state(reason='SEPARATE_FROZEN_OOF_PROTOCOL; NOT_AN_INTERVAL_ON_REFIT_VARIATION'),
        'new_source_population_uncertainty':state(reason='NO_INDEPENDENT_NEW_SOURCE_POPULATIONS_SAMPLED')})
