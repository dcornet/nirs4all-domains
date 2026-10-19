"""Freeze identity-only scopes and descriptor/task selection before Y decoding."""
from collections import Counter
from pathlib import Path
from alpha18_common import Context
from nirs4all_domains.full_bank import metadata_scope,CONTEXTS
from nirs4all_domains.storage import digest,fingerprint,atomic_json
from nirs4all_domains.dependence import state


def main():
    c=Context();inventory=c.load('inventory.json');entries={e['dataset_id']:e for e in inventory['entries']}
    name='campaign-freeze.json'
    assert not (c.root/name).exists(),'DO_NOT_REPLACE_A_SCIENTIFIC_FREEZE'
    scopes={};qualification=[];stress=[]
    for s in inventory['sources']:
        tasks=[t for t in inventory['tasks'] if t['view_id']==s['view_id'] and t['metadata_eligible']]
        if not tasks:continue
        try:
            scope=metadata_scope(entries[s['dataset_id']],s);scopes[s['view_id']]=scope
            result=state({'alignment':scope['alignment'],'n_development':len(scope['development_indices']),
                'n_retained':scope['n_retained'],'group_columns':scope['group_columns']})
            # At most one first eligible quantitative target per source, selected
            # without any outcome values. Eligibility is checked again per target.
            for factor in CONTEXTS:
                if factor not in scope['contexts']:continue
                values=scope['contexts'][factor];dev=scope['development_indices'];counts=Counter(values[i] for i in dev)
                counts.pop('',None)
                if 2<=len(counts)<=20 and min(counts.values())>=12 and len(dev)<=1200:
                    stress.append({'view_id':s['view_id'],'task_id':tasks[0]['task_id'],'factor':factor});break
        except Exception as error:result=state(reason=type(error).__name__+':'+str(error),status='failed')
        qualification.append({'view_id':s['view_id'],'result':result})
    v={'inventory_id':inventory['inventory_id'],'sources':inventory['sources'],
       'entries':inventory['entries'],'tasks':inventory['tasks'],'scopes':scopes,
       'qualification':qualification,'stress_selection':stress[:24],
       'target_numeric_cells_decoded':0,'model_fits':0,
       'budget':c.approval,'baseline_measurement':c.guard(),
       'methods_version':'1.3.6','dag_version':'0.3.41',
       'native_binary':'.audit/alpha13/executed-alpha13-cli.exe',
       'native_binary_sha256':digest('.audit/alpha13/executed-alpha13-cli.exe'),
       'controller_sha256':{str(p):digest(p) for p in [Path(__file__),Path('bridges/python/nirs4all_domains/full_bank.py'),Path('docs/ALPHA18_SCIENTIFIC_PROTOCOL.md'),Path('docs/ALPHA18_RESOURCE_PLAN.md')]}}
    v['freeze_id']=fingerprint(v);c.save(name,v)
    atomic_json('docs/campaign/prospective-freeze.json',{'freeze_id':v['freeze_id'],
        'inventory_id':v['inventory_id'],'qualification':qualification,'stress_selection':stress[:24],
        'controller_sha256':v['controller_sha256'],'n_reference_metadata_eligible':sum(t['metadata_eligible'] for t in v['tasks']),
        'target_numeric_cells_decoded':0,'model_fits':0,'resource_plan':'../ALPHA18_RESOURCE_PLAN.md',
        'scientific_protocol':'../ALPHA18_SCIENTIFIC_PROTOCOL.md'})
    print('SCOPES',len(scopes),'STRESS_SELECTION',len(stress[:24]));print('QUALIFICATION',Counter(q['result']['reason'] or 'computed' for q in qualification));print(c.guard())

if __name__=='__main__':main()
