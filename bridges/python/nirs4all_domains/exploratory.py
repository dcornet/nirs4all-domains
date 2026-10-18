"""Evidence-tier decisions for observation CV; no independence or fit implied."""
import re

from .falsification import require_pre_outcome

PROTOCOL = 'domains.exploratory.admission.v0.1'


def admit(evidence):
    require_pre_outcome(evidence)
    result = {'protocol': PROTOCOL, 'tier': 'not_admitted', 'blockers': [],
              'evaluation_scope': None, 'independent_generalization': False,
              'real_fitting_authorized': False}
    for field in ['analysis_authorized', 'complete_X_qualified']:
        if evidence.get(field) is not True:
            result['blockers'].append(field.upper()+'_REQUIRED')
    if result['blockers']:
        return result
    result['tier'] = 'X_only_observation_description'
    for field in ['canonical_keyed_XY_verified', 'canonical_quantitative_target_declared',
                  'development_scope_frozen_before_target_decode', 'retained_targets_sealed']:
        if evidence.get(field) is not True:
            result['blockers'].append(field.upper()+'_REQUIRED')
    if evidence.get('target_unit_status') not in ['documented', 'unspecified_canonical_units']:
        result['blockers'].append('EXPLICIT_TARGET_UNIT_STATUS_REQUIRED')
    for field in ['canonical_X_sha256', 'canonical_Y_sha256', 'mapping_evidence_sha256']:
        value = evidence.get(field)
        if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
            result['blockers'].append(field.upper()+'_REQUIRED')
    if result['blockers']:
        return result
    result['tier'] = 'exploratory_XY'
    known = evidence.get('known_dependencies_exist')
    verified = evidence.get('complete_verified_groups') is True
    if known not in [True, False, None] or (known is not None and type(known) is not bool):
        raise ValueError('DEPENDENCY_EVIDENCE_MUST_BE_BOOLEAN_OR_UNKNOWN')
    if evidence.get('verified_dependency_links_present') is True and evidence.get('known_links_preserved') is not True:
        result['blockers'] = ['VERIFIED_DEPENDENCY_LINKS_MUST_REMAIN_INDIVISIBLE']
        return result
    result['tier'] = 'exploratory_supervised_eligible'
    result['evaluation_scope'] = 'verified_group_CV' if verified else 'observation_CV_potentially_optimistic'
    result['physical_assay_independence'] = 'not_established'
    result['target_unit_status'] = evidence['target_unit_status']
    result['cross_dataset_absolute_error_comparison'] = False
    result['unresolved_dependency_risk'] = known is not False and not verified
    return result
