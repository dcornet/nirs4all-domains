"""Scientific reuse of complete-source profiles; ordinary source-permitted aggregates."""
from collections import Counter
from itertools import combinations
from pathlib import Path
import json

from alpha17_common import Context, read
from nirs4all_domains.synthesis import PRIMARY, summarize, threshold_association, validate_states
from nirs4all_domains.storage import atomic_json, digest


METRICS = ['pc1_fraction', 'pc5_fraction', 'retained_variance_fraction', 'effective_dimension',
           'clusters_8', 'noise_8', 'nn_median', 'neighbor_cv', 'proximity_0.01',
           'raw_snv_ari', 'raw_snv_overlap']
PAIRS = [('pc1_fraction', 'proximity_0.01'), ('pc1_fraction', 'raw_snv_ari'),
         ('proximity_0.01', 'raw_snv_ari')]


def compare(rows):
    """Prespecified native summaries and family sensitivity, no spectral refits."""
    distributions, paired, sensitivity, associations = [], [], [], []
    for rep in ['raw', 'snv']:
        current = [r for r in rows if r['representation'] == rep]
        for metric in METRICS:
            eligible = [r for r in current if r['metrics'][metric]['status'] == 'computed']
            distributions.append({'representation': rep, 'metric': metric,
                'total_views': len(current), 'computed_views': len(eligible),
                'missing_reasons': dict(Counter(r['metrics'][metric]['reason'] for r in current if r not in eligible)),
                'summary': summarize([r['metrics'][metric]['value'] for r in eligible])})
        if rep == 'raw':
            for family in sorted({r['family'] for r in current}):
                selected = [r for r in current if r['family'] != family]
                for metric in ['pc1_fraction', 'proximity_0.01', 'raw_snv_ari']:
                    values = [r['metrics'][metric]['value'] for r in selected if r['metrics'][metric]['status'] == 'computed']
                    sensitivity.append({'excluded_catalog_family': family, 'metric': metric,
                        'remaining_views': len(selected), 'computed_views': len(values), 'summary': summarize(values)})
            for left, right in PAIRS:
                eligible = [r for r in current if all(r['metrics'][k]['status'] == 'computed' for k in [left,right])]
                result = threshold_association([r['metrics'][left]['value'] for r in eligible],
                    [r['metrics'][right]['value'] for r in eligible], [r['view_id'] for r in eligible])
                if result['status'] == 'computed':
                    # Membership remains in the local provenance, not in aggregate output.
                    result['value'].pop('source_view_ids')
                associations.append({'left': left, 'right': right, 'association': result})
    by = {(r['view_id'],r['representation']):r for r in rows}
    for metric in METRICS:
        ids = sorted({r['view_id'] for r in rows if all((r['view_id'],rep) in by and
            by[r['view_id'],rep]['metrics'][metric]['status'] == 'computed' for rep in ['raw','snv'])})
        delta = [by[k,'snv']['metrics'][metric]['value']-by[k,'raw']['metrics'][metric]['value'] for k in ids]
        paired.append({'metric': metric, 'matched_views': len(ids), 'SNV_minus_raw': summarize(delta)})
    result = {'distributions': distributions, 'paired_representation_changes': paired,
        'leave_one_catalog_family_out': sensitivity, 'native_abs_Pearson_screens': associations}
    validate_states(result)
    return result


