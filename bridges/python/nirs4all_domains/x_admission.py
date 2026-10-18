"""Rights-scoped source admission, separate from physical/reference modeling."""
from .admission import DIMENSIONS
from .falsification import require_pre_outcome
from .storage import fingerprint


def authorize_x_source(spec):
    require_pre_outcome(spec)
    required={'dataset_id','content_version','source_id','catalog_tier','original_source_url','provenance_urls','permissions','metadata_hashes','identity_scope'}
    if set(spec)!=required:raise ValueError('COMPLETE_TARGET_FREE_SOURCE_SPECIFICATION_REQUIRED')
    if spec['original_source_url'] not in spec['provenance_urls']:raise ValueError('ORIGINAL_SOURCE_PROVENANCE_MISMATCH')
    if set(spec['permissions'])!=set(DIMENSIONS):raise ValueError('FOUR_PERMISSION_DIMENSIONS_REQUIRED')
    for dimension in DIMENSIONS:
        permission=spec['permissions'][dimension]
        if permission.get('status') not in ['allowed','unknown','denied']:raise ValueError('UNKNOWN_RIGHTS_STATE')
        if dimension!='redistribute_raw' and (permission['status']!='allowed' or not permission.get('evidence')):
            raise ValueError('ORIGINAL_X_RIGHTS_NOT_AUTHORIZED:'+dimension)
    if spec['identity_scope']!='observation_conditional':raise ValueError('PHYSICAL_IDENTITIES_REQUIRE_SEPARATE_ORIGINAL_KEY_PROOF')
    if not spec['metadata_hashes']:raise ValueError('SOURCE_METADATA_HASHES_REQUIRED')
    result={'protocol_version':'domains.x_source_admission.v0.1','status':'admitted_x_only','specification':spec,
        'numeric_original_equivalence':{'status':'unavailable','reason':'ORIGINAL_NUMERIC_AND_ROW_KEY_EQUIVALENCE_NOT_AUDITED','value':None},
        'supervised_admission':{'status':'unavailable','reason':'ORIGINAL_PHYSICAL_REFERENCE_AND_ASSAY_CLOSURE_NOT_VERIFIED','value':None},
        'test_target_accessed':False,'model_performance_used':False}
    return {**result,'admission_id':fingerprint(result)}
