"""Cached native and bridge checks within the approved alpha.17 envelope."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from alpha17_common import Context
from nirs4all_domains.storage import atomic_json,digest


def main():
    c=Context();root=Path('.audit/alpha17/validation');root.mkdir(parents=True,exist_ok=True)
    py=sys.executable
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8',
         'N4DOMAINS_BIN':str(Path('target/debug/n4domains.exe').resolve()),
         'PYTHONPATH':str(Path('.audit/alpha10/runtime').resolve()),'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1',
         'PIP_CACHE_DIR':str((root/'pip-cache').resolve())}
    checks=[('editable',[py,'-m','pip','install','--no-deps','--no-build-isolation','-e','bridges/python']),
        ('fmt',['cargo','fmt','--all','--check']),
        ('clippy',['cargo','clippy','--workspace','--all-targets','--locked','--','-D','warnings']),
        ('workspace',['cargo','test','--workspace','--locked']),
        ('native',['cargo','test','--workspace','--locked','--','--ignored']),
        ('rustdoc',['cargo','doc','--workspace','--no-deps','--locked']),
        ('python',[py,'-m','unittest','discover','-s','tests/integration','-v']),
        ('alpha12',[py,'scripts/check_alpha12_results.py','--require-manifest']),
        ('alpha13',[py,'scripts/check_alpha13_results.py','--require-complete','--require-local-preservation']),
        ('alpha14',[py,'scripts/check_alpha14_results.py','--require-local']),
        ('alpha15',[py,'scripts/check_alpha15_results.py']),
        ('alpha16',[py,'scripts/check_alpha16_results.py','--require-local']),
        ('alpha17',[py,'scripts/check_alpha17_results.py','--require-local']),
        ('source-isolation',[py,'scripts/verify_alpha11_source_isolation.py']),
        ('canonical-render',[env['N4DOMAINS_BIN'],'analyze','tests/fixtures/translation.json','--out',str(root/'canonical')]),
        ('canonical-report',[py,'scripts/check_report.py',str(root/'canonical/report.json')]),
        ('wheel',[py,'-m','pip','wheel','--no-deps','--no-build-isolation','bridges/python','--wheel-dir',str(root/'wheel')]),
        ('sdist',[py,'-c',"from setuptools.build_meta import build_sdist;print(build_sdist(__import__('os').environ['ALPHA17_SDIST_OUT']))"])]
    records=[]
    for name,command in checks:
        c.guard(67108864)
        local=env.copy();cwd=Path.cwd()
        if name in ['editable','wheel']:
            local['PYTHONPATH']=str(Path('.audit/alpha14/build-runtime').resolve())+os.pathsep+env['PYTHONPATH']
        if name=='sdist':
            cwd=Path('bridges/python');local['PYTHONPATH']=str(Path('.audit/alpha14/build-runtime').resolve())
            local['ALPHA17_SDIST_OUT']=str((root/'sdist').resolve());Path(local['ALPHA17_SDIST_OUT']).mkdir(parents=True,exist_ok=True)
        log=root/(name+'.'+str(time.time_ns())+'.log');start=time.perf_counter()
        with log.open('w',encoding='utf-8') as stream:
            result=subprocess.run(command,env=local,cwd=cwd,stdout=stream,stderr=subprocess.STDOUT)
        record={'check':name,'exit_code':result.returncode,'seconds':time.perf_counter()-start,
            'log':log.as_posix(),'sha256':digest(log),'resource_limits_respected':bool(c.guard())}
        records.append(record);atomic_json(root/'checks.json',records)
        print(json.dumps({'check':name,'exit_code':result.returncode}),flush=True)
        if result.returncode:raise SystemExit(result.returncode)
    c.preservation()


if __name__=='__main__':main()
