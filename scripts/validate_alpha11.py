"""Serial release gates with actual exit/log/byte evidence and workspace guard."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from nirs4all_domains.storage import atomic_json,digest,tree_bytes


def main():
    root=Path('.audit/alpha11/validation');root.mkdir(parents=True,exist_ok=True)
    py=sys.executable;env=os.environ.copy()
    env['N4DOMAINS_BIN']=str(Path('target/debug/n4domains.exe').resolve())
    env['N4DOMAINS_METHODS_LIBRARY']=str(Path('.venv/Lib/site-packages/n4m/lib/n4m.dll').resolve())
    env['PYTHONPATH']=str(Path('.audit/alpha10/runtime').resolve())
    env['OPENBLAS_NUM_THREADS']='1';env['OMP_NUM_THREADS']='1';env['PYTHONIOENCODING']='utf-8'
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
        ('source-isolation',[py,'scripts/verify_alpha11_source_isolation.py']),
        ('guarded-cache',[py,'scripts/run_alpha11_litter.py','replay']),
        ('canonical-report',[py,'scripts/check_report.py',str(next(Path('.audit/alpha11/scratch').glob('*/P2/*/coverage/report.json')))]),
        ('structural-report',[py,'scripts/check_structure_report.py','results/structure-alpha5-real/ecosis/technical_mean/report.json']),
        ('wheel',[py,'-m','pip','wheel','--no-deps','bridges/python','--wheel-dir',str(root/'wheel')])]
    # Locate an existing protected structural report without recomputing science.
    if not Path(commands[-2][1][-1]).exists():
        choices=[]
        for p in Path('results').glob('**/report.json'):
            if 'structure' in str(p).lower():
                try:
                    if json.loads(p.read_text()).get('protocol_version')=='domains.structure.v0.1':choices.append(p)
                except (UnicodeError,ValueError):pass
            if choices:break
        if not choices:raise ValueError('HISTORICAL_STRUCTURAL_REPORT_NOT_FOUND')
        commands[-2][1][-1]=str(choices[0])
    ceiling=json.loads(Path('configs/bank/storage-policy-alpha11.json').read_text())['workspace_max_bytes'];records=[]
    for name,command in commands:
        start=time.perf_counter();log=root/(name+'.log')
        with log.open('w',encoding='utf-8') as out:
            result=subprocess.run(command,env=env,stdout=out,stderr=subprocess.STDOUT,text=True)
        item={'check':name,'exit_code':result.returncode,'seconds':time.perf_counter()-start,
              'log_sha256':digest(log),'workspace_unique_bytes_after':tree_bytes([Path.cwd()])}
        records.append(item);atomic_json(root/'checks.json',records);print(json.dumps(item),flush=True)
        if result.returncode:
            print(log.read_text(encoding='utf-8')[-6000:]);raise SystemExit(result.returncode)
        if item['workspace_unique_bytes_after']>ceiling:raise RuntimeError('WORKSPACE_CEILING_EXCEEDED_REVIEW_REQUIRED')


if __name__=='__main__':main()
