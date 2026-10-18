"""One bounded new question: which already-profiled Y tables expose join keys?"""
import csv
from pathlib import Path
import yaml

from alpha17_common import Context
from nirs4all_domains.storage import digest


def main():
    c=Context();old=c.root/'target-key-availability.json'
    if old.exists():
        c.load(old.name);print('ALPHA17_TARGET_KEY_RECEIPT_REUSED');return
    cohort=c.phase('cohort-v2');profiled={r['view_id'] for r in c.phase('synthesis-v2')['synthesis']['rows']}
    views=[v for v in cohort['views'] if v['view_id'] in profiled]
    paths=sorted({str(Path(c.cfg['source_root'])/v['catalog_id']/'Y.csv') for v in views
        if (Path(c.cfg['source_root'])/v['catalog_id']/'Y.csv').is_file()})
    c.guard(paths=paths)
    existing=c.load('candidate-inputs.json') if (c.root/'candidate-inputs.json').exists() else []
    c.save('candidate-inputs.json',sorted(set(existing)|set(paths)))
    records=[]
    for v in views:
        path=Path(c.cfg['source_root'])/v['catalog_id']/'Y.csv'
        record={'view_id':v['view_id'],'family':v['family'],'key_fields':[],'continuous_targets':[],
            'status':'Y_TABLE_NOT_PRESENT','numeric_target_cells_decoded':0}
        if path.is_file():
            with path.open(encoding='utf-8-sig') as stream:first=stream.readline()
            sep=';' if first.count(';')>first.count(',') else ','
            fields=next(csv.reader([first],delimiter=sep))
            descriptor=yaml.safe_load((Path('.audit/datasets/catalog/datasets')/(v['catalog_id']+'.yaml')).read_text(encoding='utf-8'))
            record.update(key_fields=[k for k in ['observation_id','sample_id'] if k in fields],
                continuous_targets=[x['name'] for x in descriptor['variables'] if x['role']=='target'
                    and x['name'] in fields and x.get('type','').lower() in ['float','float64','number','numeric','continuous','double']],
                header_sha256=digest(path),path=str(path),
                status='DECLARED_KEY_PRESENT' if any(k in fields for k in ['observation_id','sample_id']) else 'NO_EXPLICIT_TARGET_KEY')
        records.append(record)
    c.save(old.name,{'scope':'Already-profiled authorized views only; header/key feasibility, not an original-owner re-audit.',
        'records':records,'new_model_fits':0,'new_spectral_fits':0})
    c.preservation()
    print('ALPHA17_BOUNDED_TARGET_KEY_CHECK_COMPLETE; NO_TARGET_VALUES_DECODED')


if __name__=='__main__':
    try:main()
    except Exception:
        print('ALPHA17_TARGET_KEY_CHECK_REFUSED; DETAILS_REMAIN_LOCAL');raise SystemExit(2) from None
