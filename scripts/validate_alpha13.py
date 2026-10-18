"""Actual serial release gates with unchanged storage limits and bounded growth."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from alpha13_common import ROOT,PUBLIC,policy
from nirs4all_domains.storage import atomic_json,digest,tree_bytes


def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8',errors='backslashreplace')
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--start',default='editable');args=p.parse_args()
    out=ROOT/'validation';out.mkdir(parents=True,exist_ok=True);env=os.environ.copy();py=sys.executable
    env.update(N4DOMAINS_BIN=str(Path('target/debug/n4domains.exe').resolve()),
        N4DOMAINS_METHODS_LIBRARY=str(Path('.venv/Lib/site-packages/n4m/lib/n4m.dll').resolve()),
        PYTHONPATH=str(Path('.audit/alpha10/runtime').resolve()),PIP_CACHE_DIR=str((ROOT/'pip-cache').resolve()),PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
    checks=[('editable',[py,'-m','pip','install','--no-deps','-e','bridges/python']),
        ('fmt',['cargo','fmt','--all','--check']),('clippy',['cargo','clippy','--workspace','--all-targets','--locked','--','-D','warnings']),
        ('workspace',['cargo','test','--workspace','--locked']),('native',['cargo','test','--workspace','--locked','--','--ignored']),
        ('rustdoc',['cargo','doc','--workspace','--no-deps','--locked']),('build',['cargo','build','--workspace','--locked']),
        ('schemas-rust',[env['N4DOMAINS_BIN'],'schema','--out','schemas']),('schemas-bank',[py,'scripts/generate_bank_schemas.py']),
        ('python',[py,'-m','unittest','discover','-s','tests/integration','-v']),
        ('alpha9-registry',[py,'scripts/check_alpha9_registry.py']),('alpha10-registry',[py,'scripts/check_alpha10_registry.py']),
        ('alpha11-registry',[py,'scripts/check_alpha11_registry.py']),('alpha12-results',[py,'scripts/check_alpha12_results.py','--require-manifest']),
        ('alpha13-results',[py,'scripts/check_alpha13_results.py','--require-complete','--require-local-preservation']),
        ('source-isolation',[py,'scripts/verify_alpha11_source_isolation.py']),('guarded-cache',[py,'scripts/run_alpha11_litter.py','replay']),
        ('canonical-report',[py,'scripts/check_report.py','.audit/alpha13/report-check/report.json']),
        ('wheel',[py,'-m','pip','wheel','--no-deps','bridges/python','--wheel-dir',str(out/'wheel')])]
    names=[n for n,c in checks];assert args.start in names
    limits=policy();proof=out/'checks.json';records=json.loads(proof.read_text()) if proof.exists() else []
    locators=json.loads((ROOT/'input-locators.json').read_text());cached=[Path(v['matrix']) for v in locators.values()]
    for name,command in checks[names.index(args.start):]:
        observed=tree_bytes([Path.cwd(),*cached]);growth=(240 if name in ['clippy','workspace'] else 32 if name in ['native','rustdoc','build'] else 8)*1024*1024
        assert observed+growth<=limits['workspace_max_bytes'],'CONSERVATIVE_VALIDATION_GROWTH_REQUIRES_REVIEW'
        for drive in ['C:/','D:/']:assert shutil.disk_usage(drive).free>growth+limits['reserve_free_bytes']
        log=out/(name+'.'+str(time.time_ns())+'.log');begin=time.perf_counter()
        with log.open('w',encoding='utf-8') as stream:result=subprocess.run(command,env=env,stdout=stream,stderr=subprocess.STDOUT)
        item={'check':name,'exit_code':result.returncode,'seconds':time.perf_counter()-begin,'log':log.as_posix(),'log_sha256':digest(log),
            'workspace_unique_bytes_after':tree_bytes([Path.cwd()]),'workspace_plus_selected_existing_x_bytes_after':tree_bytes([Path.cwd(),*cached])}
        records.append(item);atomic_json(proof,records);print(json.dumps(item),flush=True)
        if result.returncode:
            print(log.read_text(encoding='utf-8')[-6000:]);raise SystemExit(result.returncode)
        assert item['workspace_plus_selected_existing_x_bytes_after']<=limits['workspace_max_bytes'],'WORKSPACE_CEILING_REVIEW_REQUIRED'


if __name__=='__main__':main()
