"""Broaden declared-context selection before observing any new supervised Y."""
from collections import Counter,defaultdict
from pathlib import Path
import pandas as pd
from alpha18_common import Context
from nirs4all_domains.full_bank import CONTEXTS
from nirs4all_domains.storage import fingerprint,atomic_json,digest


def main():
    c=Context();f=c.load('campaign-freeze.json');assert not (c.root/'reference-progress.json').exists()
    retained=c.load('historical-retained-continuation.json');f['scopes'].update(retained['scopes'])
    for key in retained['blocked_sources']:f['scopes'].pop(key,None)
    assert not (c.root/'stress-freeze-v2.json').exists()
    entries={e['dataset_id']:e for e in f['entries']};plans=[]
    for s in f['sources']:
        key=s['view_id']
        if key not in f['scopes']:continue
        scope=f['scopes'][key];dev=scope['development_indices'];entry=entries[s['dataset_id']]
        if not 36<=len(dev)<=1200:continue
        columns=[k for k in [*CONTEXTS,'species','genus','scale','source_Project','source_project','year'] if k in entry.get('metadata_headers',[])]
        columns=list(dict.fromkeys(columns))
        if not columns:continue
        frame=pd.read_csv(entry['metadata_path'],sep=entry['metadata_separator'],usecols=['observation_id',*columns],dtype=str).fillna('')
        frame=frame.set_index('observation_id').loc[scope['observation_ids']]
        tasks=[t for t in f['tasks'] if t['view_id']==key and t['metadata_eligible']]
        if not tasks:continue
        for factor in columns:
            values=frame[factor].tolist();counts=Counter(values[i] for i in dev)
            if '' in counts or not 2<=len(counts)<=20 or min(counts.values())<12:continue
            groups=defaultdict(list)
            for i in dev:groups[scope['groups'][i]].append(i)
            if any(len({values[i] for i in ii})>1 for ii in groups.values()):continue
            level=sorted(counts,key=lambda v:(-counts[v],fingerprint([key,factor,v])))[0]
            cg=sorted([g for g,ii in groups.items() if values[ii[0]]==level],key=lambda g:fingerprint([18,'stress-eval',key,g]))
            if len(cg)<4 or len(groups)>400:continue
            evgroups=set(cg[:max(2,len(cg)//5)])
            evaluation=[i for g in evgroups for i in groups[g]]
            full=[i for i in dev if i not in set(evaluation)]
            stress=[i for i in full if values[i]!=level]
            if min(len(evaluation),len(stress))<6:continue
            plans.append({'view_id':key,'task_id':tasks[0]['task_id'],'target':tasks[0]['target'],'factor':factor,
                          'evaluation_indices':sorted(evaluation),'full_training_indices':sorted(full),
                          'stress_training_indices':sorted(stress),'context_level_digest':fingerprint(level),
                          'n_context_levels':len(counts),'n_declared_components':len(groups)})
            break
    value={'parent_freeze_id':f['freeze_id'],'protocol':'domains.bank_stress.v0.1',
           'selection_uses':'Declared context support and catalog order, no outcome values or predictive scores.',
           'plans':plans[:24],'target_numeric_cells_decoded':0,'controller_sha256':digest(__file__),
           'amendment':'Include declared species/genus, original scale, project/year as exploratory population/context factors; same claims and budget, at most 24 tasks. Three train-only native diagnostic PCAs per selected task; no outcome selection.'}
    value['historical_retained_continuation_id']=retained['continuation_id']
    value['supersedes_unexecuted_selection']=c.load('stress-freeze.json')['freeze_id']
    value['freeze_id']=fingerprint(value);c.save('stress-freeze-v2.json',value)
    atomic_json('docs/campaign/stress-selection.json',{k:v for k,v in value.items() if k!='plans'}|{'tasks':[{k:p[k] for k in ['view_id','task_id','target','factor','n_context_levels','n_declared_components']} for p in value['plans']]})
    print('PROSPECTIVE_STRESS_TASKS',len(value['plans']));print([(p['view_id'],p['factor']) for p in value['plans']])

if __name__=='__main__':main()
