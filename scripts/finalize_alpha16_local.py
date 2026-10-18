"""Render protected source-specific requests and a separate A-J research report."""
import base64
import copy
from importlib.metadata import version
from pathlib import Path

from alpha16_common import Context
from nirs4all_domains.dependence import state
from nirs4all_domains.storage import digest, fingerprint
from nirs4all_domains.original_source import manifest_file
from run_alpha16_source_resolution import inspect_original


def reconcile_original_bindings(context, resolution):
    """Read-only metadata reconciliation of already budgeted, frozen inputs.

    Preserve the initial strict-codec receipts. Recognize the explicitly tagged
    full SHA256 notation; do not promote partial hashes or infer ownership.
    Evidence is included in the approved integrated-report allocation. No new
    candidate-stage reservation, numeric experiment or target decode occurs.
    """
    records = copy.deepcopy(resolution['investigations'])
    for candidate in records:
        for original in candidate['original_bindings']:
            if original.get('reason') != 'DECLARED_FULL_ORIGINAL_CONTENT_HASH_REQUIRED':
                continue
            row = original['manifest_row']
            try:
                path = manifest_file(row, candidate['dataset_id'], [Path(context.cfg['source_root']).parent])
                frozen = context.inputs[str(path.resolve())]
                assert frozen['sha256'] == digest(path), 'ORIGINAL_FROZEN_INPUT_CHANGED'
                original['binding_reconciliation'] = {'status': 'bound', 'inspection': inspect_original(path),
                    'codec': 'Explicit sha256: prefix with complete SHA256; exact digest agrees with the previously frozen participating input.',
                    'physical_assay_independence_inferred': False}
            except (ValueError, KeyError, OSError) as exc:
                original['binding_reconciliation'] = {'status': 'unavailable', 'reason': str(exc)}
        bound = [item for item in candidate['original_bindings'] if item.get('status') == 'bound' or
            item.get('binding_reconciliation', {}).get('status') == 'bound']
        for request in candidate['requests']:
            request['local_original_availability'] = 'verified_declared_bytes_available' if bound else 'not_verified_at_declared_locators'
            request['obtainable_from_current_inspected_evidence'] = 'not_yet_verified; metadata/schema leads are not ownership contracts'
            if request['relationship'] == 'source_original' and bound:
                request['relationship'] = 'original_to_canonical_conversion_contract'
                request['evidence_required'] = 'The original bytes are present and content-bound. Supply or qualify the exact observation-key/axis/reference mapping to the canonical representation; a missing converter is needed only if that canonical correspondence depends on it. A documented original-only task can instead use a separately qualified adapter.'
                request['next_action'] = 'Use the content-bound original and inspected schema to identify the declared observation/specimen/reference fields and units; obtain original field semantics or a source-owner crosswalk before numeric Y. Do not request another copy of these existing bytes.'
        candidate['binding_reconciliation_scope'] = 'Preserved original locator receipts plus read-only schema/header reconciliation of already frozen files under the integrated-report allocation; no new target decode or model experiment.'
    return records


