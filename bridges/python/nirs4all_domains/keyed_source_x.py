"""Declared CSV field projection and identity joins; no reference-cell access."""
import pandas as pd
from .storage import fingerprint


def read_keyed_x(path,key,axis_headers,axis_unit,sep=';'):
    columns=[key,*axis_headers]
    frame=pd.read_csv(path,sep=sep,usecols=columns,dtype={key:str})
    ids=frame[key].tolist()
    if len(ids)!=len(set(ids)) or any(not isinstance(s,str) or not s for s in ids):raise ValueError('UNIQUE_DECLARED_ORIGINAL_KEYS_REQUIRED')
    return {'observation_ids':ids,'axis':list(map(float,axis_headers)),'axis_unit':axis_unit,'spectra':frame[axis_headers].values.tolist()}


def verify_keyed_x(original,canonical,canonical_to_original):
    if original['axis']!=canonical['axis'] or original['axis_unit']!=canonical['axis_unit']:raise ValueError('EXACT_DECLARED_SOURCE_AXES_REQUIRED')
    ids=canonical['observation_ids'];source_ids=original['observation_ids']
    if len(set(ids))!=len(ids) or len(set(source_ids))!=len(source_ids):raise ValueError('UNIQUE_SOURCE_IDENTITIES_REQUIRED')
    if set(ids)!=set(canonical_to_original) or set(canonical_to_original.values())!=set(source_ids) or len(set(canonical_to_original.values()))!=len(ids):
        raise ValueError('COMPLETE_ONE_TO_ONE_ORIGINAL_KEY_JOIN_REQUIRED')
    source=dict(zip(source_ids,original['spectra'],strict=True));derived=dict(zip(ids,canonical['spectra'],strict=True))
    mismatches=[s for s in sorted(ids) if source[canonical_to_original[s]]!=derived[s]]
    return {'n_observations':len(ids),'n_bands':len(original['axis']),'exact_spectral_rows':len(ids)-len(mismatches),
        'mismatched_canonical_ids':mismatches,'join':'Declared canonical observation_id -> source_sample_id -> original source key; never row position',
        'key_map_sha256':fingerprint(canonical_to_original),'axis_sha256':fingerprint(original['axis']),
        'original_observation_correspondence_verified':not mismatches,'physical_or_assay_independence_verified':False,'target_accessed':False}
