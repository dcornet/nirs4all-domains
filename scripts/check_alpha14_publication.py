"""Review exact public source bytes and scan Git surfaces. No private upload.

--freeze-reviewed is an explicit code/document review operation, not science.
Only the finite engineering allowlist below can acquire new public provenance.
Private scientific exports would additionally require the disclosure ledger;
none is admitted by this source roster.
"""
import argparse
import hashlib
import hmac
import json
from pathlib import Path
import subprocess

from nirs4all_domains.disclosure import scan_bytes
from nirs4all_domains.privacy import PrivateStore,fail
from nirs4all_domains.publication import audit_surfaces,git_surfaces,public_record
from nirs4all_domains.storage import atomic_json

BASELINE='dd4496718f449cd8d02839fa7b33ac155fbbcccb'
ROSTER='docs/audit/alpha14-public-source-roster.json'
NEW={
    'configs/bank/storage-policy-alpha14.json',
    *('bridges/python/nirs4all_domains/'+x for x in ['privacy.py','disclosure.py','publication.py','private_batch.py','private_corpus.py','private-admission.v1.schema.json','public-disclosure.v1.schema.json']),
    *('schemas/'+x+'.v1.schema.json' for x in ['private-admission','public-disclosure']),
    *('tests/integration/'+x for x in ['test_privacy.py','test_private_batch.py','test_publication.py']),
    *('scripts/'+x+'.py' for x in ['generate_privacy_schemas','prepare_alpha14_audit','screen_alpha14_catalog',
        'review_alpha14_source_rights','freeze_alpha14_private','run_alpha14_private','run_alpha14_stability',
        'diagnose_alpha14_private','finalize_alpha14_local','check_alpha14_publication','check_alpha14_results',
        'validate_alpha14','collect_alpha14_validation','record_alpha14_ci']),
    *('docs/'+x+'.md' for x in ['ALPHA14_RESOURCE_PLAN','ALPHA14_PRIVATE_CORPUS_PROTOCOL','ALPHA14_DISCLOSURE_POLICY',
        'ALPHA14_FULL_BANK_SCREENING','ALPHA14_PUBLIC_SYNTHESIS','ALPHA14_SUPERVISED_PILOT','ALPHA14_EXECUTION_NOTES',
        'ALPHA14_ECOSYSTEM_GAPS','ALPHA14_RELEASE_REPORT']),
    *('docs/audit/'+x+'.json' for x in ['alpha14-frozen-output-hashes','alpha14-portable-preservation',
        'alpha14-validation','alpha14-publication-guard','alpha14-storage','github-ci-alpha14']),ROSTER}
CHANGED={'README.md','Cargo.toml','Cargo.lock','bridges/python/pyproject.toml','.github/workflows/ci.yml',
    'crates/nirs4all-domains-cli/Cargo.toml',
    *('docs/'+x+'.md' for x in ['ARCHITECTURE','METHOD_REUSE_MATRIX','SCIENTIFIC_PROTOCOLS',
        'STORAGE_AND_REPRODUCIBILITY','BENCHMARK_QUALIFICATION_MODEL','ROADMAP','VALIDATION'])}


def names(*args):
    return [v.decode() for v in subprocess.check_output(['git',*args,'-z']).split(b'\0') if v]


def baseline_roster():
    paths=names('ls-tree','-r','--name-only',BASELINE)
    data=subprocess.check_output(['git','cat-file','--batch'],input=''.join(BASELINE+':'+p+'\n' for p in paths).encode())
    offset=0;result={}
    for p in paths:
        end=data.index(b'\n',offset);size=int(data[offset:end].split()[2]);blob=data[end+1:end+1+size];offset=end+2+size
        result[p]=public_record(blob,'historical_public')
    return result


