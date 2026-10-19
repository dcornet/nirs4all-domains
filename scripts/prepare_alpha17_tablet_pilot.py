"""Identity-only original-keyed pilot freeze; never decode quantitative targets."""
import copy
from importlib.metadata import version
from pathlib import Path

from alpha17_common import Context, read
from nirs4all_domains.confrontation import ANCHORS
from nirs4all_domains.dependence import validate_folds
from nirs4all_domains.predictive import group_folds
from nirs4all_domains.storage import digest, fingerprint


def identity_plan(original, canonical, marker):
    """Original record keys and declared context blocks, never physical aliases."""
    if marker!='by_batch_grouping_documented_not_applied':
        raise ValueError('SOURCE_SPECIFIC_SPLIT_DECLARATION_CHANGED')
    by_key={r['Unnamed: 0']:r for r in original}
    if len(by_key)!=len(original) or len({r['observation_id'] for r in canonical})!=len(canonical):
        raise ValueError('DUPLICATE_ORIGINAL_OR_CANONICAL_KEY')
    if len({r['source_sample_id'] for r in canonical})!=len(canonical) or set(by_key)!={r['source_sample_id'] for r in canonical}:
        raise ValueError('COMPLETE_BIJECTIVE_ORIGINAL_KEY_MAP_REQUIRED')
    blocks={};records=[]
    for r in canonical:
        o=by_key[r['source_sample_id']]
        if not o['Type'] or not r['batch'] or r['scale']!=o['Scale']:
            raise ValueError('SOURCE_CONTEXT_AND_SCALE_MEMBERSHIP_REQUIRED')
        if r['split_original']!=marker:
            raise ValueError('UNEXPECTED_RETAINED_OR_SOURCE_PARTITION_MEMBERSHIP')
        blocks.setdefault(r['batch'],set()).add(o['Type'])
        records.append({'observation_id':r['observation_id'],'source_record_key':r['source_sample_id'],
            'source_type':o['Type'],'declared_block':r['batch'],'source_scale':o['Scale']})
    if any(len(v)!=1 for v in blocks.values()):
        raise ValueError('DECLARED_BLOCK_WOULD_CROSS_TYPE_HOLDOUT')
    # These two legacy transport names mean observation key / declared Type
    # only. No persisted biological/assay identity is inferred from them.
    units=[{'physical_sample_id':r['observation_id'],'independence_group':r['source_type']} for r in records]
    outer=group_folds(units,4,17,'alpha17:tablet:original-type',allocation='shuffle')
    validate_folds(units,outer)
    inner={}
    for f in outer['folds']:
        selected=[r for r in units if r['physical_sample_id'] in f['train_sample_ids']]
        inner[f['fold_id']]=group_folds(selected,3,17,f['fold_id']+':inner',allocation='shuffle')
        validate_folds(selected,inner[f['fold_id']])
    return {'records':records,'outer_folds':outer,'inner_folds':inner,
        'original_contexts':len({r['source_type'] for r in records}),'declared_blocks':len(blocks),
        'development_observation_ids':[r['observation_id'] for r in records],
        'retained_observation_ids':[], 'all_declared_blocks_preserved':True,
        'physical_and_assay_independence':'unknown; these are source contexts and declared blocks'}


