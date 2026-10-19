"""Actual native/bridge/report/package checks within the current envelope."""
import os
from pathlib import Path
import subprocess
import sys
import time
import ctypes
from alpha18_common import Context
from nirs4all_domains.storage import atomic_json,digest


def main():
    c=Context();root=Path('.audit/alpha18/validation');root.mkdir(parents=True,exist_ok=True)
    from n4m._ffi import library_path
    py=sys.executable;cargo=str(Path('.tools/cargo/bin/cargo.exe').resolve())
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8',
        'N4DOMAINS_BIN':str(Path('target/debug/n4domains.exe').resolve()),
        'N4DOMAINS_METHODS_LIBRARY':str(Path(library_path()).resolve()),
        'CARGO_HOME':str(Path('.tools/cargo').resolve()),'RUSTUP_HOME':str(Path('.tools/rustup').resolve()),
        'PYTHONPATH':str(Path('.audit/alpha10/runtime').resolve()),'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1',
        'PIP_NO_INDEX':'1','PIP_CACHE_DIR':str((root/'pip-cache').resolve())}
    env['PATH']=os.pathsep.join([str(Path(p).resolve()) for p in ['.tools/cargo/bin','.venv/Lib/site-packages/nirs4all_methods.libs','.tools/mingw64/bin']])+os.pathsep+env['PATH']
    # GCC's implicit default-manifest path is misquoted by this installation
    # under a workspace containing spaces. GCC resolves its executable to a long
    # path even when invoked through 8.3; the library search prefix must itself
    # use 8.3. No copy, junction or repository linker configuration is needed.
    buffer=ctypes.create_unicode_buffer(32768)
    short=ctypes.windll.kernel32.GetShortPathNameW
    if not short(str(Path('.tools/mingw64').resolve()),buffer,len(buffer)) or ' ' in buffer.value:raise RuntimeError('SPACE_SAFE_LOCAL_LINKER_PATH_REQUIRED')
    env['LIBRARY_PATH']=str(Path(buffer.value)/'x86_64-w64-mingw32/lib')
    checks=[('editable',[py,'-m','pip','install','--no-deps','--no-build-isolation','-e','bridges/python']),
        ('fmt',[cargo,'fmt','--all','--check']),
        ('clippy',[cargo,'clippy','--workspace','--all-targets','--locked','--','-D','warnings']),
        ('workspace',[cargo,'test','--workspace','--locked']),
        ('native',[cargo,'test','--workspace','--locked','--','--ignored']),
        ('rustdoc',[cargo,'doc','--workspace','--no-deps','--locked']),
        ('rust-schema',[cargo,'run','--locked','-p','nirs4all-domains-cli','--','schema','--out','schemas']),
        ('bank-schema',[py,'scripts/generate_bank_schemas.py']),
        ('privacy-schema',[py,'scripts/generate_privacy_schemas.py']),
        ('synthesis-schema',[py,'scripts/generate_synthesis_schemas.py']),
        ('python',[py,'-m','unittest','discover','-s','tests/integration','-v']),
        ('alpha12',[py,'scripts/check_alpha12_results.py','--require-manifest']),
        ('alpha13',[py,'scripts/check_alpha13_results.py','--require-complete']),
        ('alpha14',[py,'scripts/check_alpha14_results.py']),
        ('alpha15',[py,'scripts/check_alpha15_results.py']),
        ('alpha16',[py,'scripts/check_alpha16_results.py']),
        ('alpha17',[py,'scripts/check_alpha17_results.py']),
        ('alpha18',[py,'scripts/check_alpha18_results.py','--require-local']),
        ('source-isolation',[py,'scripts/verify_alpha11_source_isolation.py']),
        ('canonical-render',[env['N4DOMAINS_BIN'],'analyze','tests/fixtures/translation.json','--out',str(root/'canonical')]),
        ('canonical-report',[py,'scripts/check_report.py',str(root/'canonical/report.json')]),
        ('wheel',[py,'-m','pip','wheel','--no-deps','--no-build-isolation','bridges/python','--wheel-dir',str(root/'wheel')]),
        ('sdist',[py,'-c',"from setuptools.build_meta import build_sdist; print(build_sdist(__import__('os').environ['ALPHA18_SDIST_OUT']))"])]
    records=[]
    for name,command in checks:
        c.guard(134217728);local=env.copy();cwd=Path.cwd()
        if name in ['editable','wheel','sdist']:local['PYTHONPATH']=str(Path('.audit/alpha14/build-runtime').resolve())+os.pathsep+env['PYTHONPATH']
        if name=='sdist':
            cwd=Path('bridges/python');local['ALPHA18_SDIST_OUT']=str((root/'sdist').resolve());Path(local['ALPHA18_SDIST_OUT']).mkdir(parents=True,exist_ok=True)
        log=root/(name+'.'+str(time.time_ns())+'.log');begin=time.monotonic()
        with log.open('w',encoding='utf-8') as out:r=subprocess.run(command,cwd=cwd,env=local,stdout=out,stderr=subprocess.STDOUT)
        records.append({'check':name,'exit_code':r.returncode,'seconds':time.monotonic()-begin,'log':log.as_posix(),'sha256':digest(log)})
        atomic_json(root/'checks.json',records);print(name,r.returncode,flush=True)
        if r.returncode:raise SystemExit(r.returncode)
        c.guard()
    c.preservation();print('ALPHA18_LOCAL_GATES_COMPLETE')

if __name__=='__main__':main()
