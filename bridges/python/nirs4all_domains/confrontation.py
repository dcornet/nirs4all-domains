"""Source-closed exploratory pilot gates; existing DAG/Methods owns all fitting."""
import copy
import re
from importlib.metadata import version

from .dependence import development_rows, state, validate_folds, score_oof
from .falsification import require_pre_outcome, response
from .multifamily import compare_design, freeze_evaluation
from .predictive import native_summary
from .storage import fingerprint, digest

PROTOCOL = 'domains.confrontation.v0.1'
ANCHORS = [
    {'id': 'raw_pls', 'engine': 'methods', 'method': 'models.pls.pls_regression',
        'preprocessing': 'raw', 'grid': {'n_components': [1, 2, 3]}},
    {'id': 'raw_ridge', 'engine': 'methods', 'method': 'models.regularized.ridge',
        'preprocessing': 'raw', 'grid': {'alpha': [.01, .1, 1., 10., 100.]}}]


def dependency_map(records):
    """Verify declared original links, never infer assay/specimen identity from X."""
    require_pre_outcome(records)
    if not records or len({r['observation_id'] for r in records}) != len(records):
        raise ValueError('UNIQUE_COMPLETE_ORIGINAL_OBSERVATION_KEYS_REQUIRED')
    owners = {}
    for row in records:
        for kind in ['physical_id', 'reference_id', 'assay_event_id', 'component_id', 'partition']:
            if not isinstance(row.get(kind), str) or not row[kind]:
                raise ValueError('ORIGINAL_PHYSICAL_REFERENCE_ASSAY_COMPONENT_OWNERSHIP_REQUIRED')
        for kind in ['physical_id', 'reference_id', 'assay_event_id', 'component_id']:
            scope = row['component_id'], row['partition']
            key = kind, row[kind]
            if key in owners and owners[key] != scope:
                raise ValueError('INDIVISIBLE_ORIGINAL_DEPENDENCY_CROSSES_COMPONENT_OR_PARTITION')
            owners[key] = scope
    return {'rows': records, 'map_sha256': fingerprint(records),
        'scope': 'Verified declared links, not a guarantee that undocumented dependencies are absent.'}


def admit(evidence):
    require_pre_outcome(evidence)
    if evidence.get('analysis_authorized') is not True:
        return {'tier': 'not_admitted', 'blockers': ['LOCAL_ANALYSIS_PERMISSION_REQUIRED']}
    if evidence.get('complete_X_qualified') is not True:
        return {'tier': 'not_admitted', 'blockers': ['COMPLETE_QUALIFIED_X_REQUIRED']}
    xy_gates = ['original_keyed_XY_verified', 'target_meaning_units_verified', 'development_scope_frozen_before_target_decode']
    blockers = [key.upper()+'_REQUIRED' for key in xy_gates if evidence.get(key) is not True]
    if blockers:
        return {'tier': 'X_only_qualified', 'blockers': blockers}
    model_gates = ['original_study_verified', 'physical_specimen_ownership_verified', 'reference_assay_ownership_verified',
        'dependency_map_verified', 'component_safe_split_feasible']
    blockers = [key.upper()+'_REQUIRED' for key in model_gates if evidence.get(key) is not True]
    if blockers:
        return {'tier': 'XY_descriptive_qualified', 'blockers': blockers}
    for key in ['original_source_sha256', 'canonical_X_sha256', 'canonical_Y_sha256', 'closure_evidence_sha256']:
        if not re.fullmatch('[0-9a-f]{64}', evidence.get(key) or ''):
            raise ValueError('EXACT_ORIGINAL_SOURCE_CONTENT_AND_CLOSURE_BINDINGS_REQUIRED')
    return {'tier': 'exploratory_supervised_qualified', 'blockers': [],
        'confirmation': state(reason='ONE_STUDY_WITHOUT_INDEPENDENT_COHORT_POWER_AND_UNTOUCHED_ROLE', status='insufficient_information'),
        'source_publication_rights_used_for_scientific_admission': False}


def fit_count(frozen_evaluation):
    """Prospective grid/inner/refit count from the exact already frozen FoldSets."""
    count = 0
    for design in frozen_evaluation['inner_designs'].values():
        for inner in design.values():
            # Existing freeze stores one FoldSet per outer scope.
            count += len(inner['folds'])*8 + 2
    return count