def main():
    import pandas as pd
    from n4m._ffi import library_path
    c=Context();name='ORIGINAL_KEYED_TABLET_PILOT_FREEZE.json'
    if (c.root/name).exists():
        c.load(name);print('ALPHA17_TABLET_FREEZE_REUSED; NOT_AUTHORIZED');return
    pre=c.load('original-tablet-metadata-preflight.json');leaf=Path(pre['leaf'])
    source=Path(pre['original_source']);x=leaf/'X.csv';m=leaf/'M.csv'
    c.guard(paths=[str(source),str(x),str(m)])
    proof_path=Path('docs/benchmarks/alpha13/sources/tablet-original-key-audit.json');proof=read(proof_path)
    for p in [source,x,m]:assert digest(p)==proof['source_hashes'][p.name], 'ORIGINAL_KEYED_X_INPUT_CHANGED'
    assert proof['original_x_correspondence']['exact_spectral_rows']==310
    metadata=pd.read_csv(m,sep=';',usecols=['observation_id','source_sample_id','batch','scale','split_original'],dtype=str,keep_default_na=False).to_dict('records')
    identities=identity_plan(pre['metadata'],metadata,'by_batch_grouping_documented_not_applied')
    assert len(identities['records'])==310 and identities['original_contexts']==4 and identities['declared_blocks']==31
    fit_count=sum(len(identities['inner_folds'][f['fold_id']]['folds'])*sum(len(next(iter(a['grid'].values()))) for a in ANCHORS)+len(ANCHORS) for f in identities['outer_folds']['folds'])
    assert fit_count==104
    extension=read('docs/benchmarks/alpha13/x-only-extension.json')
    existing=next(r for r in extension['records'] if r['dataset_id']=='ucph_tablet_nir')
    for p in existing['profiles'].values():assert digest(p['path'])==p['sha256']
    inputs=[{'path':str(p),'sha256':digest(p),'bytes':p.stat().st_size} for p in [source,x,m]]
    packet={'protocol':'domains.alpha17.original_keyed_context_pilot.v0.1',
        'dataset_id':'ucph_tablet_nir','source_id':'X','content_version':'1.0.0',
        'source_url':'https://ucphchemometrics.com/tablet/',
        'source_authenticity_scope':'Existing cached flat table and frozen alpha13 exact keyed X audit; no newly owner-verified specimen/assay identities.',
        'inputs':inputs,'original_source':str(source),'canonical_X':str(x),'canonical_M':str(m),
        'target':{'column':'active (%w/w)','meaning':'Active substance mass fraction','unit':'percent mass/mass',
            'owner_key':'Unnamed: 0','numeric_values_validated':False,'numeric_target_cells_decoded':0},
        'canonical_Y_used':False,'join':'canonical observation_id -> M.source_sample_id -> original record key -> co-located quantitative target column',
        'X_correspondence_receipt':{'path':str(proof_path),'sha256':digest(proof_path)},
        'identities':identities,'n_observations':310,'n_bands':404,
        'access_scope':'All 310 provided development observations; marker is a grouping recommendation, not declared retained membership. Source page calls these development data.',
        'evaluation':'Leave one original Type context out, nested leave-one-remaining-Type-out; preserve every provided canonical block.',
        'independent_generalization':False,'study_role':'exploratory_discovery; not independent confirmation',
        'anchors':copy.deepcopy(ANCHORS),'native_model_fit_upper':fit_count,
        'train_only_PCA_fit_upper':4,'PCA_components':20,
        'PCA_scope':'Methods FlexiblePCA fit outer training X, then transform train/evaluation without refit. Descriptive PC1/2 summaries only; no invented exact full moments/support score.',
        'frozen_X_descriptors':existing,
        'hypotheses':{'contract_path':'docs/benchmarks/alpha13/falsification-contract.json',
            'sha256':digest('docs/benchmarks/alpha13/falsification-contract.json'),
            'H1_H5_changed':False,'stress_contrast':'unavailable: first within-dataset reference experiment only',
            'D_RMSE':'unavailable without matched reference/stress designs','D_skill':'unavailable without matched reference/stress designs',
            'S':'1 - pooled OOF RMSE / pooled training-only null OOF RMSE; unavailable for zero/undefined null'},
        'outcomes':['Pooled and per-context RMSE/MAE/R2 and null-relative skill for both fixed model families.',
            'Training-only target range and evaluation extrapolation counts; no cross-dataset absolute-error inference.',
            'Train-fitted PC1/2 descriptive summaries, missingness, lineage, selected parameters and failures.',
            'No group/study confidence interval from four unverified contexts; no post-response descriptor selection.'],
        'providers':{k:version(k) for k in ['nirs4all-methods','dag-ml','nirs4all-datasets']},
        'methods_library_sha256':digest(library_path()),
        'controller_sha256':digest('scripts/run_alpha17_tablet_pilot.py'),
        'preparer_sha256':digest(__file__),
        'bridge_sha256':{n:digest(Path('bridges/python/nirs4all_domains')/n) for n in ['multifamily.py','predictive.py','dependence.py']},
        'resource':{'new_reservation_bytes':8388608,'scratch_bytes':4194304,'essential_evidence_bytes':4194304,
            'additional_combined_upper_bytes':67108864,'estimated_wall_stop_seconds':3600,'estimated_RAM_stop_bytes':1073741824,
            'estimate_scope':'Operational bounds; real task runtime/native peaks not yet observed. NumPy float64 feature transport alone is 1001920 bytes, not a whole-process estimate.',
            'serial_tasks':1,'workspace_ceiling_increase':0,'campaign_ceiling_increase':0},
        'failure_policy':'Abort on changed hashes, key/scope/group conflict, any missing/nonfinite X/Y, unsupported native metric or resource bound. Keep partial checkpoints and denominator; no row dropping, redraw or automatic refit.',
        'publication':'Ordinary aggregates under existing source permission; raw X/Y, source record keys, fold rosters and OOF predictions remain protected.',
        'real_fitting_authorized':False,'new_real_fits':0}
    packet['plan_id']=fingerprint(packet);c.save(name,packet);c.preservation()
    print('ALPHA17_ORIGINAL_KEYED_TABLET_PILOT_FROZEN; 104_MODEL_PLUS_4_PCA_FITS_PROPOSED; NO_TARGET_DECODE_OR_FITS')


if __name__=='__main__':
    try:main()
    except Exception as error:
        try:Context().save('tablet-freeze-failure.json',{'type':type(error).__name__,'detail':str(error)})
        except Exception:pass
        print('ALPHA17_TABLET_FREEZE_REFUSED; DETAILS_REMAIN_LOCAL');raise SystemExit(2) from None
