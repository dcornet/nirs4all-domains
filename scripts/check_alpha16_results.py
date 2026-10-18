"""Portable preservation and optional protected alpha.16 source evidence checks."""
import argparse
import base64
import hashlib
from pathlib import Path

from nirs4all_domains.storage import digest
from alpha16_common import read


def verify_private(context):
    for name, root in [('baseline-private-preservation.json', context.store.root),
                       ('baseline-workspace-private-preservation.json', Path.cwd())]:
        baseline = context.load(name)
        assert all(digest(root/p) == sha for p, sha in baseline['files'].items()), 'PROTECTED_PRIVATE_HISTORY_CHANGED'
    old = context.load('baseline-shared-journal.json')
    previous = old.get('journal', old.get('snapshot', old))
    ledger = read(context.scheduler.root/'journal.json')
    assert all(ledger['runs'][key] == value for key, value in previous['runs'].items()), 'HISTORICAL_JOURNAL_RUN_CHANGED'
    assert all(ledger['task_reserved_bytes'][key] >= value for key, value in previous['task_reserved_bytes'].items()), 'HISTORICAL_TASK_RESERVATION_REDUCED'
    assert ledger['reserved_campaign_bytes'] >= previous['reserved_campaign_bytes']
    assert all(digest(item['path']) == item['sha256'] for item in context.inputs.values()), 'FROZEN_PARTICIPATING_INPUT_CHANGED'
    for item in context.freeze['sources']:
        assert digest(item['matrix']) == item['source_sha256']
    snapshot = context.load('executed-source-snapshot.json')
    assert all(hashlib.sha256(base64.b64decode(item['base64'], validate=True)).hexdigest() == item['sha256']
        for item in snapshot['sources'].values()), 'EXECUTION_SOURCE_ARCHIVE_CHANGED'
    resolution = context.load('source-resolution.json')
    assert not resolution['target_cells_decoded'] and not resolution['real_supervised_fits']
    for candidate in resolution['investigations']:
        task = context.store.authenticate(['alpha16-source-resolution', candidate['dataset_id']])
        assert ledger['task_reserved_bytes'][task] <= context.approval['candidate_cumulative_bytes']
        assert candidate['stopping_decision']['stop_unchanged_search']
        assert candidate['requests'] and not candidate['retained_Y_accessed']
    pointer = context.load('report.json')
    assert digest(pointer['artifact_path']) == pointer['artifact_sha256']
    report = read(pointer['artifact_path'])
    annotation = context.load('report-scope-annotation.json')
    assert annotation['original_report_receipt'] == pointer['artifact_sha256']
    assert not annotation['new_target_cells_or_model_fits']
    assert all(set(['observation', 'confidence', 'consequence', 'action']) <= set(item) for item in annotation['findings'])
    assert set('ABCDEFGHIJ') <= set(report)
    assert digest(report['markdown']['path']) == report['markdown']['sha256']
    assert digest(report['I']['source_request_document']['path']) == report['I']['source_request_document']['sha256']
    assert not report['F']['H1_H5_changed'] and not report['F']['outcome_formulas_changed']
    assert not report['G']['real_pilot_executed'] and not report['H']['new_public_scientific_exports']
    for value in report['G']['outcomes'].values():
        assert value['value'] is None and value['reason'] and value['status'] != 'computed'
    context.guard()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-local', action='store_true')
    args = parser.parse_args()
    portable = read('docs/audit/alpha16-portable-preservation.json')
    frozen = read('docs/audit/alpha16-frozen-output-hashes.json')
    for path, sha in portable['repository_blobs'].items():
        assert digest(path) in {sha, portable['newline_only_variants'].get(path, {}).get('local_snapshot_sha256')}, 'ALPHA16_PROTECTED_PUBLIC_HISTORY_CHANGED'
    if args.require_local:
        from alpha16_common import Context
        assert all(digest(path) == sha for path, sha in frozen.items()), 'ALPHA16_LOCAL_HISTORY_CHANGED'
        verify_private(Context())
    assert not Path('docs/benchmarks/alpha16').exists(), 'UNAPPROVED_PRIVATE_SCIENTIFIC_EXPORT'
    import json
    print(json.dumps({'status': 'verified', 'protected_repository_files': len(portable['repository_blobs']),
        'protected_local_files_verified': len(frozen) if args.require_local else None,
        'private_verification': 'verified_locally' if args.require_local else 'not_accessed_in_portable_verification',
        'new_private_scientific_exports': 0, 'frozen_H1_H5_preserved': True}))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('ALPHA16_VERIFICATION_REFUSED; DETAILS_PROTECTED')
        raise SystemExit(2) from None
