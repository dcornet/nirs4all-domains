"""Study-role isolation and locked response semantics; no estimator implementation."""
import math
import re
from itertools import combinations
from .dependence import state
from .storage import fingerprint

FORBIDDEN={'Y_test','y_test','y','Y','rmse','predictions','model_scores','future_scores','supervised_outcomes'}
DISCOVERY={'study:ecosis-ca2023','study:perten','study:litter-2024'}


def require_pre_outcome(value):
    if isinstance(value,dict):
        for key,item in value.items():
            if key in FORBIDDEN:raise ValueError('OUTCOME_INPUT_FORBIDDEN_IN_DESCRIPTOR_OR_COHORT_FREEZE')
            require_pre_outcome(item)
    elif isinstance(value,list):
        for item in value:require_pre_outcome(item)
    elif isinstance(value,float) and not math.isfinite(value):raise ValueError('NONFINITE_PREREGISTRATION_VALUE')


def freeze_roles(records,relations):
    require_pre_outcome(records);require_pre_outcome(relations)
    for r in records:
        if any(not isinstance(r.get(k),str) or not r[k].strip() for k in ['source_id','original_study_id','population_namespace']):
            raise ValueError('NONEMPTY_DECLARED_STUDY_POPULATION_SOURCE_IDENTITIES_REQUIRED')
    by_id={r['source_id']:r for r in records}
    if len(by_id)!=len(records):raise ValueError('DUPLICATE_SOURCE_ROLE_IDENTITY')
    studies={};populations={}
    for r in records:
        study=r['original_study_id'];role=r['role'];population=r['population_namespace']
        if role not in ['discovery','potential_confirmation','confirmation','unavailable']:raise ValueError('UNKNOWN_STUDY_ROLE')
        if study in DISCOVERY and role in ['potential_confirmation','confirmation']:raise ValueError('HISTORICAL_DISCOVERY_CANNOT_BECOME_UNTOUCHED_CONFIRMATION')
        if role=='confirmation' and not all(r.get(k) is True for k in ['original_study_verified','physical_reference_closure_verified','untouched_outcomes','exact_task_and_splits_frozen']):
            raise ValueError('CONFIRMATION_ADMISSION_GATE_NOT_MET')
        if study in studies and studies[study]!=role:raise ValueError('STUDY_SPLIT_ACROSS_DISCOVERY_AND_CONFIRMATION')
        if population in populations and populations[population]!=role:raise ValueError('SHARED_POPULATION_SPLIT_ACROSS_ROLES')
        studies[study]=role;populations[population]=role
    by_pair={}
    for relation in relations:
        ids=relation.get('source_ids')
        if not isinstance(ids,list) or len(ids)!=2 or any(not isinstance(s,str) or s not in by_id for s in ids) or ids[0]==ids[1]:
            raise ValueError('DECLARED_DISTINCT_SOURCE_PAIR_REQUIRED')
        if relation.get('overlap') not in ['verified_shared','unknown_possible','verified_disjoint']:
            raise ValueError('UNKNOWN_SOURCE_OVERLAP_STATE')
        pair=frozenset(ids)
        if pair in by_pair:raise ValueError('DUPLICATE_SOURCE_OVERLAP_RELATION')
        by_pair[pair]=relation
        left,right=(by_id[s] for s in ids)
        if relation['overlap'] in ['verified_shared','unknown_possible'] and left['role']!=right['role']:
            raise ValueError('UNRESOLVED_OR_SHARED_SOURCE_OVERLAP_CROSSES_ROLES')
        if relation['overlap']=='verified_disjoint' and not re.fullmatch('[0-9a-f]{64}',relation.get('evidence_sha256') or ''):
            raise ValueError('DISJOINTNESS_REQUIRES_INDEPENDENT_EVIDENCE')
    for left,right in combinations(records,2):
        roles={left['role'],right['role']}
        separated_roles='discovery' in roles and bool(roles & {'potential_confirmation','confirmation'})
        distinct_confirmation=left['original_study_id']!=right['original_study_id'] and 'confirmation' in roles
        if separated_roles or distinct_confirmation:
            relation=by_pair.get(frozenset([left['source_id'],right['source_id']]))
            if left['population_namespace']==right['population_namespace'] or not relation or relation['overlap']!='verified_disjoint':
                raise ValueError('UNRESOLVED_OR_SHARED_SOURCE_OVERLAP_PREVENTS_INDEPENDENT_ROLES')
    value={'protocol_version':'domains.falsification.v0.1','records':records,'relations':relations,
        'independent_confirmation_studies':len({r['original_study_id'] for r in records if r['role']=='confirmation'}),
        'scope':'Original studies/populations, never row/fold/target counts; potential roles are not admissions.'}
    value['cohort_id']=fingerprint(value);return value


