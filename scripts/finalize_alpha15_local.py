"""Assemble rich confidential A–J findings and review local aggregate drafts."""
from collections import Counter
import csv
import json
from pathlib import Path

from alpha15_common import Context, read
from nirs4all_domains.disclosure import DisclosureBoundary, candidate
from nirs4all_domains.storage import atomic_json, digest, fingerprint, tree_bytes


def phase(context, name):
    return read(context.load(name+'.json')['artifact_path'])


def build(context, folder):
    cohort = phase(context, 'cohort-v2'); package = phase(context, 'synthesis-v2')
    synthesis = package['synthesis']; closure = phase(context, 'source-closure-v2')
    stability = []
    for reference in read('docs/benchmarks/alpha13/real-stability.json')['reports']:
        assert digest(reference['path']) == reference['sha256']
        stability.append({'origin': 'alpha13.revised-B60', 'source_view': reference['dataset_id'],
            'path': reference['path'], 'sha256': reference['sha256'], 'evidence': {
                k:v for k,v in read(reference['path']).items() if k in ['overall_classification','resampling_design','limitations']}})
    for source in context.old_report['source_reports']:
        if source.get('stability_execution', {}).get('status') == 'computed':
            ref = source['stability_execution'];assert digest(ref['local_path']) == ref['sha256']
            stability.append({'origin': 'alpha14.frozen-B60', 'source_view': source['dataset_id']+'/'+source['source_id'],
                'path': ref['local_path'], 'sha256': ref['sha256'], 'evidence': source.get('stability', {})})
    drafts = []
    boundary = DisclosureBoundary(context.store)
    for metric, indicator in [('pc1_fraction', 'pc1_fraction'), ('raw_snv_ari', 'partition_agreement')]:
        summary = next(d for d in synthesis['distributions'] if d['metric'] == metric and d['representation'] == 'raw')
        if summary['summary']['status'] != 'computed':continue
        draft = candidate([{'indicator': indicator, 'statistic': 'median', 'status': 'computed',
            'reason': None, 'value': summary['summary']['value']['median']}], limitations=[
                'STUDY_OVERLAP_UNRESOLVED', 'NOT_SUPERVISED_VALIDATION', 'NOT_REPRESENTATIVE_OF_NIRS'])
        # This is a rejection review: no owner publication attestation is invented.
        clearance = {'decision': 'local_only', 'candidate_sha256': fingerprint(draft),
            'reviewer_attestation': 'No new publication/participation clearance was granted.',
            'participation_approved': False, 'aggregate_fields_approved': False,
            'joint_prior_exports': [], 'small_cell_and_linkage_reviewed': False, 'source_receipts': []}
        decision = boundary.review(draft, [], clearance)
        drafts.append({'exact_private_candidate': draft, 'exact_candidate_sha256': fingerprint(draft),
            'clearance': clearance, 'decision': decision,
            'rationale': 'Source aggregate permissions and participation clearance are not established for every contributor; no safe joint-release approval exists. Existing public tables and distinctive n/p/family combinations remain linkage context.'})
    metadata = [{'view_id': row['view_id'], 'representation': row['representation'],
        'metadata_agreement': row['metadata_agreement'], 'neighbor_support': row['neighbor_support']}
        for row in synthesis['rows']]
    strong = [r for r in synthesis['relationships'] if r['association']['status'] == 'computed' and
        r['association']['value']['screens'][-1]['exceeds']]
    size_dependence = [r for r in synthesis['relationships'] if r['right'] in ['n_observations', 'n_bands']]
    invariants = {'old_hypotheses_unchanged': True, 'new_spectral_fits': 0, 'new_supervised_real_fits': 0,
        'Y_test_used_for_selection': False, 'target_cells_decoded': 0, 'TabPFN': False,
        'public_scientific_exports': 0, 'cross_source_row_position_joins': 0}
    value = {'visibility': 'local_private', 'protocol': 'domains.alpha15.confidential_report.v0.1',
        'A': {'cohort_ref': context.load('cohort-v2.json'), 'denominators': cohort['denominators'],
            'independent_study_denominator': cohort['independent_study_denominator']},
        'B': {'synthesis_ref': context.load('synthesis-v2.json'), 'figures_and_matrix': package['artifacts'], 'stability_by_original_protocol': stability},
        'C': {'strong_native_threshold_pairs': strong, 'sample_size_width_screens': size_dependence,
            'metadata_and_query_support_ref': 'Each row in B synthesis_ref contains original metadata agreement and exact query/reference support.',
            'family_associations': synthesis['family_associations'],
            'independent_study_adjustment': 'Not identifiable with unresolved overlap; no independent-study p-values or causal redundancy claims.'},
        'D': {'material_family_views': cohort['material_family_views'], 'modality_views': cohort['modality_views'],
            'known_and_possible_relationships': cohort['relations'], 'verified_population_namespaces': sorted({
                v['population']['id'] for v in cohort['views'] if v['population'].get('verified')})},
        'E': closure, 'F': {'frozen_H1_H5': 'Original alpha12/13 contracts remain preserved; no new subset or score-derived threshold.',
            'readiness': 'X-only evidence motivates hypotheses; no independent supervised confirmation or low-risk certification.',
            'limits': 'Repeated folds and component draws are not new studies. Future cross-study tests require original dependency maps, untouched retained roles and a prospective power plan.'},
        'G': {'real_pilot_executed': False, 'reason': 'Original keyed X/Y and specimen/reference/assay ownership not closed; owner budget explicitly excludes pilot.',
            'anchors': 'raw PLS components 1/2/3; nested raw Ridge .01/.1/1/10/100, component-safe native DAG selection/refit.',
            'outcomes': 'Unavailable, including D_RMSE, S and D_skill; no synthetic response substituted for real evidence.'},
        'H': {'candidates': drafts, 'new_public_exports': [], 'identity_mapping_and_key_unchanged': True},
        'I': {'resources_at_report': context.guard(), 'invariants': invariants,
            'numeric_provider': 'Methods1.3.6 ABI2.19; summary/factor/correlation public ABI; no new PCA/HDBSCAN/B60 or model fits.',
            'validation': 'Release engineering and hosted CI recorded separately after scientific report generation.'},
        'J': {'bounded_alpha16': ['Obtain original keyed spectrum/specimen/reference/assay ownership for an investigated alternative.',
            'Freeze exact development/retained population, target units, component-safe reference/stress/size-control folds and native fit count.',
            'Seek separate pilot resource approval; execute all PLS/Ridge outcomes including null/contrary responses.',
            'Reserve independent studies for future study-level confirmation with prospective power; keep TabPFN deferred.']}}
    text = ['# Alpha.15 confidential scientific report', '', 'LOCAL PRIVATE — source participation and numerical findings are not approved for publication.',
        '', '## A — Actual research cohort', '', 'Declared units and actual receipts are reconciled; restricted and incomplete cases remain in the denominator.',
        '', '| Denominator | Value |', '|---|---:|']
    text += ['| '+k+' | '+str(v)+' |' for k,v in cohort['denominators'].items()]
    text += ['', 'Independent-study denominator: '+json.dumps(cohort['independent_study_denominator']),
        'Unproven-disjoint source pairs: '+str(cohort['unknown_or_unproven_disjoint_source_pairs']),
        '', '## B — Cross-dataset structural findings', '', 'Native source-view distributions (not independent-study estimates):', '',
        '| Representation | Descriptor | Computed views | Median | Q25 | Q75 | Min | Max |', '|---|---|---:|---:|---:|---:|---:|---:|']
    for d in synthesis['distributions']:
        s = d['summary']['value'] or {}
        text.append('| '+' | '.join(map(str, [d['representation'], d['metric'], len(d['eligible_source_view_ids'])]+[s.get(k, 'unavailable') for k in ['median','q25','q75','min','max']]))+' |')
    text += ['', 'Representation response is paired within exact source view. Native change summaries and every matched raw/SNV value are retained:']
    for p in synthesis['paired_representation_changes']:
        text.append('- '+p['metric']+': '+json.dumps(p['change_summary'], ensure_ascii=False))
    text += ['', 'Standalone protected figures and matrix:']
    text += ['- ['+Path(a['path']).name+']('+a['path'].replace('\\','/')+') SHA256 '+a['sha256'] for a in package['artifacts']]
    text += ['', 'Stability evidence retains each original protocol, source/component scope, fractions, settings, pair exposure, eligible ARI support and classification; no pooling across original alpha12 and revised B60 designs.']
    for b in stability:
        text += ['- '+b['origin']+' / '+b['source_view']+' / '+b['sha256']+': '+json.dumps({k:b['evidence'][k] for k in ['overall_classification','resampling_design','limitations'] if k in b['evidence']}, ensure_ascii=False)]
    text += ['', '## C — Descriptor quality', '', 'Strong absolute-correlation threshold screens are descriptive redundancy leads. They do not supply exact r/sign or identify mechanisms.']
    for r in strong:
        text.append('- '+r['representation']+': '+r['left']+' ↔ '+r['right']+'; |r| > .95, matched source views '+str(r['association']['value']['n_source_views']))
    text += ['', 'Sample-size and spectral-width screens (constant/insufficient support stays unavailable):']
    text += ['- '+json.dumps(r, ensure_ascii=False) for r in size_dependence]
    text += ['', 'Availability/missingness is explicit for every source/descriptor. Exact effective dimension is missing when full moments are unavailable; truncated PCA values are never promoted to exact moments. Native family eta² is unadjusted for n/p and overlap. Factor semantics, cardinality, missingness and provenance remain in the companion JSON; cardinality is not physical independence.',
        '', 'Observation: descriptor spread and native threshold relationships above vary by representation and support. Confidence: exact reused profiles and native summaries, conditional on each frozen source. Consequence: redundant descriptors can be hypotheses for later validation, but cannot be combined into a universal shortcut score. Action: lock these descriptors before supervised comparisons and retain all missingness states.',
        '', '## D — Independent study diversity', '', 'Material families: '+json.dumps(cohort['material_family_views']), 'Modalities: '+json.dumps(cohort['modality_views']),
        'Verified physical namespaces: '+json.dumps(value['D']['verified_population_namespaces']),
        'Shared package/reference relationships and unresolved overlap are retained in A/D of the JSON. Views, representations and verified physical keys do not establish independent original studies.',
        '', '## E — Candidate supervised tasks', '', 'Ranking uses authorization, original conversion/manifest availability, metadata and target-unit leads, never predictive results.']
    for record in closure['investigations']:
        text += ['', '### '+record['dataset_id'], 'Admission: '+json.dumps(record['decision']),
            'Original-file/schema inspections: '+json.dumps(record['original_file_inspections'], ensure_ascii=False),
            'Canonical identity and target headers: '+json.dumps(record['headers'], ensure_ascii=False),
            'Observation/confidence/consequence/action: '+json.dumps(record['finding'], ensure_ascii=False),
            'Exact inspected document hashes: '+json.dumps(record['files'], ensure_ascii=False)]
    for section, title in [('F','H1–H5 readiness'),('G','Supervised pilot'),('H','Confidentiality and disclosure'),('I','Resources and validation'),('J','Next scientific phase')]:
        text += ['', '## '+section+' — '+title, '', '```json', json.dumps(value[section], ensure_ascii=False, indent=2), '```']
    report = folder/'CONFIDENTIAL_REPORT.md';report.write_text('\n'.join(text)+'\n', encoding='utf-8')
    value['markdown'] = {'path': str(report), 'sha256': digest(report)}
    assert tree_bytes([folder])+len(json.dumps(value).encode()) < 4*1024*1024, 'REPORT_ESSENTIAL_EVIDENCE_LIMIT'
    return value


def main():
    context = Context()
    inputs = {name: context.load(name+'.json')['artifact_sha256'] for name in ['cohort-v2', 'synthesis-v2', 'source-closure-v2']}
    inputs['controller_sha256'] = digest(__file__)
    value = context.run('report', inputs, lambda folder: build(context, folder))
    # Small signed pointer, rather than another copy of the scientific report.
    context.save('confidential-release-report.json', {'artifact_path': context.load('report.json')['artifact_path'],
        'artifact_sha256': context.load('report.json')['artifact_sha256'], 'markdown': value['markdown']})
    pointer = context.root/'CONFIDENTIAL_REPORT.md'
    pointer.write_text('# Alpha.15 confidential report\n\nFull protected A–J report: ['+Path(value['markdown']['path']).name+']('+value['markdown']['path'].replace('\\','/')+')\n', encoding='utf-8')
    print('ALPHA15_CONFIDENTIAL_A_TO_J_REPORT_COMPLETE; DISCLOSURE_DRAFTS_LOCAL_ONLY')


if __name__ == '__main__':
    try: main()
    except Exception:
        print('ALPHA15_REPORT_REFUSED; DETAILS_PROTECTED');raise SystemExit(2)
