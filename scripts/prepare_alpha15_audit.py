"""Extend public preservation and privately freeze the prior confidential corpus."""
import hashlib
import json
from pathlib import Path
import subprocess

from nirs4all_domains.privacy import PrivateStore
from nirs4all_domains.storage import atomic_json, digest

BASELINE = '7ecb6d978c20c2ab7195d1b288e52d66a7656748'


def main():
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip() == BASELINE
    prior = json.loads(Path('docs/audit/alpha14-frozen-output-hashes.json').read_text())
    assert len(prior) == 617 and all(digest(path) == sha for path, sha in prior.items())
    tracked = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASELINE]).decode().splitlines()
    added = {p for p in tracked if p.startswith(('docs/ALPHA14', 'docs/audit/alpha14-')) or
        p in ['docs/audit/github-ci-alpha14.json', 'configs/bank/storage-policy-alpha14.json']}
    names = set(prior) | added
    frozen = {p: digest(p) for p in sorted(names)}
    portable = sorted(names & set(tracked))
    data = subprocess.check_output(['git', 'cat-file', '--batch'],
        input=''.join(BASELINE+':'+p+'\n' for p in portable).encode())
    offset = 0; blobs = {}; variants = {}
    for p in portable:
        end = data.index(b'\n', offset); size = int(data[offset:end].split()[2])
        blob = data[end+1:end+1+size]; offset = end+2+size
        sha = hashlib.sha256(blob).hexdigest(); blobs[p] = sha
        if sha != frozen[p]:
            assert Path(p).read_bytes().replace(b'\r\n', b'\n') == blob.replace(b'\r\n', b'\n')
            variants[p] = {'local_snapshot_sha256': frozen[p], 'repository_blob_sha256': sha}
    for path, value in [('docs/audit/alpha15-frozen-output-hashes.json', frozen),
            ('docs/audit/alpha15-portable-preservation.json', {'baseline_commit': BASELINE,
                'repository_blobs': blobs, 'newline_only_variants': variants})]:
        if Path(path).exists(): assert json.loads(Path(path).read_text()) == value
        else: atomic_json(path, value)
    cfg = json.loads(Path('.audit/alpha15/private-root.json').read_text())
    store = PrivateStore(cfg['root'], Path.cwd()); destination = Path(cfg['report_root'])
    path = destination/'baseline-private-preservation.json'
    if path.exists():
        envelope = json.loads(path.read_text()); value = envelope['preservation']
        assert store.authenticate(value) == envelope['authentication']
        assert all(digest(store.root/p) == sha for p, sha in value['files'].items())
    else:
        files = {p.relative_to(store.root).as_posix(): digest(p) for p in store.root.rglob('*')
            if p.is_file() and not p.is_relative_to(destination)}
        value = {'visibility': 'local_private', 'baseline': BASELINE, 'files': files,
            'scope': 'All existing alpha.14 confidential evidence, reports, mappings and keys; new alpha.15 directory excluded.'}
        atomic_json(path, {'preservation': value, 'authentication': store.authenticate(value)})
    print(json.dumps({'protected_local_public_history_files': len(frozen), 'protected_repository_files': len(blobs),
        'prior_confidential_files_frozen_privately': True, 'private_file_names_counts_or_hashes_printed': False}))


if __name__ == '__main__':
    try: main()
    except Exception:
        print('ALPHA15_BASELINE_PRESERVATION_REFUSED; no confidential details printed.')
        raise SystemExit(2)
