"""Original keyed litter CSV field projection, with no reference-cell access."""
import pandas as pd


def read_litter_view(path,source_id,axis=tuple(range(400,2401))):
    columns=['ID',*map(str,axis)]
    # Only these columns are materialized. Reference columns can contain arbitrary
    # strings without entering conversion, matching, selection or diagnostics.
    frame=pd.read_csv(path,usecols=columns,dtype={'ID':str})
    ids=frame.ID.tolist()
    if len(ids)!=len(set(ids)) or any(not isinstance(s,str) or not s for s in ids):
        raise ValueError('UNIQUE_ORIGINAL_LITTER_IDS_REQUIRED')
    return {'source_id':source_id,'observation_ids':ids,'identity_evidence':'verified_physical_identity',
        'axis':list(axis),'axis_unit':'nm','spectra':frame[list(map(str,axis))].values.tolist()}


def match_litter_views(left,right):
    if left['axis']!=right['axis'] or left['axis_unit']!=right['axis_unit']:
        raise ValueError('IDENTICAL_ORIGINAL_PAIRED_AXES_REQUIRED')
    rows=[dict(zip(v['observation_ids'],v['spectra'],strict=True)) for v in (left,right)]
    common=sorted(set(rows[0])&set(rows[1]))
    matched=[{**v,'observation_ids':common,'spectra':[data[s] for s in common]} for v,data in zip((left,right),rows,strict=True)]
    return matched,{'n_matched':len(common),'left_only':sorted(set(rows[0])-set(rows[1])),
        'right_only':sorted(set(rows[1])-set(rows[0])),'join':'original ID; never source row position',
        'parent_observation_counts':[len(left['observation_ids']),len(right['observation_ids'])]}