def report(context, folder):
    resolution = context.load('source-resolution.json')
    records = reconcile_original_bindings(context, resolution)
    requests = []
    for candidate in records:
        requests.append('## '+candidate['dataset_id'])
        requests.append('Prior evidence receipt: `'+str(candidate['prior_receipt'])+'`.')
        requests.append('### Original files and exact locator results')
        for original in candidate['original_bindings']:
            row = original['manifest_row']
            requests.append('- Declared original: `'+row.get('local_path_if_any', '')+'`; source: '+row.get('source_path_or_url', '')+'.')
            requests.append('  Inspection: '+original.get('reason', original.get('inspection', {}).get('scope', 'unavailable'))+'.')
            if 'binding_reconciliation' in original:
                import json
                requests.append('  Preserved initial result reconciled against the full tagged digest and already frozen input: '+json.dumps(original['binding_reconciliation'], ensure_ascii=False)+'.')
        for driver in candidate['driver_resolution']:
            requests.append('- Delegated converter: `'+str(driver['declared_path'])+'`; present: '+str(driver['exists'])+'; never executed.')
        requests.append('### Documents inspected')
        for item in candidate['documents']:
            requests.append('- `'+item['path']+'`, SHA256 `'+item['sha256']+'`.')
        requests.append('### Tier-specific remaining evidence and next action')
        for request in candidate['requests']:
            requests.append('- **'+request['relationship']+'**: '+request['evidence_required'])
            requests.append('  Current inspected evidence does not verify this link. '+request['next_action'])
        requests.append('### Admission scope')
        requests.append('Existing decision: `'+candidate['admission']['tier']+'`. Original correspondence, physical ownership and assay ownership are separate claims. This bounded inspection does not establish absence of evidence elsewhere.')
        requests.append('The first request is the current actionable bottleneck; later crosswalk/ownership requests are conditional prerequisites, not claims that those fields are absent from uninspected originals.')
        requests.append('No numeric target was decoded, no retained target was accessed and no model was fitted. Stop unchanged searches; reopen only on newly supplied original evidence.')
    request_path = folder/'UNRESOLVED_SOURCE_REQUESTS.md'
    request_path.write_text('# Confidential original-reference requests — alpha.16\n\n'+'\n\n'.join(requests)+'\n', encoding='utf-8')
    why = 'ORIGINAL_KEYED_REFERENCE_UNIT_SCOPE_AND_DEPENDENCY_CHAIN_NOT_VERIFIED; SEPARATE_REAL_PILOT_APPROVAL_NOT_GRANTED'
    outcomes = {name: state(reason=why) for name in ['D_RMSE', 'S_reference', 'S_stress', 'D_skill']}
    value = {
        'visibility': 'local_private', 'protocol': 'domains.alpha16.original_reference.v0.1',
        'A': {'candidate_receipt': fingerprint(resolution), 'investigations': records,
            'pre_outcome_selection': True, 'source_names_and_counts_public': False},
        'B': {'numeric_XY_correspondence': state(reason='ORIGINAL_KEYED_TARGET_ACCESS_CONTRACT_NOT_VERIFIED'),
            'numeric_target_cells_decoded': 0, 'no_positional_equivalence': True},
        'C': {'dependency_ownership': state(reason='SOURCE_ORIGINAL_PHYSICAL_REFERENCE_ASSAY_CHAIN_NOT_VERIFIED'),
            'unique_observations_do_not_supply_independence': True},
        'D': {'exact_real_task': state(reason='SOURCE_REFERENCE_ADMISSION_NOT_COMPLETE'),
            'tier_distinctions': ['X_only', 'development_only_XY', 'exploratory_supervised', 'independent_confirmation']},
        'E': {'exact_real_folds': state(reason='COMPONENT_MEMBERSHIP_AND_ORIGINAL_STRESS_CONTEXT_REQUIRED'),
            'conditional_executable_protocol': 'nirs4all_domains.confrontation.freeze/execute; existing native grouped inner selection/refit, matched evaluation and size_match.exact_training_subset.',
            'prospective_fits': state(reason='NO_ADMITTED_EXACT_REAL_FOLDS; NO_NUMERIC_BUDGET_INVENTED')},
        'F': {'H1_H5_changed': False, 'outcome_formulas_changed': False,
            'bindings': {str(p): digest(p) for p in [Path('docs/ALPHA12_HYPOTHESIS_REGISTER.md'), Path('docs/ALPHA12_FUTURE_OUTCOME_CONTRACT.md')]},
            'study_confirmation': state(reason='ONE_EXPLORATORY_TASK_CANNOT_CONFIRM_ACROSS_STUDIES')},
        'G': {'real_pilot_executed': False, 'real_supervised_fits': 0, 'outcomes': outcomes,
            'separate_owner_permission': state(reason='EXACT_SOURCE_TASK_FOLDS_AND_RESOURCES_REQUIRED_BEFORE_PILOT_REQUEST')},
        'H': {'new_public_scientific_exports': 0, 'private_OOF_in_public_artifacts': False,
            'rights_and_disclosure_framework_unchanged': True},
        'I': {'resources': context.guard(), 'historical_cleanup_or_migration': False,
            'new_PCA_HDBSCAN_B60_campaigns': 0, 'TabPFN_execution_or_installation': False,
            'source_request_document': {'path': str(request_path), 'sha256': digest(request_path)},
            'providers_during_source_resolution': {p: version(p) for p in ['nirs4all-methods', 'dag-ml', 'nirs4all-datasets', 'nirs4all-domains-bridge']}},
        'J': {'next_action': 'Supply the source-specific original evidence in the linked requests. Verify original keyed X/Y, units and target scope; close physical/assay ownership; freeze exact reference/stress/size controls and native fit count, then request separate owner approval. Accumulate independent study evidence only after that first admissible task.'}}
    lines = ['# Confidential alpha.16 A–J report', '', 'Source-specific evidence is private; no publication permission is implied.', '',
        '[Exact source-owner requests](UNRESOLVED_SOURCE_REQUESTS.md)', '']
    titles = ['Source candidates examined', 'Original X/Y correspondence', 'Physical/reference dependencies', 'Admitted task',
        'Frozen evaluation', 'H1–H5 readiness', 'Actual supervised experiment', 'Privacy and disclosure', 'Resources and verification', 'Next phase']
    import json
    for letter, title in zip('ABCDEFGHIJ', titles, strict=True):
        lines.extend(['## '+letter+' — '+title, '', '```json', json.dumps(value[letter], indent=2, ensure_ascii=False), '```', ''])
    path = folder/'CONFIDENTIAL_REPORT.md'
    path.write_text('\n'.join(lines), encoding='utf-8')
    value['markdown'] = {'path': str(path), 'sha256': digest(path)}
    return value