def private_taints():
    config=Path('.audit/alpha14/private-root.json')
    if not config.exists():fail('LOCAL_PRIVATE_REVIEW_REQUIRED')
    value=json.loads(config.read_text());root=Path(value['root'])
    store=PrivateStore(root,Path.cwd())
    global_literals=[(store.keys/'scope.key').read_bytes(),str(root),str(root).replace('\\','/')]
    newer=[]
    frozen=root/'execution-freeze.json'
    if frozen.exists():
        for source in json.loads(frozen.read_text())['freeze']['sources']:
            newer.extend([source['source_sha256'],source['admission']['source_scope'].split('/')[0]])
    mapping=store.identities/'mapping.json'
    if mapping.exists():
        for contract in json.loads(mapping.read_text())['mapping'].values():
            # Tiny numeric identifiers cannot be reliably distinguished from
            # ordinary public numbers. Closed schemas/provenance exclude them;
            # literal matching is only a secondary defense for distinct strings.
            original=contract[-1]
            if len(original)>=16 and not original.isnumeric():newer.append(original)
    return global_literals,newer,store


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--freeze-reviewed',action='store_true');p.add_argument('--staged',action='store_true')
    p.add_argument('--public-only',action='store_true');args=p.parse_args()
    baseline=baseline_roster()
    if args.public_only:
        global_literals,newer,store=[],[],None
    else:global_literals,newer,store=private_taints()
    if args.freeze_reviewed:
        if args.public_only:fail('LOCAL_REVIEW_REQUIRED_TO_FREEZE_ROSTER')
        current=set(names('ls-files'))|set(names('ls-files','--others','--exclude-standard'))
        if current-set(baseline)-NEW:fail('NEW_PUBLIC_SURFACE_NOT_IN_REVIEW_ALLOWLIST')
        records={};variants={}
        for path in sorted(current-{ROSTER}):
            file=Path(path)
            if not file.is_file() or file.is_symlink():fail('REVIEWED_SOURCE_FILE_REQUIRED')
            data=file.read_bytes();scan_bytes(path.encode()+b'\n'+data,sensitive_literals=global_literals)
            old=baseline.get(path)
            if old and hashlib.sha256(data).hexdigest()==old['sha256']:
                records[path]=old;continue
            if old and path not in CHANGED|NEW:
                original=subprocess.check_output(['git','cat-file','blob',BASELINE+':'+path])
                if data.replace(b'\r\n',b'\n')==original.replace(b'\r\n',b'\n'):
                    records[path]=old
                    variants[path]={'checkout_sha256':hashlib.sha256(data).hexdigest(),'repository_sha256':old['sha256']}
                    continue
            if path not in CHANGED|NEW:
                # Git's existing newline-only checkout differences are allowed
                # only for exact recorded original local hashes.
                local=json.loads(Path('docs/audit/alpha14-frozen-output-hashes.json').read_text())
                if path not in local or hashlib.sha256(data).hexdigest()!=local[path]:fail('UNREVIEWED_BASELINE_CHANGE')
                records[path]=public_record(data,'historical_public');continue
            scan_bytes(path.encode()+b'\n'+data,sensitive_literals=newer)
            kind='synthetic_fixture' if path.startswith('tests/') else 'reviewed_documentation' if path.endswith('.md') else 'public_source'
            canonical=data.replace(b'\r\n',b'\n') if Path(path).suffix in ['.py','.md','.json','.toml','.lock','.yml','.yaml'] else data
            records[path]=public_record(canonical,kind)
            if canonical!=data:
                variants[path]={'checkout_sha256':hashlib.sha256(data).hexdigest(),'repository_sha256':records[path]['sha256']}
        value={'schema_version':1,'baseline_commit':BASELINE,'files':records,'newline_only_variants':variants}
        atomic_json(ROSTER,value)
        atomic_json(store.root/'public-source-review.json',{'roster':value,'authentication':store.authenticate(value)})
        print(json.dumps({'status':'explicit_public_source_roster_frozen','private_scientific_exports_approved':0}));return
    value=json.loads(Path(ROSTER).read_text())
    if set(value)!={'schema_version','baseline_commit','files','newline_only_variants'} or value['schema_version']!=1 or value['baseline_commit']!=BASELINE:
        fail('PUBLIC_SOURCE_ROSTER_INVALID')
    if store is not None:
        signed=json.loads((store.root/'public-source-review.json').read_text())
        if signed['roster']!=value or not hmac.compare_digest(signed['authentication'],store.authenticate(signed['roster'])):
            fail('PUBLIC_SOURCE_REVIEW_AUTHENTICATION_FAILED')
    roster=value['files']
    if set(roster)-set(baseline)-NEW:fail('PUBLIC_SOURCE_ROSTER_PATH_NOT_REVIEWED')
    if not isinstance(value['newline_only_variants'],dict) or set(value['newline_only_variants'])-set(roster):
        fail('PUBLIC_NEWLINE_VARIANT_INVALID')
    for path,variant in value['newline_only_variants'].items():
        if set(variant)!={'checkout_sha256','repository_sha256'} or variant['repository_sha256']!=roster[path]['sha256']:
            fail('PUBLIC_NEWLINE_VARIANT_INVALID')
        if any(not isinstance(v,str) or len(v)!=64 or any(c not in '0123456789abcdef' for c in v) for v in variant.values()):
            fail('PUBLIC_NEWLINE_VARIANT_INVALID')
    roster[ROSTER]=public_record(Path(ROSTER).read_bytes(),'public_source')
    surfaces=list(git_surfaces(Path.cwd(),staged=args.staged))
    if not args.staged:
        seen={p for p,d in surfaces}
        surfaces.extend((p,Path(p).read_bytes()) for p in names('ls-files','--others','--exclude-standard') if p not in seen)
    for path,data in surfaces:
        scan_bytes(path.encode()+b'\n'+data,sensitive_literals=global_literals)
        if path not in baseline or hashlib.sha256(data).hexdigest()!=baseline[path]['sha256']:
            # Historical local CRLF copies are still original public content.
            if roster.get(path,{}).get('kind')!='historical_public':scan_bytes(path.encode()+b'\n'+data,sensitive_literals=newer)
        if path in value['newline_only_variants']:
            v=value['newline_only_variants'][path]
            if set(v)!={'checkout_sha256','repository_sha256'} or v['repository_sha256']!=roster[path]['sha256']:
                fail('PUBLIC_NEWLINE_VARIANT_INVALID')
            sha=hashlib.sha256(data).hexdigest()
            if sha==v['checkout_sha256']:
                if hashlib.sha256(data.replace(b'\r\n',b'\n')).hexdigest()!=v['repository_sha256']:
                    fail('PUBLIC_NEWLINE_VARIANT_CONTENT_CHANGED')
                roster[path]=public_record(data,roster[path]['kind'])
    result=audit_surfaces(surfaces,roster,sensitive_literals=global_literals)
    result.update(mode='actual_index_blobs' if args.staged else 'worktree_and_new_public_files',
        private_taint_registry_checked=not args.public_only,
        private_scientific_exports_approved=0,private_inputs_sent_to_CI=False)
    print(json.dumps(result))


if __name__=='__main__':main()
