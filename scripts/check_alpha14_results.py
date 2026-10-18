"""Portable public contracts/history; optional private verification stays local."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import jsonschema
from nirs4all_domains.storage import digest


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--require-local',action='store_true');args=parser.parse_args()
    preservation=json.loads(Path('docs/audit/alpha14-portable-preservation.json').read_text())
    hashes=json.loads(Path('docs/audit/alpha14-frozen-output-hashes.json').read_text())
    variants=preservation['newline_only_variants']
    for path,sha in preservation['repository_blobs'].items():
        accepted={sha}
        if path in variants:accepted.add(variants[path]['local_snapshot_sha256'])
        assert digest(path) in accepted,'PROTECTED_PORTABLE_ALPHA14_BASELINE_CHANGED'
    if args.require_local:
        assert all(digest(p)==h for p,h in hashes.items()),'PROTECTED_LOCAL_ALPHA14_BASELINE_CHANGED'
        cfg=json.loads(Path('.audit/alpha14/private-root.json').read_text());root=Path(cfg['root'])
        from nirs4all_domains.privacy import PrivateStore
        store=PrivateStore(root,Path.cwd())
        report=json.loads((root/'confidential-release-report.json').read_text())
        assert store.authenticate(report['report'])==report['authentication']
        assert report['report']['all_164_entries_screened'] is True
        assert report['report']['private_source_data_in_public_repository'] is False
    for name in ['private-admission','public-disclosure']:
        path=Path('schemas')/(name+'.v1.schema.json')
        schema=json.loads(path.read_text());jsonschema.Draft202012Validator.check_schema(schema)
        assert path.read_bytes()==(Path('bridges/python/nirs4all_domains')/path.name).read_bytes()
    # Frozen original hypotheses and outcome bindings are protected historical
    # files. No private input, key, mapping, target or result is needed in CI.
    assert not Path('docs/ALPHA14_PRIVATE_X_RESULTS.md').exists()
    scientific=Path('docs/benchmarks/alpha14')
    assert not scientific.exists() or not any(scientific.rglob('*')),'UNREVIEWED_ALPHA14_SCIENTIFIC_EXPORT'
    print(json.dumps({'status':'verified','protected_repository_files':len(preservation['repository_blobs']),
        'protected_local_files_verified':len(hashes) if args.require_local else None,
        'private_verification':'verified_locally' if args.require_local else 'not_accessed_in_portable_verification',
        'public_private_scientific_payloads':0,'frozen_H1_H5_preserved':True}))


if __name__=='__main__':main()