def main():
    context = Context()
    resolution = context.load('source-resolution.json')
    result = context.run('report', 'integrated-report', {'resolution': fingerprint(resolution), 'format': 'A-J-v1'},
        lambda folder: report(context, folder), reserve=4194304)
    for name, source in [('CONFIDENTIAL_REPORT.md', result['markdown']['path']),
                         ('UNRESOLVED_SOURCE_REQUESTS.md', result['I']['source_request_document']['path'])]:
        (context.root/name).write_bytes(Path(source).read_bytes())
    # Source-owner request clarification uses completed receipts and file stats;
    # it is reporting within the existing integrated allocation, not a new
    # candidate stage, reservation or numeric experiment. Keep stage bytes intact.
    findings = []
    for candidate in result['A']['investigations']:
        originals = []
        for original in candidate['original_bindings']:
            row = original['manifest_row']; locator = row.get('local_path_if_any')
            path = Path(locator) if locator else None
            present = bool(path and path.is_file())
            originals.append({'declared_path': locator, 'present_at_declared_path': present,
                'whole_file_bytes': path.stat().st_size if present else None,
                'participating_input_frozen': bool(present and str(path.resolve()) in context.inputs),
                'original_binding': original.get('binding_reconciliation', original)})
        available = any(item['original_binding'].get('status') == 'bound' for item in originals)
        unadmitted = any(item['present_at_declared_path'] and not item['participating_input_frozen'] for item in originals)
        if available:
            action = 'Original bytes are already present and content-bound. Supply the original field semantics/crosswalk identifying observation -> specimen -> reference/assay, target definition/units and source partition scope. Use the exact inspected schema in the linked report. Do not supply another copy of these files.'
        elif unadmitted:
            action = 'A declared original is present but has not passed the participating-input guard. Review the exact full-file bytes and refusal reason below before further access; source absence and a request for another copy would be incorrect. Original field/ownership semantics are still separately required.'
        else:
            action = 'Supply the exact declared original or a documented corrected local locator/source binding, followed by the observation/reference/assay crosswalk and target-unit/access contract. Do not regenerate identifiers from row positions.'
        findings.append({'dataset_id': candidate['dataset_id'], 'originals': originals,
            'observation': 'Exact original locators/content and selective schema evidence are reconciled separately from canonical identities. The original reference/units/access/dependency contract remains unverified.',
            'confidence': 'Bounded declared-file and schema inspection; not a claim that required evidence does not exist elsewhere.',
            'consequence': candidate['admission'], 'action': action,
            'source_owner_clarification': 'Original experimental identities/ownership and units need original documentation or owner clarification; a content checksum alone cannot supply them.'})
    annotation = {'visibility': 'local_private', 'findings': findings,
        'reporting_controller_sha256': digest(__file__),
        'original_report_receipt': context.load('report.json')['artifact_sha256'],
        'scope': 'Request clarification from existing receipts and file metadata. Initial strict-codec records remain immutable; tagged full SHA256 is reconciled, never partial hashes. The frozen pre-outcome roster is retained; no retrospective reselection or new scientific execution.',
        'ranking_limit': 'The initial availability ranking treated tagged digests conservatively. The current codec accepts sha256: notation; the executed roster and its actual archived rule remain unchanged. No global catalog-exhaustion or best-source claim follows.',
        'new_target_cells_or_model_fits': 0}
    context.save('report-scope-annotation.json', annotation)
    owner_lines = ['# Current source-owner actions — alpha.16', '',
        'These requests use the verified local availability and reconciled original bindings. Earlier stage reports remain preserved; no numeric target or model experiment is added.', '']
    for finding in findings:
        owner_lines.extend(['## '+finding['dataset_id'], '', finding['action'], '',
            '**Confidence:** '+finding['confidence'], '', '**Exact declared originals:**', ''])
        for original in finding['originals']:
            owner_lines.append('- `'+str(original['declared_path'])+'`: present='+str(original['present_at_declared_path'])+
                ', full bytes='+str(original['whole_file_bytes'])+', participating input frozen='+str(original['participating_input_frozen'])+'.')
        owner_lines.extend(['', 'The original inspected field/member schema and document hashes are in [the detailed requests](UNRESOLVED_SOURCE_REQUESTS.md); the observation/confidence/consequence/action records are in [the signed annotation](report-scope-annotation.json).', ''])
    (context.root/'OWNER_NEXT_ACTIONS.md').write_text('\n'.join(owner_lines), encoding='utf-8')
    for name in ['CONFIDENTIAL_REPORT.md', 'UNRESOLVED_SOURCE_REQUESTS.md']:
        path = context.root/name
        text = path.read_text(encoding='utf-8')
        path.write_text('Current actionable summary: [source-owner next actions](OWNER_NEXT_ACTIONS.md).\n\n'+text, encoding='utf-8')
        with path.open('a', encoding='utf-8') as stream:
            stream.write('\n\nCurrent source-owner action and verified local availability: [signed reporting clarification](report-scope-annotation.json). This distinguishes existing bytes, input-budget refusals and genuinely missing locators; it preserves the original stage report.\n')
    sources = ['scripts/alpha16_common.py', 'scripts/run_alpha16_source_resolution.py',
        'scripts/finalize_alpha16_local.py', 'bridges/python/nirs4all_domains/original_source.py']
    # Archive the actual file-based controller revision before engineering changes.
    if not (context.root/'executed-source-snapshot.json').exists():
        context.save('executed-source-snapshot.json', {'sources': {p: {'sha256': digest(p),
            'base64': base64.b64encode(Path(p).read_bytes()).decode()} for p in sources},
            'bridge_metadata_during_science': version('nirs4all-domains-bridge'),
            'locator_bootstrap_scope': 'Initial locator-only receipts were made by a stdin bootstrap using the same manifest/delegated-driver projection. File-based reference and shortlist/report execution are archived here; no original numeric X/Y or model execution is attributed to that bootstrap.'})
    context.guard()
    print('ALPHA16_CONFIDENTIAL_REPORT_AND_OWNER_REQUESTS_WRITTEN; NO_REAL_PILOT')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        try:
            Context().save('report-failure.json', {'type': type(exc).__name__, 'detail': str(exc)})
        except Exception:
            pass
        print('ALPHA16_REPORT_REFUSED; DETAILS_PROTECTED')
        raise SystemExit(2) from None
