"""Additional protected handoff; preserve initial alpha17 reports unchanged."""
from alpha17_common import Context,read
from nirs4all_domains.storage import digest


def main():
    c=Context();old=c.load('science.json');rows=read(old['artifact_path'])['all_authorized_rows'][:]
    extension=c.load('X-extension-results.json')
    for r in extension['reports']:
        assert digest(r['artifact_path'])==r['artifact_sha256']
        v=read(r['artifact_path'])
        if v['result']['status']=='computed':rows+=v['result']['value']
    assert len({r['view_id'] for r in rows})==56
    lines=['# Alpha.17 scientific follow-up — 2026-10-19','',
        'Initial reports/receipts are preserved. All 56 authorized computed views appear here; '
        '42 views have public aggregate permission. No source-view count is an independent-study count.','',
        '| View | Representation | n | p | PC1 | Effective dimension | Clusters | Noise | Raw/SNV ARI |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    def cell(v):return format(v['value'],'.6g') if v['status']=='computed' else v['reason']
    for r in sorted(rows,key=lambda x:(x['view_id'],x['representation'])):
        lines.append('| '+' | '.join([r['view_id'],r['representation'],str(r['n_observations']),str(r['n_bands'])]+
            [cell(r['metrics'][k]) for k in ['pc1_fraction','effective_dimension','clusters_8','noise_8','raw_snv_ari']])+' |')
    lines+=['','## Actual predictive experiment','',
        'See the public ALPHA17_TABLET_PILOT_RESULTS.md for every permitted aggregate and adverse context. '
        'tablet-pilot-results.json authenticates the protected OOF/lineage artifact. '
        'The exact original-keyed source/target/FoldSets remain in ORIGINAL_KEYED_TABLET_PILOT_FREEZE.json. '
        'No canonical Y positional join or retained-label access. All 310 observations remain.',
        '', '## Decision','',
        'Authorized X and tablet work is complete. Missing original specimen/assay links limit independent '
        'generalization; unchanged owner investigations stop. Source-specific original requests remain '
        'in the initial OWNER_DECISION_PACKET.md, without making them prerequisites for this executed '
        'exploratory route. Only 655,918 campaign bytes remain unreserved; no further real fit/acquisition '
        'or retry is authorized. A later diverse/matched-design experiment requires a concrete fresh budget.',
        '', 'No raw matrix, source key, fold roster, target vector or OOF prediction is published. '
        'Ordinary source-permitted aggregates and public catalog names/links follow the owner decisions.', '']
    (c.root/'CONFIDENTIAL_FOLLOWUP_REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
    c.save('followup-handoff.json',{'report_sha256':digest(c.root/'CONFIDENTIAL_FOLLOWUP_REPORT.md'),
        'computed_views':56,'published_views':42,'pilot_result_pointer':c.load('tablet-pilot-results.json'),
        'initial_reports_preserved':True,'next_real_task_authorized':False,**c.guard()})
    c.preservation();print('ALPHA17_FULL_BANK_AND_PILOT_FOLLOWUP_HANDOFF_COMPLETE')


if __name__=='__main__':main()
