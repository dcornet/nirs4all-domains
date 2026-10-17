"""Serial, resumable release checks; logs and byte guards are execution evidence."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from nirs4all_domains.storage import atomic_json,digest,tree_bytes


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--start',default='editable');args=parser.parse_args()
    root=Path('.audit/alpha12/validation');root.mkdir(parents=True,exist_ok=True)
    py=sys.executable;env=os.environ.copy()
    env.update(N4DOMAINS_BIN=str(Path('target/debug/n4domains.exe').resolve()),
        N4DOMAINS_METHODS_LIBRARY=str(Path('.venv/Lib/site-packages/n4m/lib/n4m.dll').resolve()),
        PYTHONPATH=str(Path('.audit/alpha10/runtime').resolve()),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',PYTHONIOENCODING='utf-8')
    commands=[('editable',[py,'-m','pip','install','--no-deps','-e','bridges/python']),
        ('fmt',['cargo','fmt','--all','--check']),
        ('clippy',['cargo','clippy','--workspace','--all-targets','--locked','--','-D','warnings']),
        ('workspace',['cargo','test','--workspace','--locked']),
        ('native',['cargo','test','--workspace','--locked','--','--ignored']),
        ('rustdoc',['cargo','doc','--workspace','--no-deps','--locked']),
        ('build',['cargo','build','--workspace','--locked']),
        ('schemas-rust',[env['N4DOMAINS_BIN'],'schema','--out','schemas']),
        ('schemas-bank',[py,'scripts/generate_bank_schemas.py']),
        ('python',[py,'-m','unittest','discover','-s','tests/integration','-v']),
        ('alpha9-registry',[py,'scripts/check_alpha9_registry.py']),
        ('alpha10-registry',[py,'scripts/check_alpha10_registry.py']),
        ('alpha11-registry',[py,'scripts/check_alpha11_registry.py']),
        ('alpha12-results',[py,'scripts/check_alpha12_results.py']),
        ('source-isolation',[py,'scripts/verify_alpha11_source_isolation.py']),
        ('guarded-cache',[py,'scripts/run_alpha11_litter.py','replay']),
        ('canonical-report',[py,'scripts/check_report.py',str(next(Path('.audit/alpha11/scratch').glob('*/P2/*/coverage/report.json')))]),
        ('wheel',[py,'-m','pip','wheel','--no-deps','bridges/python','--wheel-dir',str(root/'wheel')])]
    assert args.start in dict(commands)
    ceiling=json.loads(Path('configs/bank/storage-policy-alpha12.json').read_text())['workspace_max_bytes']
    proof=root/'checks.json';records=json.loads(proof.read_text()) if proof.exists() else []
    start_index=[n for n,c in commands].index(args.start)
    for name,command in commands[start_index:]:
        start=time.perf_counter();log=root/(name+'.log')
        if log.exists():log=root/(name+'.'+str(time.time_ns())+'.log')
        with log.open('w',encoding='utf-8') as stream:
            result=subprocess.run(command,env=env,stdout=stream,stderr=subprocess.STDOUT,text=True)
        item={'check':name,'exit_code':result.returncode,'seconds':time.perf_counter()-start,
            'log':log.as_posix(),'log_sha256':digest(log),'workspace_unique_bytes_after':tree_bytes([Path.cwd()])}
        records.append(item);atomic_json(proof,records);print(json.dumps(item),flush=True)
        if result.returncode:
            print(log.read_text(encoding='utf-8')[-7000:]);raise SystemExit(result.returncode)
        if item['workspace_unique_bytes_after']>ceiling:raise RuntimeError('WORKSPACE_CEILING_EXCEEDED_REVIEW_REQUIRED')


if __name__=='__main__':main()
