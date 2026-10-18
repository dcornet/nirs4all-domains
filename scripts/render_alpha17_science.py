"""Render ordinary aggregate science and reuse historical supervised scores."""
import json
import os
from pathlib import Path

from nirs4all_domains.falsification import response
from nirs4all_domains.storage import atomic_json, digest


def main():
    source=Path('docs/benchmarks/alpha11/litter-model-results.json')
    old=json.loads(source.read_text())
    target=json.loads(Path('docs/benchmarks/alpha11/litter-admission.json').read_text())['specification']['target']
    rows=[]
    for model,item in old['models'].items():
        for result in item['designs']:
            if result['status']!='computed':
                rows.append({'model':model,'result':result});continue
            r=result['value'];scores=r['scores']['value'];null=r['null_scores']['value']['rmse']['value']
            endpoint={'target_definition':target['name'],'target_unit':target['unit'],
                'evaluation_ids':[v['physical_sample_id'] for v in r['oof']],
                'rmse':scores['rmse']['value'],'null_rmse':null,
                'metrics_from_native_provider':True,'null_fitted_on_training_only':True}
            skill=response(endpoint,endpoint)['value']['reference_skill']
            rows.append({'model':model,'historical_design_id':r['design_id'],
                'rmse':scores['rmse'],'r2':scores['r2'],'null_rmse':null,'null_relative_skill':skill,
                'n_evaluation_observations':len(endpoint['evaluation_ids']),
                'retained_target_accessed':r['test_target_accessed']})
    atomic_json('docs/benchmarks/alpha17/retrospective-anchors.json',{
        'protocol':'domains.alpha17.retrospective_scores.v0.1','source_report':source.as_posix(),
        'source_report_sha256':digest(source),'target':{'name':target['name'],'unit':target['unit']},
        'rows':rows,'new_model_fits':0,'original_population_count':1,
        'scope':'Historical litter development-group CV; seeds and models are repeated views of one discovery population.',
        'limitations':['Retrospective score reuse, not a prospective H1–H5 test.',
            'No new stress comparison or independent-study effect estimated.',
            'Model and preprocessing effects cannot be attributed to structural susceptibility alone.',
            'Full-source X descriptors and development-only evaluation have different sampling scopes.']})
    os.environ['MPLCONFIGDIR']=str(Path('.audit/alpha17/mpl-cache').resolve())
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    matplotlib.rcParams['svg.fonttype']='none'
    value=json.loads(Path('docs/benchmarks/alpha17/structural-summary.json').read_text())
    distributions=value['comparison']['distributions']
    fig,axes=plt.subplots(1,3,figsize=(10,3.3))
    for axis,metric,title in zip(axes,['pc1_fraction','noise_8','raw_snv_ari'],
            ['PC1 explained variance','HDBSCAN noise fraction','Raw/SNV partition ARI']):
        reps=['raw'] if metric=='raw_snv_ari' else ['raw','snv']
        for index,rep in enumerate(reps):
            d=next(x for x in distributions if x['metric']==metric and x['representation']==rep)
            s=d['summary']['value']
            axis.hlines(index,s['min'],s['max'],color='#aaa',linewidth=1)
            axis.hlines(index,s['q25'],s['q75'],color='#2166ac',linewidth=6)
            axis.plot(s['median'],index,'o',color='#b2182b',markersize=5)
        axis.set_yticks(range(len(reps)),['raw / SNV' if metric=='raw_snv_ari' else r.upper() for r in reps])
        axis.set_xlim(0,1);axis.set_ylim(-.7,len(reps)-.3)
        axis.set_title(title+'\n'+('38 valid views' if metric=='raw_snv_ari' else '40 views'),fontsize=10)
        axis.grid(axis='x',alpha=.2)
    fig.suptitle('Source-view medians, interquartile ranges and observed ranges',fontsize=11)
    fig.text(.5,.015,'Permitted aggregate subset; source views are not independent studies.',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.06,1,.93])
    out=Path('docs/figures/alpha17-structure.svg');out.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(out,metadata={'Date':None,'Creator':'nirs4all-domains aggregate science'})
    plt.close(fig)
    print('ALPHA17_PUBLIC_SCIENTIFIC_FIGURE_AND_RETROSPECTIVE_SCORES_RENDERED')


if __name__=='__main__':main()
