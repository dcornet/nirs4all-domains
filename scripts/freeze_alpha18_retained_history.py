"""Carry forward known sealed memberships using identity-only historical records.

Scalar y and flat X arrays are removed from schema-v1 task text BEFORE JSON
number decoding. No historical or current retained outcome is accessed.
"""
from collections import defaultdict,Counter
import copy
import json
from pathlib import Path
import re
import pandas as pd
from alpha18_common import Context
from nirs4all_domains.storage import digest,fingerprint,atomic_json


def task_metadata(path):
    text=path.read_text(encoding='utf-8-sig')
    if '"observations"' not in text or '"partition"' not in text:return None
    text=re.sub(r'"y"\s*:\s*(?:null|-?[0-9.eE+]+)','"y":null',text)
    text=re.sub(r'"x"\s*:\s*\[[^\]]*\]','"x":[]',text)
    return json.loads(text)


def main():
    c=Context();f=c.load('campaign-freeze.json');assert not (c.root/'reference-progress.json').exists()
    assert not (c.root/'historical-retained-continuation.json').exists()
    names={e['dataset_id'] for e in f['entries']};history=defaultdict(list);proof=[]
    for base in [Path('results'),Path('.audit')]:
        for path in base.rglob('*task*.json'):
            if path.is_relative_to(Path('.audit/alpha18')):continue
            try:t=task_metadata(path)
            except (ValueError,KeyError):continue
            if not t or t.get('context',{}).get('dataset_id') not in names:continue
            name=t['context']['dataset_id'];obs=t.get('observations',[])
            if not any(r.get('partition')=='test' for r in obs):continue
            history[name].extend(obs);proof.append({'path':path.as_posix(),'sha256':digest(path),'dataset_id':name})
    scopes=copy.deepcopy(f['scopes']);scopes.update(c.load('scope-marker-continuation.json')['scopes'])
    entries={e['dataset_id']:e for e in f['entries']};updated={};blocked={};summary=[]
    ca='ecosis_freeze_dried_leaf_spectra_and_measured_traits_from_the_reflectance_nirs'
    ca_related={ca,'ecosis_fresh_leaf_spectra_and_measured_traits_from_the_sierra_reflectance_nirs','ecosis_oven_dried_leaf_spectra_and_measured_traits_from_the_si_reflectance_nirs'}
    for source in f['sources']:
        key=source['view_id'];name=source['dataset_id']
        if key not in scopes:continue
        records=history.get(name,[])
        if name in ca_related:records=history.get(ca,records)
        if not records:continue
        scope=scopes[key];entry=entries[name]
        columns=[k for k in ['observation_id','sample_id','source_sample_id','source_ID','source_plot','source_plot_name'] if k in entry.get('metadata_headers',[])]
        m=pd.read_csv(entry['metadata_path'],sep=entry['metadata_separator'],usecols=columns,dtype=str).fillna('')
        if 'observation_id' in m:m=m.set_index('observation_id').loc[scope['observation_ids']].reset_index()
        alias=defaultdict(list);plot=defaultdict(list)
        for r in records:
            for k in ['observation_id','sample_id','physical_sample_id']:
                if r.get(k):alias[str(r[k])].append(r)
            p=r.get('metadata',{}).get('plot_name')
            if p is not None:plot[str(p)].append(r)
        # Perten's original explicit sample/experimental-context ledger.
        if name=='perten_cereals_nir':
            admission=json.loads(Path('docs/benchmarks/alpha9/perten-admission.json').read_text())
            records=admission['specification']['split']['records'];alias=defaultdict(list)
            for r in records:alias[r['sample_id']].append({'partition':'test' if r['partition']=='retained' else 'train','independence_group':r['context_block']})
        # Canonical litter stores the original encoded specimen ID in source_ID;
        # the historical ledger declares the literal 'litter:' prefix.
        if 'intact_and_ground_leaf_litter' in name:
            admission=json.loads(Path('docs/benchmarks/alpha11/litter-admission.json').read_text())
            for r in admission['specification']['split']['memberships']:
                assert r['id'].startswith('litter:')
                alias[r['id'][len('litter:'):]].append({'partition':r['partition'],'independence_group':r['component']})
        matched=[];retained=set();newgroups=[]
        for i,row in enumerate(m.to_dict('records')):
            hits=[]
            for field in ['observation_id','sample_id','source_sample_id','source_ID']:
                if row.get(field):hits.extend(alias.get(row[field],[]))
            if not hits and name in ca_related:
                for field in ['source_plot_name','source_plot']:
                    if row.get(field):hits.extend(plot.get(row[field],[]))
            matched.append(bool(hits))
            if any(r.get('partition') in ['test','retained'] for r in hits):retained.add(i)
            gs={r.get('independence_group') or r.get('metadata',{}).get('validation_component_id') or r.get('metadata',{}).get('plot_name') for r in hits}-{None,''}
            # More than one historical block is an unresolved identity conflict.
            if len(gs)>1:matched[-1]=False
            newgroups.append('historical:'+next(iter(gs)) if len(gs)==1 else scope['groups'][i])
        if not all(matched):
            blocked[key]='KNOWN_PROJECT_RETAINED_POPULATION_WITHOUT_COMPLETE_CANONICAL_KEY_BINDING'
            summary.append({'view_id':key,'decision':'supervision_unavailable','mapped_rows':sum(matched),'n_rows':len(matched),'reason':blocked[key]});continue
        olddev=set(scope['development_indices']);retained|=set(range(len(matched)))-olddev
        protectedgroups={newgroups[i] for i in retained};dev=[i for i in range(len(matched)) if i not in retained and newgroups[i] not in protectedgroups]
        scope.update(groups=newgroups,development_indices=dev,n_retained=len(retained),
            n_purged_retained_component=sum(i not in retained and newgroups[i] in protectedgroups for i in range(len(matched))),
            group_columns=sorted(set(scope['group_columns']+['historical_declared_component'])))
        updated[key]=scope
        summary.append({'view_id':key,'decision':'known_sealed_memberships_preserved','n_development':len(dev),'n_retained':len(retained),'n_groups':len({newgroups[i] for i in dev})})
    value={'parent_freeze_id':f['freeze_id'],'scopes':updated,'blocked_sources':blocked,'summary':summary,'historical_metadata_inputs':proof,
           'target_numeric_cells_decoded':0,'model_fits':0,'controller_sha256':digest(__file__)}
    value['continuation_id']=fingerprint(value);c.save('historical-retained-continuation.json',value)
    atomic_json('docs/campaign/historical-retained-continuation.json',{k:v for k,v in value.items() if k not in ['scopes','historical_metadata_inputs']}|{'historical_metadata_input_count':len(proof)})
    print('RETAINED_SCOPE_DECISIONS',summary);print('HISTORICAL_INPUTS',len(proof),'KNOWN_COHORTS',len(history))

if __name__=='__main__':main()