def build(context, folder):
    audit = context.auth(context.store.root/'screening-rights-reviewed.json', 'audit')
    cohort = context.phase('cohort-v2')
    synthesis = context.phase('synthesis-v2')['synthesis']
    rows = synthesis['rows']
    catalog = {e['dataset_id']:e for e in audit['entries']}
    views = {v['view_id']:v for v in cohort['views']}
    for row in rows:
        assert catalog[views[row['view_id']]['catalog_id']]['access_analysis_eligible'] is True
    permitted = []
    for row in rows:
        entry = catalog[views[row['view_id']]['catalog_id']]
        permission = entry['permissions']['publish_aggregates']
        # Existing source-backed grants are sufficient for ordinary statistics.
        # No catalog-tier veto, renewed owner byte approval or suppression rule.
        if permission['status'] == 'allowed' and permission['evidence_receipts']:
            permitted.append(row)
    private = {'protocol': 'domains.alpha17.existing_bank_science.v0.1',
        'all_authorized_rows': rows, 'all_authorized_comparison': compare(rows),
        'source_permission_ledger': [{'view_id':key,'permissions':catalog[v['catalog_id']]['permissions'],
            'permission_basis':catalog[v['catalog_id']]['permission_basis']} for key,v in views.items()],
        'public_contributing_views': sorted({r['view_id'] for r in permitted}),
        'source_evidence': {'cohort': context.auth(context.store.root/'alpha15/cohort-v2.json'),
            'synthesis': context.auth(context.store.root/'alpha15/synthesis-v2.json')},
        'new_spectral_fits': 0, 'new_real_model_fits': 0}
    public = {'protocol': private['protocol'], 'scope': 'Source-view descriptive analysis; ordinary source-permitted aggregates.',
        'coverage': {'catalog_entries': len(audit['entries']),
            'locally_authorized_entries': sum(e['access_analysis_eligible'] for e in audit['entries']),
            'existing_characterized_views': len({r['view_id'] for r in rows}),
            'aggregate_permission_covered_views': len({r['view_id'] for r in permitted}),
            'published_raw_and_SNV_rows': len(permitted)},
        'comparison': compare(permitted),
        'limitations': ['Source views are not independent studies; population overlap remains unresolved.',
            'Coverage is incomplete and publication-permitted coverage is a subset of local analysis.',
            'Catalog family labels are unverified and can be erroneous; family sensitivity is descriptive.',
            'Equal source-view weights do not correct study multiplicity or convenience sampling.',
            'Native correlation filters supply absolute-threshold decisions, not signed coefficients or p-values.',
            'X geometry alone cannot demonstrate shortcuts or predict a universal leakage probability.',
            'No numeric target access, spectral refit or new real supervised fit.'],
        'H1_H5_changed': False, 'new_real_model_fits': 0, 'new_spectral_fits': 0}
    validate_states(public)
    atomic_json(folder/'ordinary-aggregates.json', public)
    private['public_candidate'] = {'path': str(folder/'ordinary-aggregates.json'), 'sha256': digest(folder/'ordinary-aggregates.json')}
    # Reuse the existing exact owner requests once; no further source search.
    old = context.store.root/'alpha16/OWNER_NEXT_ACTIONS.md'
    owner = context.root/'OWNER_DECISION_PACKET.md'
    owner.write_text('# Alpha.17 owner decision packet\n\nNo new original crosswalk or owner clarification received. '
        'Stop unchanged source investigations. The following existing requests limit stronger claims, not exploratory observation analysis.\n\n'
        +old.read_text(encoding='utf-8')+'\n\n## Current decision\n\n'
        'Use all authorized existing X profiles locally; publish ordinary aggregates covered by source permission. '
        'Unknown physical/assay ownership remains unknown. Canonical keyed XY may support explicitly optimistic observation CV. '
        'Known dependency groups must be mapped and kept whole. No external message authorized or sent. '
        'No real-fit authorization yet. See the bounded computational proposal before execution.\n', encoding='utf-8')
    return private


def main():
    context = Context()
    result = context.run('science', lambda folder: build(context, folder))
    candidate = result['public_candidate']
    assert digest(candidate['path']) == candidate['sha256']
    # Only the aggregate candidate generated from existing allowed source grants.
    public = read(candidate['path'])
    atomic_json('docs/benchmarks/alpha17/structural-summary.json', public)
    context.preservation()
    print('ALPHA17_EXISTING_BANK_SCIENCE_COMPLETE; NO_NEW_REAL_FITS')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('ALPHA17_SCIENCE_REFUSED; DETAILS_REMAIN_LOCAL')
        raise SystemExit(2) from None