def freeze(task, evidence, original_links, designs, hypothesis_ref, *, x_aware_full_population=False):
    decision = admit(evidence)
    if decision['tier'] != 'exploratory_supervised_qualified':
        raise ValueError('SCIENTIFIC_PILOT_ADMISSION_REQUIRED')
    if not re.fullmatch('[0-9a-f]{64}', hypothesis_ref.get('sha256') or ''):
        raise ValueError('FROZEN_H1_H5_BINDING_REQUIRED')
    linked = dependency_map(original_links)
    rows = development_rows(task)
    declared = {r['observation_id']: r for r in original_links}
    if {r['observation_id'] for r in task['observations']} != set(declared):
        raise ValueError('COMPLETE_ORIGINAL_TASK_MEMBERSHIP_REQUIRED')
    for row in task['observations']:
        original = declared[row['observation_id']]
        if (row['physical_sample_id'], row['independence_group'], row['partition']) != (
                original['physical_id'], original['component_id'], original['partition']):
            raise ValueError('ORIGINAL_TO_CANONICAL_PHYSICAL_COMPONENT_MAPPING_CHANGED')
        if row['partition'] == 'train' and row.get('metadata', {}).get('validation_component_id') != original['component_id']:
            raise ValueError('ORIGINAL_TO_CANONICAL_VALIDATION_COMPONENT_MAPPING_CHANGED')
    for folds in designs.values():
        validate_folds(rows, folds)
    if set(designs) != {'reference', 'stress', 'size_control'}:
        raise ValueError('REFERENCE_STRESS_AND_MATCHED_SIZE_CONTROL_REQUIRED')
    evaluation = freeze_evaluation(task, designs, copy.deepcopy(ANCHORS), hypothesis_ref['sha256'])
    evaluation['selection_basis'] = 'Alpha.15 source/reference closure and frozen X hypotheses; no model-response selection.'
    evaluation['low_dependence'] = state(reason='EXPLORATORY_PILOT_CANNOT_CERTIFY_LOW_STRUCTURAL_DEPENDENCE')
    evaluation['evaluation_id'] = fingerprint({k: v for k, v in evaluation.items() if k != 'evaluation_id'})
    from n4m import library_path
    providers = {key: version(key) for key in ['nirs4all-methods', 'dag-ml']}
    providers['methods_library_sha256'] = digest(library_path())
    value = {'protocol': PROTOCOL, 'visibility': 'local_private', 'source_closure': evidence, 'admission': decision,
        'dependency_map_sha256': linked['map_sha256'], 'hypothesis_ref': hypothesis_ref,
        'evaluation': evaluation, 'anchors': copy.deepcopy(ANCHORS), 'providers': providers,
        'prospective_model_fits': fit_count(evaluation), 'transductive_X_aware_split': bool(x_aware_full_population),
        'stopping_rule': 'All planned outcomes retained; stop only for registered admission/numerical/resource failure.',
        'real_execution': state(reason='SEPARATE_EXACT_OWNER_BUDGET_APPROVAL_REQUIRED'),
        'study_level_confirmation': False, 'retained_targets_select_models': False}
    value['pilot_id'] = fingerprint(value)
    return value


def execute(task, frozen, approval, library, checkpoint=None):
    current = {k: v for k, v in frozen.items() if k != 'pilot_id'}
    if fingerprint(current) != frozen['pilot_id']:
        raise ValueError('PILOT_FREEZE_DIGEST_MISMATCH')
    if approval.get('owner_approved') is not True or approval.get('pilot_id') != frozen['pilot_id'] or \
            approval.get('model_fit_upper_bound', -1) < frozen['prospective_model_fits'] or approval.get('storage_admitted') is not True:
        raise ValueError('SEPARATE_EXACT_PILOT_RESOURCE_APPROVAL_REQUIRED')
    if frozen['providers']['methods_library_sha256'] != digest(library) or any(
            version(key) != frozen['providers'][key] for key in ['nirs4all-methods', 'dag-ml']):
        raise ValueError('FROZEN_PILOT_PROVIDER_CHANGED')
    if checkpoint is None:
        if approval.get('execution_scope') != 'public_synthetic_test' or task.get('data_origin') != 'synthetic':
            raise ValueError('ATOMIC_STAGESTORE_EXECUTOR_REQUIRED_FOR_REAL_PILOT')
    # compare_design filters retained rows, checks content/spec hashes, and runs
    # the existing grouped native CV/SELECT/REFIT seam. No new numerical backend.
    outcomes = {}
    rows = {r['physical_sample_id']: r for r in development_rows(task)}
    for design in ['reference', 'stress', 'size_control']:
        outcomes[design] = {}
        for spec in frozen['anchors']:
            contract = {'task': {'task_id': frozen['pilot_id']}, 'pilot_id': frozen['pilot_id'],
                'design': design, 'specification': spec, 'providers': frozen['providers']}
            compute = lambda: compare_design(task, frozen['evaluation'], design, spec, library)
            outcomes[design][spec['id']] = checkpoint(contract, compute) if checkpoint is not None else compute()
        for result in outcomes[design].values():
            if result['status'] != 'computed':
                continue
            value = result['value']
            folds = frozen['evaluation']['outer_designs'][design]['folds']
            means = {f['fold_id']: native_summary([rows[key]['y'] for key in f['train_sample_ids']])['mean'] for f in folds}
            for observation in value['oof']:
                observation['null_prediction'] = means[observation['fold_id']]
            value['null_scores'] = score_oof(value['oof'], 'null_prediction')
            value['null_fitted_on_training_only'] = True
    contrasts = {}
    for spec in frozen['anchors']:
        def endpoint(design):
            result = outcomes[design][spec['id']]
            if result['status'] != 'computed':
                return None
            value = result['value']
            return {'target_definition': task['context']['target_id'], 'target_unit': task['target_unit'],
                'evaluation_ids': [r['physical_sample_id'] for r in value['oof']],
                'rmse': value['scores']['value']['rmse']['value'],
                'null_rmse': value['null_scores']['value']['rmse']['value'],
                'metrics_from_native_provider': True, 'null_fitted_on_training_only': True}
        reference, stress = endpoint('reference'), endpoint('stress')
        contrasts[spec['id']] = response(reference, stress) if reference is not None and stress is not None else state(reason='SCHEDULED_NATIVE_MODEL_OUTCOME_UNAVAILABLE')
    return {'pilot_id': frozen['pilot_id'], 'visibility': 'local_private', 'outcomes': outcomes,
        'matched_contrasts': contrasts,
        'scope': 'One exploratory original study, not study-level H1–H5 confirmation.',
        'contrary_and_null_outcomes_retained': True}
