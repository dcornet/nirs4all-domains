"""Human-readable scientific handoff from the already computed local evidence."""
from pathlib import Path

from alpha17_common import Context,read


def cell(value):
    return format(value['value'],'.5g') if value['status']=='computed' else 'unavailable: '+value['reason']


def main():
    c=Context();pointer=c.load('science.json');science=read(pointer['artifact_path'])
    lines=['# Alpha.17 confidential scientific report','',
        'The owner amended the priority to scientific bank coverage and permitted ordinary aggregates. '
        'No new original evidence was received; unchanged owner investigations stop.',
        '', '## Existing complete-source views', '',
        '| Source view | Representation | Catalog family | n | p | PC1 fraction | Clusters | Noise | Raw/SNV ARI |',
        '|---|---|---|---:|---:|---:|---:|---:|---:|']
    for r in sorted(science['all_authorized_rows'],key=lambda x:(x['view_id'],x['representation'])):
        lines.append('| '+' | '.join([r['view_id'],r['representation'],r['family'],str(r['n_observations']),str(r['n_bands'])]
            +[cell(r['metrics'][k]) for k in ['pc1_fraction','clusters_8','noise_8','raw_snv_ari']])+' |')
    lines+=['','## Native distribution summaries','',
        'All local authorized views participate below; these are source views, not independent populations. '
        'Publication of the public subset follows established source permissions. The catalog private label alone is not a restriction.','',
        '| Representation | Metric | Computed views | Median | IQR |','|---|---|---:|---:|---|']
    for r in science['all_authorized_comparison']['distributions']:
        if r['summary']['status']=='computed':
            s=r['summary']['value'];lines.append(f"| {r['representation']} | {r['metric']} | {r['computed_views']} | {s['median']:.5g} | {s['q25']:.5g} – {s['q75']:.5g} |")
    lines+=['','## Interpretation and next action','',
        'Observation: descriptors and their raw/SNV changes vary across source views. Confidence: descriptive, '
        'with exact per-metric missingness in the authenticated science artifact. Consequence: no universal '
        'shortcut score, causal fraction or independent-study inference follows. Action: expand missing source '
        'coverage and compare distinct descriptors with later genuinely matched predictive outcomes.',
        '', 'No new raw source numeric target decode or real supervised/PCA/HDBSCAN/B60 fit occurred. '
        'The eight-view X plan is awaiting separate resource approval. The inspected unkeyed Y tables need '
        'a declared target-axis binding before a numeric supervised freeze. Unknown physical ownership '
        'otherwise permits explicitly optimistic exploratory CV; verified known links stay indivisible.',
        '', '## Local evidence entry points','',
        '- science.json: signed pointer to the full 53-view comparison and permission ledger.',
        '- OWNER_DECISION_PACKET.md: retained original requests and amended priorities.',
        '- EXPLORATORY_FIT_PROPOSAL.json: actual inspected identity blockers, not an admitted numeric task.',
        '- target-key-availability.json: bounded Y-header question, without target-value decoding.',
        '- NEXT_X_CAMPAIGN_PLAN.json: exact prospective missing-view selection and costs; not approved.',
        '- output-review.json / LOCAL_OUTPUT_INCIDENT.md: factual output-boundary review and uncertainty.',
        '- final-delivery-local-validation.json: completed checks and actual storage measurement.','']
    (c.root/'CONFIDENTIAL_REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
    packet=c.root/'OWNER_DECISION_PACKET.md'
    text=packet.read_text(encoding='utf-8').replace('Known dependency groups must be mapped and kept whole.',
        'Verified known links must remain indivisible; missing physical-group membership permits explicitly optimistic observation CV.')
    if '## First technical question' not in text:
        text+=('\n\n## First technical question\n\nThe two inspected canonical tasks have observation-keyed X/M and '
        'unkeyed Y. Provide the declared Y observation/sample-axis manifest or relevant exporter code receipt, '
        'bound to the file hashes in EXPLORATORY_FIT_PROPOSAL.json. No original biological crosswalk is requested '
        'for observation CV. On receipt validate complete key membership, conflicts, partitions and target '
        'definition before numeric decode and any real fit. Without it, continue X coverage and reuse qualified '
        'historical scores. No external message is authorized. Real fitting still requires a separate exact budget decision.\n')
    packet.write_text(text,encoding='utf-8')
    c.preservation()
    print('ALPHA17_LOCAL_SCIENCE_AND_DECISION_HANDOFF_COMPLETE')


if __name__=='__main__':
    try:main()
    except Exception:
        print('ALPHA17_HANDOFF_REFUSED; DETAILS_REMAIN_LOCAL');raise SystemExit(2) from None
