"""Finite exact-byte engineering review; no private scientific export permission."""
import hashlib
import json
from pathlib import Path
import subprocess

import check_alpha14_publication as review

baseline_taints = review.private_taints
original_scan = review.scan_bytes
private_tokens = set()
global_tokens = set()
known_public = {}


def public_proof(path, body):
    """Only mechanically derived historical proof objects may repeat old tokens."""
    value = json.loads(body)
    previous_prefix = 'docs/audit/alpha15-'
    if path.endswith('frozen-output-hashes.json'):
        old = json.loads(subprocess.check_output(['git', 'show', review.BASELINE+':'+previous_prefix+'frozen-output-hashes.json']))
        assert all(value.get(p) == sha for p, sha in old.items())
        for p in set(value)-set(old):
            blob = subprocess.check_output(['git', 'show', review.BASELINE+':'+p])
            local = Path(p).read_bytes()
            assert local.replace(b'\r\n', b'\n') == blob.replace(b'\r\n', b'\n')
            assert value[p] == hashlib.sha256(local).hexdigest()
    elif path.endswith('portable-preservation.json'):
        old = json.loads(subprocess.check_output(['git', 'show', review.BASELINE+':'+previous_prefix+'portable-preservation.json']))
        assert set(value) == set(old) and value['baseline_commit'] == review.BASELINE
        assert all(value['repository_blobs'].get(p) == sha for p, sha in old['repository_blobs'].items())
        assert all(value['newline_only_variants'].get(p) == v for p, v in old['newline_only_variants'].items())
        for p in set(value['repository_blobs'])-set(old['repository_blobs']):
            blob = subprocess.check_output(['git', 'show', review.BASELINE+':'+p])
            local = Path(p).read_bytes()
            assert value['repository_blobs'][p] == hashlib.sha256(blob).hexdigest()
            assert local.replace(b'\r\n', b'\n') == blob.replace(b'\r\n', b'\n')
        assert set(value['newline_only_variants']) <= set(value['repository_blobs'])
        for p in set(value['newline_only_variants'])-set(old['newline_only_variants']):
            accepted = {value['repository_blobs'][p], hashlib.sha256(Path(p).read_bytes()).hexdigest()}
            assert set(value['newline_only_variants'][p].values()) <= accepted
    else:
        assert path == review.ROSTER
        assert set(value) == {'schema_version', 'baseline_commit', 'files', 'newline_only_variants'}
        assert value['schema_version'] == 1 and value['baseline_commit'] == review.BASELINE
        baseline = review.baseline_roster()
        assert set(value['files']) <= set(baseline) | review.NEW
        for p, record in value['files'].items():
            assert set(record) == {'kind', 'sha256', 'visibility'} and record['visibility'] == 'public'
            assert record['kind'] in {'historical_public', 'public_source', 'reviewed_documentation', 'synthetic_fixture'}
            data = Path(p).read_bytes()
            assert record['sha256'] in {hashlib.sha256(data).hexdigest(),
                hashlib.sha256(data.replace(b'\r\n', b'\n')).hexdigest()}
        assert set(value['newline_only_variants']) <= set(value['files'])
        for p, variant in value['newline_only_variants'].items():
            assert set(variant) == {'checkout_sha256', 'repository_sha256'}
            assert variant['checkout_sha256'] == hashlib.sha256(Path(p).read_bytes()).hexdigest()
            assert variant['repository_sha256'] == value['files'][p]['sha256']


def scoped_scan(data, *, sensitive_literals=(), **kwargs):
    """Keep participation taints everywhere except verified historical proofs."""
    path, separator, body = data.partition(b'\n')
    proofs = {review.ROSTER, 'docs/audit/alpha16-frozen-output-hashes.json',
        'docs/audit/alpha16-portable-preservation.json'}
    if separator and path.decode(errors='replace') in proofs:
        matched = [v for v in sensitive_literals if (v if isinstance(v, bytes) else v.encode()) in data]
        if any((v if isinstance(v, bytes) else v.encode()) in private_tokens for v in matched):
            public_proof(path.decode(), body)
            kept = []
            for literal in sensitive_literals:
                raw = literal if isinstance(literal, bytes) else literal.encode()
                if raw in private_tokens and raw not in global_tokens and raw in data:
                    if raw not in known_public:
                        known_public[raw] = subprocess.run(['git', 'grep', '-q', '-F', '-e', raw.decode(), review.BASELINE], capture_output=True).returncode == 0
                    if known_public[raw]:
                        continue
                kept.append(literal)
            sensitive_literals = kept
    return original_scan(data, sensitive_literals=sensitive_literals, **kwargs)


def private_taints():
    global_literals, newer, store = baseline_taints()
    config = Path('.audit/alpha16/private-root.json')
    if config.exists():
        from alpha16_common import Context
        context = Context()
        source_root = str(Path(context.cfg['source_root']))
        # The generic cache root occurs in historical public audit scripts.
        # Reject new mentions; exact unchanged historical bytes stay public.
        newer.extend([source_root, source_root.replace('\\', '/')])
        if (context.root/'source-resolution.json').exists():
            newer.extend(r['dataset_id'] for r in context.load('source-resolution.json')['investigations'])
        for path, item in context.inputs.items():
            newer.extend([path, path.replace('\\', '/'), item['sha256']])
    global_tokens.update(v if isinstance(v, bytes) else v.encode() for v in global_literals)
    private_tokens.update(v if isinstance(v, bytes) else v.encode() for v in newer)
    return global_literals, newer, store


review.private_taints = private_taints
review.scan_bytes = scoped_scan
review.BASELINE = '886cf82a9571aa3d7a52bf07021bf6f47034129b'
review.ROSTER = 'docs/audit/alpha16-public-source-roster.json'
review.REVIEW_FILE = 'alpha16/public-source-review.json'
review.NEW = {
    'configs/bank/storage-policy-alpha16.json', review.ROSTER,
    'bridges/python/nirs4all_domains/original_source.py',
    'tests/integration/test_original_reference.py',
    *('scripts/'+name+'.py' for name in ['alpha16_common', 'record_alpha16_approval',
        'run_alpha16_source_resolution', 'finalize_alpha16_local', 'check_alpha16_results',
        'check_alpha16_publication', 'validate_alpha16', 'collect_alpha16_validation',
        'record_alpha16_ci', 'finalize_alpha16_delivery']),
    *('docs/'+name+'.md' for name in ['ALPHA16_RESOURCE_PLAN', 'ALPHA16_ORIGINAL_REFERENCE_CLOSURE',
        'ALPHA16_STUDY_ADMISSION', 'ALPHA16_EXACT_PILOT_FREEZE', 'ALPHA16_SUPERVISED_RESULTS',
        'ALPHA16_UNRESOLVED_SOURCE_REQUESTS', 'ALPHA16_RELEASE_REPORT']),
    *('docs/audit/'+name+'.json' for name in ['alpha16-frozen-output-hashes',
        'alpha16-portable-preservation', 'alpha16-validation', 'alpha16-storage', 'github-ci-alpha16'])}


if __name__ == '__main__':
    review.main()