def response(reference,stress):
    if any(reference[k]!=stress[k] for k in ['target_definition','target_unit']):raise ValueError('MATCHED_TARGET_DEFINITION_AND_UNIT_REQUIRED')
    for value in [reference,stress]:
        if not isinstance(value.get('evaluation_ids'),list) or not value['evaluation_ids'] or any(not isinstance(s,str) or not s.strip() for s in value['evaluation_ids']):
            raise ValueError('NONEMPTY_DECLARED_EVALUATION_IDENTITIES_REQUIRED')
    if len(set(reference['evaluation_ids']))!=len(reference['evaluation_ids']) or len(set(stress['evaluation_ids']))!=len(stress['evaluation_ids']):
        raise ValueError('UNIQUE_EVALUATION_IDENTITIES_REQUIRED')
    if set(reference['evaluation_ids'])!=set(stress['evaluation_ids']):
        return state(reason='UNMATCHED_EVALUATION_POPULATIONS; NO_PURE_STRUCTURAL_TREATMENT_CONTRAST',status='inconclusive')
    for value in [reference,stress]:
        if value.get('metrics_from_native_provider') is not True or value.get('null_fitted_on_training_only') is not True:raise ValueError('NATIVE_METRICS_AND_TRAINING_ONLY_NULL_REQUIRED')
        if not isinstance(value['rmse'],(int,float)) or isinstance(value['rmse'],bool) or not math.isfinite(value['rmse']) or value['rmse']<0:raise ValueError('FINITE_NONNEGATIVE_RMSE_REQUIRED')
    def skill(v):
        null=v['null_rmse']
        if not isinstance(null,(int,float)) or isinstance(null,bool) or not math.isfinite(null) or null<=0:
            return state(reason='ZERO_OR_UNDEFINED_NULL_DENOMINATOR')
        result=1-v['rmse']/null
        return state(result) if math.isfinite(result) else state(reason='NONFINITE_RELATIVE_SKILL')
    a,b=skill(reference),skill(stress)
    return state({'d_rmse':stress['rmse']-reference['rmse'],'reference_skill':a,'stress_skill':b,
        'd_skill':state(b['value']-a['value']) if a['status']==b['status']=='computed' else state(reason='NULL_RELATIVE_SKILL_UNAVAILABLE'),
        'target_unit':reference['target_unit'],'n_matched_evaluation_ids':len(reference['evaluation_ids']),
        'causal_shortcut_fraction':state(reason='NOT_IDENTIFIED_BY_STRUCTURAL_STRESS'),
        'study_level_hypothesis_verdict':state(reason='ONE_PAIRED_TASK_IS_NOT_INDEPENDENT_STUDY_CONFIRMATION',status='insufficient_information')})


def retain_evidence(cohort,observations,expected_observation_ids=None):
    allowed={r['source_id'] for r in cohort['records']};seen=set()
    for r in observations:
        if r['source_id'] not in allowed or r['observation_id'] in seen:raise ValueError('OUTCOME_OUTSIDE_FROZEN_COHORT_OR_DUPLICATED')
        seen.add(r['observation_id'])
    if expected_observation_ids is not None:
        if len(set(expected_observation_ids))!=len(expected_observation_ids) or set(expected_observation_ids)!=seen:
            raise ValueError('SCHEDULED_OUTCOME_ROSTER_MISMATCH')
    completeness=state({'observations':len(seen)}) if expected_observation_ids is not None else state(reason='FROZEN_OBSERVATION_ROSTER_NOT_PROVIDED')
    return {'cohort_id':cohort['cohort_id'],'observations':observations,
        'scheduled_completeness':completeness,'selection_uses_outcomes':False,
        'scope':'All supplied observations retained regardless of sign; planned completeness requires an exact frozen observation roster.'}
