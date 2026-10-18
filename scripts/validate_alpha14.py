"""Actual serial release gates with combined public/private storage guards."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from nirs4all_domains.storage import atomic_json,digest,tree_bytes


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--start',default='editable')
    p.add_argument('--only',default='');p.add_argument('--artifact-suffix',default='');a=p.parse_args()
    assert a.artifact_suffix in ['', '-portable-acl']
    root=Path('.audit/alpha14');out=root/'validation';out.mkdir(parents=True,exist_ok=True)
    cfg=json.loads((root/'private-root.json').read_text());private=Path(cfg['root'])
    freeze=json.loads((private/'execution-freeze.json').read_text())['freeze']
    files=freeze['sources'][0]['other_participating_files'] if freeze['sources'] else []
    policy=json.loads(Path('configs/bank/storage-policy-alpha14.json').read_text())
    env={**os.environ,'N4DOMAINS_BIN':str(Path('target/debug/n4domains.exe').resolve()),
        'N4DOMAINS_METHODS_LIBRARY':str(Path('.venv/Lib/site-packages/n4m/lib/n4m.dll').resolve()),
        'PYTHONPATH':str(Path('.audit/alpha10/runtime').resolve()),'PIP_CACHE_DIR':str((root/'pip-cache').resolve()),
        'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'}
    py=sys.executable
    checks=[('editable',[py,'-m','pip','install','--no-deps','-e','bridges/python']),
        ('fmt',['cargo','fmt','--all','--check']),('clippy',['cargo','clippy','--workspace','--all-targets','--locked','--','-D','warnings']),
        ('workspace',['cargo','test','--workspace','--locked']),('native',['cargo','test','--workspace','--locked','--','--ignored']),
        ('rustdoc',['cargo','doc','--workspace','--no-deps','--locked']),('build',['cargo','build','--workspace','--locked']),
        ('schemas-rust',[env['N4DOMAINS_BIN'],'schema','--out','schemas']),('schemas-bank',[py,'scripts/generate_bank_schemas.py']),
        ('schemas-privacy',[py,'scripts/generate_privacy_schemas.py']),('python',[py,'-m','unittest','discover','-s','tests/integration','-v']),
        ('alpha9-registry',[py,'scripts/check_alpha9_registry.py']),('alpha10-registry',[py,'scripts/check_alpha10_registry.py']),
        ('alpha11-registry',[py,'scripts/check_alpha11_registry.py']),('alpha12-results',[py,'scripts/check_alpha12_results.py','--require-manifest']),
        ('alpha13-results',[py,'scripts/check_alpha13_results.py','--require-complete','--require-local-preservation']),
        ('alpha14-results',[py,'scripts/check_alpha14_results.py','--require-local']),
        ('source-isolation',[py,'scripts/verify_alpha11_source_isolation.py']),('guarded-cache',[py,'scripts/run_alpha11_litter.py','replay']),
        ('canonical-render',[env['N4DOMAINS_BIN'],'analyze','tests/fixtures/translation.json','--out',str(root/'report-check')]),
        ('canonical-report',[py,'scripts/check_report.py',str(root/'report-check/report.json')]),
        ('wheel',[py,'-m','pip','wheel','--no-deps','bridges/python','--wheel-dir',str(out/('wheel'+a.artifact_suffix))]),
        ('sdist-tools',[py,'-m','pip','install','--no-deps','--target',str(root/'build-runtime'),'setuptools>=77']),
        ('sdist',[py,'-c',"import os;from setuptools.build_meta import build_sdist;print(build_sdist(os.environ['ALPHA14_SDIST_OUT']))"])]
    labels=[name for name,cmd in checks];assert a.start in labels
    selected=set(a.only.split(',')) if a.only else set(labels)
    assert selected<=set(labels)
    records=json.loads((out/'checks.json').read_text()) if (out/'checks.json').exists() else []
    for name,command in checks[labels.index(a.start):]:
        if name not in selected:continue
        growth=(320 if name=='clippy' else 240 if name=='workspace' else 64 if name in ['native','rustdoc','build'] else 16)*1024*1024
        used=tree_bytes([Path.cwd(),private,*files]);assert used+growth<=policy['workspace_max_bytes'],'VALIDATION_GROWTH_REQUIRES_REVIEW'
        assert all(shutil.disk_usage(d).free>growth+policy['reserve_free_bytes'] for d in ['C:/','D:/'])
        local_env=env.copy();cwd=Path.cwd()
        if name=='sdist':
            local_env['PYTHONPATH']=str((root/'build-runtime').resolve())
            local_env['ALPHA14_SDIST_OUT']=str((out/('sdist'+a.artifact_suffix)).resolve());cwd=Path('bridges/python')
            Path(local_env['ALPHA14_SDIST_OUT']).mkdir(parents=True,exist_ok=True)
        log=out/(name+'.'+str(time.time_ns())+'.log');begin=time.perf_counter()
        with log.open('w',encoding='utf-8') as stream:
            result=subprocess.run(command,env=local_env,cwd=cwd,stdout=stream,stderr=subprocess.STDOUT)
        used=tree_bytes([Path.cwd(),private,*files])
        row={'check':name,'exit_code':result.returncode,'seconds':time.perf_counter()-begin,
            'log':log.as_posix(),'log_sha256':digest(log),'combined_ceiling_respected':used<=policy['workspace_max_bytes']}
        records.append(row);atomic_json(out/'checks.json',records);print(json.dumps(row),flush=True)
        if result.returncode:
            # All these inputs are synthetic/public; no private execution logs
            # are emitted by this release-validation runner.
            print(log.read_text(encoding='utf-8')[-6000:]);raise SystemExit(result.returncode)
        assert row['combined_ceiling_respected'],'VALIDATION_COMBINED_CEILING_REVIEW_REQUIRED'


if __name__=='__main__':main()
