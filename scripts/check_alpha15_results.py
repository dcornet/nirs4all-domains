"""Portable alpha.15 invariants; confidential numerical checks only on request."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import jsonschema
from nirs4all_domains.storage import digest


def main():
    parser = argparse.ArgumentParser();parser.add_argument('--require-local', action='store_true');args = parser.parse_args()
    frozen = json.loads(Path('docs/audit/alpha15-frozen-output-hashes.json').read_text())
    portable = json.loads(Path('docs/audit/alpha15-portable-preservation.json').read_text())
    for path, sha in portable['repository_blobs'].items():
        accepted = {sha, portable['newline_only_variants'].get(path, {}).get('local_snapshot_sha256')}
        assert digest(path) in accepted, 'ALPHA15_PROTECTED_REPOSITORY_HISTORY_CHANGED'
    schema = json.loads(Path('schemas/cross-dataset-synthesis.v1.schema.json').read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    assert Path('schemas/cross-dataset-synthesis.v1.schema.json').read_bytes() == Path('bridges/python/nirs4all_domains/cross-dataset-synthesis.v1.schema.json').read_bytes()
    if args.require_local:
        from alpha15_common import Context, read
        from nirs4all_domains.synthesis import validate_states
        context = Context()
        assert all(digest(s['matrix']) == s['source_sha256'] for s in context.freeze['sources']), 'ALPHA15_ORIGINAL_CACHE_CONTENT_CHANGED'
        closure_inputs = context.load('closure-input-accounting.json')
        assert all(digest(p['path']) == p['sha256'] for p in closure_inputs['original_and_canonical_inputs']), 'ALPHA15_CLOSURE_INPUT_CHANGED'
        # The engineering collector creates attribution after the first full
        # local gate run. Once present, it must always have exact source bytes.
        if (context.root/'execution-source-attribution.json').exists():
            attribution = context.load('execution-source-attribution.json')
            snapshot = context.load('executed-source-snapshot.json')
            assert set(snapshot['sources']) == set(attribution['executed_controller_sources'])
            assert all(hashlib.sha256(base64.b64decode(item['base64'], validate=True)).hexdigest() == item['sha256'] ==
                attribution['executed_controller_sources'][path] for path, item in snapshot['sources'].items()), 'EXECUTED_SCIENTIFIC_SOURCE_CHANGED'
        assert all(digest(p) == sha for p, sha in frozen.items()), 'ALPHA15_LOCAL_HISTORY_CHANGED'
        preservation = read(context.root/'baseline-private-preservation.json')
        assert preservation['authentication'] == context.store.authenticate(preservation['preservation'])
        assert all(digest(context.store.root/p) == sha for p, sha in preservation['preservation']['files'].items()), 'ALPHA15_CONFIDENTIAL_BASELINE_CHANGED'
        for name in ['cohort-v2', 'synthesis-v2', 'source-closure-v2', 'report']:
            receipt = context.load(name+'.json')
            assert digest(receipt['artifact_path']) == receipt['artifact_sha256'], 'ALPHA15_PRIVATE_RECEIPT_CHANGED'
        package = read(context.load('synthesis-v2.json')['artifact_path'])
        result = package['synthesis'];jsonschema.validate(result, schema);validate_states(result)
        assert all(digest(a['path']) == a['sha256'] for a in package['artifacts'])
        report = read(context.load('report.json')['artifact_path'])
        assert set('ABCDEFGHIJ') <= set(report)
        assert digest(report['markdown']['path']) == report['markdown']['sha256']
        assert not report['G']['real_pilot_executed'] and not report['H']['new_public_exports']
        assert all(c['decision']['decision'] == 'local_only' for c in report['H']['candidates'])
        context.guard()
    assert not Path('docs/benchmarks/alpha15').exists(), 'UNAPPROVED_SCIENTIFIC_EXPORT'
    print(json.dumps({'status': 'verified', 'protected_repository_files': len(portable['repository_blobs']),
        'protected_local_files_verified': len(frozen) if args.require_local else None,
        'private_verification': 'verified_locally' if args.require_local else 'not_accessed_in_portable_verification',
        'new_private_scientific_exports': 0, 'frozen_H1_H5_preserved': True}))


if __name__ == '__main__':
    try: main()
    except Exception:
        print('ALPHA15_VERIFICATION_REFUSED; NO_CONFIDENTIAL_DETAILS');raise SystemExit(2)
