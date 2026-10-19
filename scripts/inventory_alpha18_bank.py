"""Catalog/export metadata and reuse accounting; no quantitative target decode."""
from collections import Counter
import csv
from pathlib import Path
import yaml

from alpha18_common import Context,read
from nirs4all_domains.storage import atomic_json,digest,fingerprint


def header(path):
    with Path(path).open(encoding='utf-8-sig') as stream:
        first=stream.readline()
    sep=';' if first.count(';')>first.count(',') else ','
    return next(csv.reader([first],delimiter=sep)),sep


def row_count(path):
    # These standardized exporters remove embedded newlines in object cells.
    # Count record lines without materializing/decoding retained target cells.
    count=0;last=b''
    with Path(path).open('rb') as stream:
        while data:=stream.read(1048576):count+=data.count(b'\n');last=data[-1:]
    return max(0,count+(last not in [b'',b'\n'])-1)


def main():
    c=Context();audit=c.old.auth(c.store.root/'screening-rights-reviewed.json','audit')
    cohort=c.old.phase('cohort-v2');assert len(audit['entries'])==164 and len(cohort['views'])==171
    files=[]
    for e in audit['entries']:
        if e['access_analysis_eligible']:
            leaf=Path(c.cfg['source_root'])/e['dataset_id']
            files.extend(str(p) for p in leaf.glob('*.csv'))
            if (leaf/'source_to_standard.py').exists():files.append(str(leaf/'source_to_standard.py'))
    c.participate(files)
    private={'protocol':'domains.full_bank.inventory.v0.1','entries':[],'sources':[],'tasks':[]}
    old_science=read(c.old.load('science.json')['artifact_path']);reused={}
    for row in old_science['all_authorized_rows']:reused.setdefault(row['view_id'],[]).append(row)
    oldviews={r['view_id']:r for r in cohort['views']};oldstates={r['view_id']:r for r in cohort['executions']}
    hashes={k:v['content_sha256'] for k,v in oldviews.items()}
    x17=c.old.load('approved-X-execution-freeze.json')
    hashes.update({r['view_id']:r['sha256'] for r in x17['sources']})
    for ref in c.old.load('X-extension-results.json')['reports']:
        assert digest(ref['artifact_path'])==ref['artifact_sha256'];value=read(ref['artifact_path'])
        if value['result']['status']=='computed':reused[value['view_id']]=value['result']['value']
        oldstates[value['view_id']]={'status':value['result']['status'],'reason':value['result']['reason']}
    license17={r['view_id']:r for r in c.old.load('new-source-public-license-metadata.json')['records'] if r.get('license_id')=='cc-nc'}
    for e in audit['entries']:
        name=e['dataset_id'];leaf=Path(c.cfg['source_root'])/name
        descriptor=Path('.audit/datasets/catalog/datasets')/(name+'.yaml')
        assert digest(descriptor)==e['descriptor_sha256'],'PINNED_CATALOG_CHANGED'
        d=yaml.safe_load(descriptor.read_text(encoding='utf-8'))
        entry={'dataset_id':name,'content_version':e['content_version'],'family':e['family'],
            'analysis_authorized':e['access_analysis_eligible'],'catalog_tier':e['catalog_tier'],
            'source_urls':[r['locator'] for r in d.get('origin_sources',[]) if r.get('kind')=='url' and r.get('locator','').startswith(('https://','http://'))],
            'original_study_evidence':e['original_study'],'declared_variables':d.get('variables',[]),'declared_splits':d.get('splits',[]),
            'metadata_path':str(leaf/'M.csv'),'target_path':str(leaf/'Y.csv'),'exporter_path':str(leaf/'source_to_standard.py'),
            'permissions':e['permissions'],'source_count':len(e['sources'])}
        for kind,key in [('metadata','metadata_path'),('target','target_path'),('exporter','exporter_path')]:
            p=Path(entry[key]);entry[kind+'_available']=p.is_file()
            if e['access_analysis_eligible'] and p.is_file():
                entry[kind+'_sha256']=digest(p)
                if kind!='exporter':entry[kind+'_headers'],entry[kind+'_separator']=header(p);entry[kind+'_rows']=row_count(p)
        private['entries'].append(entry)
        for s in e['sources']:
            key=name+'/'+s['source_id'];path=Path(s['matrix_availability']['locator'])
            row={'view_id':key,'dataset_id':name,'source_id':s['source_id'],'content_version':e['content_version'],
                'family':e['family'],'modality':oldviews[key]['modality'],'catalog_n':s['dimensions']['n_observations'],
                'catalog_p':s['dimensions']['n_variables'],'axis_unit':s['dimensions']['axis_unit'],
                'analysis_authorized':e['access_analysis_eligible'],'matrix':str(path),'matrix_available':path.is_file(),
                'prior_execution_state':oldstates.get(key,{}).get('status','not_executed'),
                'prior_reason':oldstates.get(key,{}).get('reason'),'aggregate_permission':e['permissions']['publish_aggregates']['status']}
            if key in license17:row['aggregate_permission']='allowed_noncommercial'
            if e['access_analysis_eligible'] and path.is_file():
                row.update(input_sha256=digest(path),input_bytes=path.stat().st_size)
                row['headers'],row['separator']=header(path);row['n_observations']=row_count(path)
                row['n_bands']=len([h for h in row['headers'] if h not in ['observation_id','sample_id','ID_sample']])
                row['reused_exact_profile']=hashes.get(key)==row['input_sha256'] and key in reused
                row['rows']=reused[key] if row['reused_exact_profile'] else []
                row['X_plan']='reuse' if row['reused_exact_profile'] else 'compute' if row['n_observations']*row['n_bands']<=3000000 and row['n_observations']<=5000 else 'resource_deferred'
            else:row['reused_exact_profile']=False;row['X_plan']='analysis_not_authorized' if not e['access_analysis_eligible'] else 'source_unavailable';row['rows']=[]
            private['sources'].append(row)
            for variable in d.get('variables',[]):
                if variable.get('role')!='target':continue
                target=variable['name'];dtype=str(variable.get('type','')).lower()
                is_numeric=dtype in ['numeric','number','continuous','float','float64','float32','double','integer','int','int64']
                identifier=target.lower() in ['id','sample_id','observation_id','replicate','batch','plot','species_code','usda_species_code'] or target.lower().endswith(('_id','_code'))
                reason='CATEGORICAL_OR_UNDECLARED_NUMERIC_TYPE' if not is_numeric else 'IDENTIFIER_OR_CATEGORY_CODE' if identifier else None
                if reason is None and not e['access_analysis_eligible']:reason='ANALYSIS_NOT_AUTHORIZED'
                if reason is None and (not entry['target_available'] or target not in entry.get('target_headers',[])):reason='DECLARED_TARGET_COLUMN_UNAVAILABLE'
                if reason is None and row['X_plan'] in ['source_unavailable','analysis_not_authorized']:reason='REQUIRED_X_UNAVAILABLE'
                if reason is None and row.get('n_observations')!=entry.get('target_rows'):reason='X_Y_ROW_COUNT_MISMATCH_WITHOUT_DECLARED_RELATION'
                if reason is None and entry.get('metadata_rows') not in [None,row.get('n_observations')]:reason='X_M_ROW_COUNT_MISMATCH'
                if reason is None and row['X_plan']=='resource_deferred':reason='INITIAL_MATRIX_COST_TIER_EXCEEDED'
                t={'task_id':fingerprint([name,e['content_version'],s['source_id'],target,'domains.bank_reference.v0.1']),
                    'dataset_id':name,'view_id':key,'target':target,'declared_type':dtype,
                    'meaning':variable.get('description',variable.get('label',target)),
                    'unit':variable.get('unit',variable.get('units')) or 'unspecified_canonical_units',
                    'metadata_eligible':reason is None,'eligibility_reason':reason,
                    'alignment_basis':'Explicit matching IDs preferred; otherwise owner-attested same-export order with frozen file identities and no known independent reorder/filter.',
                    'independence_claim':False,'execution_state':'not_attempted'}
                private['tasks'].append(t)
        print(name+' INVENTORIED',flush=True)
    private['inventory_id']=fingerprint(private);c.save('inventory.json',private)
    public={'protocol':private['protocol'],'catalog_entries':164,'declared_source_views':171,
        'entries':[{k:e[k] for k in ['dataset_id','content_version','family','analysis_authorized','catalog_tier','source_urls','source_count']} for e in private['entries']],
        'source_views':[{k:r.get(k) for k in ['view_id','dataset_id','source_id','content_version','family','modality','analysis_authorized','matrix_available','catalog_n','catalog_p','n_observations','n_bands','prior_execution_state','X_plan','aggregate_permission']} for r in private['sources']],
        'quantitative_tasks':private['tasks'],'counts':{'X_plans':dict(Counter(r['X_plan'] for r in private['sources'])),
            'declared_target_tasks':len(private['tasks']),'metadata_eligible_quantitative_tasks':sum(t['metadata_eligible'] for t in private['tasks']),
            'target_eligibility_reasons':dict(Counter(t['eligibility_reason'] for t in private['tasks'] if t['eligibility_reason']))},
        'target_numeric_cells_decoded':0,'model_fits':0,'owner_same_export_attestation':True,
        'limitations':['Counts are source views and source/target tasks, not independent studies.',
            'Metadata eligibility precedes numeric, split, key/order and resource qualification; it is not execution proof.']}
    atomic_json('docs/campaign/bank-inventory.json',public);c.preservation()
    print(public['counts']);print(c.guard())


if __name__=='__main__':main()
