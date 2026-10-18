"""Bounded factual review of the identified raw-shell inspection incident."""
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import zipfile

from alpha17_common import Context
from nirs4all_domains.storage import atomic_json, digest


def build(context, folder):
    markers = {k:{v.encode(),v.replace('\\','/').encode(),v.replace('/','\\').encode()}
        for k,v in context.cfg.items() if k in ['root','report_root','previous_report_root','source_root']}
    def hits(data):
        return sorted(k for k,vs in markers.items() if any(v in data for v in vs))
    sources, events = [], []
    sessions = Path.home()/'.codex/sessions'
    for path in sessions.rglob('rollout-2026-10-16T12-43-27*.jsonl'):
        # The ongoing session is append-only: bind the observed prefix, not a
        # fictitious immutable whole-file hash. Account the entire current file.
        prefix = path.read_bytes()
        items = [json.loads(line) for line in prefix.splitlines()]
        matches = []
        for i,e in enumerate(items):
            payload = e.get('payload',{});command = payload.get('input','')
            if payload.get('type') != 'custom_tool_call' or not isinstance(command,str):
                continue
            if "Get-Content -LiteralPath '.audit/alpha16/private-root.json'" not in command:
                continue
            output = next((v for v in items[i+1:] if v.get('payload',{}).get('call_id') == payload['call_id']
                and v['payload'].get('type') == 'custom_tool_call_output'), None)
            if output is None:
                continue
            text = json.dumps(output['payload']['output'])
            # Decode representations only for comparison; never emit the value.
            found = []
            for key,values in markers.items():
                for value in values:
                    token = value.decode()
                    if any(t in text for t in [token,json.dumps(token)[1:-1],json.dumps(json.dumps(token)[1:-1])[1:-1]]):
                        found.append(key);break
            if not found:
                continue
            matches.append({'line':i+1,'call_id':payload['call_id'],'command_timestamp':e['timestamp'],
                'output_timestamp':output['timestamp'],'command_sha256':hashlib.sha256(command.encode()).hexdigest(),
                'output_sha256':hashlib.sha256(text.encode()).hexdigest(),'categories':found})
        if matches:
            sources.append(str(path));events.extend(matches)
            context.save('incident-transcript-prefix.json', {'path':str(path),'prefix_bytes':len(prefix),
                'prefix_sha256':hashlib.sha256(prefix).hexdigest(), 'receipt_scope':'Observed immutable prefix; source may append.'})
    assert events, 'EXACT_INCIDENT_EXECUTION_NOT_LOCATED'
    context.save('incident-inputs.json',sources)
    context.guard()
    tracked = {}
    for name in subprocess.check_output(['git','ls-files','-z']).decode().split('\0'):
        if name and Path(name).is_file():
            found = hits(Path(name).read_bytes())
            if found:tracked[name] = found
    old = {}
    for name in tracked:
        result = subprocess.run(['git','show','886cf82a9571aa3d7a52bf07021bf6f47034129b:'+name],capture_output=True)
        if result.returncode == 0:old[name] = hits(result.stdout)
    archives, logs = [], []
    for p in Path('.audit/alpha16/validation').rglob('*'):
        members = {}
        if p.suffix == '.whl':
            with zipfile.ZipFile(p) as z:members = {n:hits(z.read(n)) for n in z.namelist()}
        elif p.name.endswith('.tar.gz'):
            with tarfile.open(p) as t:members = {m.name:hits(t.extractfile(m).read()) for m in t.getmembers() if m.isfile()}
        else:continue
        archives.append({'path':str(p),'sha256':digest(p),'member_matches':{k:v for k,v in members.items() if v}})
    for p in Path('.audit/alpha16').rglob('*.log'):
        logs.append({'path':str(p),'sha256':digest(p),'categories':hits(p.read_bytes()),
            'destination':'downloaded_CI_log' if 'ci' in p.parts else 'local_engineering_log'})
    value = {'visibility':'local_private','events':events,'exact_locations':context.cfg,
        'sensitivity':'Generic development/cache/evidence directory locations; no raw matrices, target values or credentials in the identified configuration dump.',
        'responsible_boundary':'Assistant-authored PowerShell raw Get-Content inside exec; tool response, not application/native diagnostic.',
        'observed_dissemination':['Agent tool response','Persisted local agent transcript'],
        'local_terminal_copy':'No separate terminal recording established; exec used pipes.',
        'tracked_matches':tracked,'pre_incident_public_matches':old,'archives':archives,'logs':logs,
        'retention':'Matching local transcript prefix remains accessible to the local owner. External service retention/access not established by these local inspections.',
        'uploads':'No new upload performed by this review. Uninspected destinations and service-side copies remain unknown.',
        'mitigation':'Use scripts/inspect_private_roots.py for fixed-code inspection; synthetic subprocess regression. Raw shell bypass remains possible.',
        'no_secret_rotation_or_cache_migration':True}
    (context.root/'LOCAL_OUTPUT_INCIDENT.md').write_text('# Local output incident\n\n'
        +'\n\n'.join(k+': '+str(value[k]) for k in ['sensitivity','responsible_boundary','observed_dissemination','retention','uploads','mitigation'])
        +'\n\nExact authenticated evidence: output-review.json.\n',encoding='utf-8')
    return value


def main():
    context = Context()
    context.run('output-review', lambda folder: build(context,folder))
    context.preservation()
    print('ALPHA17_OUTPUT_REVIEW_COMPLETE; EXTERNAL_RETENTION_UNKNOWN')


if __name__ == '__main__':
    try:main()
    except Exception:
        print('ALPHA17_OUTPUT_REVIEW_REFUSED; DETAILS_REMAIN_LOCAL')
        raise SystemExit(2) from None
