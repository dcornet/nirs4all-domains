"""Read-only preservation snapshot; no spectral loading, acquisition or fitting."""
import hashlib
import json
from pathlib import Path
import subprocess
from nirs4all_domains.storage import atomic_json,digest

BASELINE='ebb1b9b8a45d01618931d846d059641701cac7da'


def main():
    assert subprocess.check_output(['git','rev-parse','HEAD']).decode().strip()==BASELINE
    prior=json.loads(Path('docs/audit/alpha12-frozen-output-hashes.json').read_text())
    assert len(prior)==371 and all(digest(p)==h for p,h in prior.items())
    tracked=subprocess.check_output(['git','ls-tree','-r','--name-only',BASELINE]).decode().splitlines()
    names=set(prior)|{p for p in tracked if p.startswith(('docs/benchmarks/alpha12/','docs/ALPHA12','docs/audit/alpha12-')) or p=='docs/audit/github-ci-alpha12.json'}
    frozen={p:digest(p) for p in sorted(names)}
    portable=sorted(set(tracked)&names)
    data=subprocess.check_output(['git','cat-file','--batch'],input=''.join(BASELINE+':'+p+'\n' for p in portable).encode())
    offset=0;blobs={};variants={}
    for p in portable:
        end=data.index(b'\n',offset);header=data[offset:end].split();assert header[1]==b'blob'
        size=int(header[2]);blob=data[end+1:end+1+size];offset=end+2+size
        sha=hashlib.sha256(blob).hexdigest();blobs[p]=sha
        if sha!=frozen[p]:
            assert Path(p).read_bytes().replace(b'\r\n',b'\n')==blob.replace(b'\r\n',b'\n'),p
            variants[p]={'local_snapshot_sha256':frozen[p],'repository_blob_sha256':sha}
    destination=Path('docs/audit/alpha13-frozen-output-hashes.json')
    if destination.exists():assert json.loads(destination.read_text())==frozen
    atomic_json(destination,frozen)
    atomic_json('docs/audit/alpha13-portable-preservation.json',{'baseline_commit':BASELINE,'repository_blobs':blobs,
        'newline_only_variants':variants,'scope':'Original local hashes and baseline repository bytes both preserved. No historical content changes.'})
    print(json.dumps({'protected_local':len(frozen),'protected_portable':len(portable),'newline_only_variants':len(variants),'baseline':BASELINE}))


if __name__=='__main__':main()
