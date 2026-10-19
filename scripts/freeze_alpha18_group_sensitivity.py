"""Freeze experimental-plot grouping contrasts from metadata, never scores."""
from collections import Counter
import copy
import pandas as pd
from alpha18_common import Context
from nirs4all_domains.storage import fingerprint,digest,atomic_json
from alpha18_target_selection import eligible_tasks


def main():
    c=Context();f=c.load('campaign-freeze.json');assert not (c.root/'group-sensitivity-freeze-v2.json').exists()
    f['scopes'].update(c.load('scope-marker-continuation.json')['scopes'])
    retained=c.load('historical-retained-continuation.json');f['scopes'].update(retained['scopes'])
    semantics={r['task_id']:r for r in c.load('target-semantics-v2.json')['records']}
    entries={e['dataset_id']:e for e in f['entries']};plans=[];scope_updates={}
    for source in f['sources']:
        key=source['view_id'];entry=entries[source['dataset_id']]
        if key not in f['scopes'] or key in retained['blocked_sources']:continue
        columns=[k for k in ['source_Plot','source_plot_id','source_plot_name','source_plot'] if k in entry.get('metadata_headers',[])]
        if not columns:continue
        scope=copy.deepcopy(f['scopes'][key]);n=len(scope['observation_ids'])
        frame=pd.read_csv(entry['metadata_path'],sep=entry['metadata_separator'],usecols=['observation_id',*columns],dtype=str).fillna('').set_index('observation_id').loc[scope['observation_ids']]
        parent=list(range(n));used=[]
        def find(i):
            while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
            return i
        for key_values,label in [(scope['groups'],'existing_component')]+[(frame[k].tolist(),k) for k in columns]:
            first={};repeat=False
            for i,value in enumerate(key_values):
                if not value or value.lower() in ['nan','na','none','unknown']:continue
                if value in first:parent[find(i)]=find(first[value]);repeat=True
                else:first[value]=i
            if repeat and label!='existing_component':used.append(label)
        if not used:continue
        groups=['declared-plot:'+fingerprint([source['view_id'],find(i)]) for i in range(n)]
        if len(set(groups))==len(set(scope['groups'])):continue
        excluded=set(range(n))-set(scope['development_indices']);sealed={groups[i] for i in excluded}
        dev=[i for i in scope['development_indices'] if groups[i] not in sealed]
        scope.update(groups=groups,development_indices=dev,
            n_purged_retained_component=n-len(dev)-scope['n_retained'],
            group_columns=sorted(set(scope['group_columns']+used)))
        scope_updates[source['view_id']]=scope
        tasks=eligible_tasks(f,source['view_id'],semantics)
        if not tasks:continue
        plans.append({'view_id':source['view_id'],'task_id':tasks[0]['task_id'],'target':tasks[0]['target'],
                      'plot_fields':used,'n_development':len(dev),'n_declared_groups':len({groups[i] for i in dev})})
    value={'parent_freeze_id':f['freeze_id'],'plans':plans[:14],'scopes':scope_updates,
           'protocol':'domains.bank_declared_plot_sensitivity.v0.1','controller_sha256':digest(__file__),
           'selection':'One semantic-priority quantitative target per source where plot links actually merge existing components; no model scores used.',
           'interpretation':'Primary reference estimates within-context performance. Additional whole-plot CV is conservative experimental-context sensitivity, not verified biological independence.',
           'maximum_model_fits':84,'reservation_upper_bytes':14*524288,'ceiling_increase_bytes':0}
    value['supersedes_unexecuted_freeze_id']=c.load('group-sensitivity-freeze.json')['freeze_id']
    value['target_priority_sha256']=digest('scripts/alpha18_target_selection.py')
    value['freeze_id']=fingerprint(value);c.save('group-sensitivity-freeze-v2.json',value)
    atomic_json('docs/campaign/group-sensitivity-freeze-v2.json',{k:v for k,v in value.items() if k!='scopes'})
    print('DECLARED_PLOT_CASES',value['plans'])

if __name__=='__main__':main()
