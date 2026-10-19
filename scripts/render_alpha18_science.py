"""Human-readable bank tables, figures and README status from shared matrices."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['svg.hashsalt']='nirs4all-domains-alpha18'
import matplotlib.pyplot as plt
from nirs4all_domains.storage import atomic_json

ROOT=Path('docs/campaign')


def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8'))


def main():
    # The private freeze retains exact local execution locators; the outgoing
    # hash map uses repository-relative POSIX paths on every platform.
    freeze_path=ROOT/'prospective-freeze.json';freeze=json.loads(freeze_path.read_text(encoding='utf-8'))
    normalized={}
    for name,sha in freeze['controller_sha256'].items():
        path=Path(name)
        if path.is_absolute():path=path.relative_to(Path.cwd())
        normalized[path.as_posix()]=sha
    freeze['controller_sha256']=normalized;atomic_json(freeze_path,freeze)
    x=read('structural-matrix.json');e=read('experiment-matrix.json');c=read('confrontation.json');s=read('status.json')
    rows=[r for source in x['sources'] if source['aggregates']['status']=='computed' for r in source['aggregates']['value']]
    bykey={(r['view_id'],r['representation']):r for r in rows}
    pairs=[(r,bykey[(r['view_id'],'snv')]) for r in rows if r['representation']=='raw' and (r['view_id'],'snv') in bykey]
    fig,ax=plt.subplots(figsize=(6,5),layout='constrained')
    ax.scatter([a['metrics']['pc1_fraction']['value'] for a,b in pairs],[b['metrics']['pc1_fraction']['value'] for a,b in pairs],alpha=.75)
    ax.plot([0,1],[0,1],color='grey',linestyle='--');ax.set(xlabel='Raw PC1 variance fraction',ylabel='SNV PC1 variance fraction',title=f'Source-permitted paired geometry ({len(pairs)} views)',xlim=(0,1.02),ylim=(0,1.02))
    fig.savefig(ROOT/'representation-geometry.svg',metadata={'Date':None});fig.savefig(ROOT/'representation-geometry.png',dpi=160);plt.close(fig)
    joined=c['joined_source_views'];fig,axes=plt.subplots(1,2,figsize=(11,4.7),layout='constrained')
    for family,color in [('pls','#1f77b4'),('ridge','#d95f02')]:
        rr=[r for r in joined if r['skill_across_targets'][family]['status']=='computed' and r['descriptors']['pc1_fraction']['status']=='computed']
        axes[0].scatter([r['descriptors']['pc1_fraction']['value'] for r in rr],[r['skill_across_targets'][family]['value']['median'] for r in rr],label=f'{family.upper()} (n={len(rr)})',alpha=.7,color=color)
    rr=[r for r in joined if all(r['skill_across_targets'][f]['status']=='computed' for f in ['pls','ridge'])]
    axes[1].scatter([r['skill_across_targets']['pls']['value']['median'] for r in rr],[r['skill_across_targets']['ridge']['value']['median'] for r in rr],alpha=.75)
    axes[0].axhline(0,color='grey',linestyle='--');axes[1].axhline(0,color='grey',linestyle='--');axes[1].axvline(0,color='grey',linestyle='--')
    axes[0].set(xlabel='Frozen raw PC1 fraction',ylabel='Median within-view target CV skill',title='Exploratory geometry/performance comparison');axes[0].legend()
    axes[1].set(xlabel='PLS median target CV skill',ylabel='Ridge median target CV skill',title='Fixed models on shared target populations')
    fig.savefig(ROOT/'descriptor-performance.svg',metadata={'Date':None});fig.savefig(ROOT/'descriptor-performance.png',dpi=160);plt.close(fig)
    md=['# Exploratory reference results','',
        'One row per source/target; source terms control numeric publication. Negative skill and failures are retained. CV is not a certificate of biological independence.','',
        'Numeric identifiers and category codes have no regression interpretation. Their executed diagnostic counts remain visible; diagnostic values stay in the local audit and are excluded from quantitative synthesis. Context/derived/QC endpoints are explicitly tagged in the JSON matrix.','',
        '| Source / target | State | n evaluated | Group policy | PLS skill | Ridge skill |','|---|---|---:|---|---:|---:|']
    for t in e['tasks']:
        v=t['aggregates']['value'] if t['aggregates']['status']=='computed' else {};skills=[]
        for family in ['pls','ridge']:
            p=v.get('families',{}).get(family,{}).get('pooled',{})
            skill=p.get('value',{}).get('skill',{}) if p.get('status')=='computed' else {}
            skills.append(f"{skill['value']:.4f}" if skill.get('status')=='computed' else 'unavailable')
        md.append(f"| {t['view_id']} / {t['target']} | {t['execution_state']} | {v.get('n_evaluated','-')} | {v.get('evaluation_scope','-')} | {' | '.join(skills)} |")
    (ROOT/'experiment-matrix.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    status_lines=['| Scientific unit | Executed full-bank status |','|---|---:|',
        f"| Catalog entries / declared source views | {s['catalog_entries']} / {s['declared_source_views']} |",
        f"| Complete raw/SNV source profiles | {s['computed_source_views']} |",
        f"| Partial profiles / failed X attempts | {s['partial_source_views']} / {s['failed_source_views']} |",
        f"| Views with source-permitted public profile values | {s['publishable_source_views']} |",
        f"| Resource-deferred / analysis-not-authorized views | {s['resource_deferred_views']} / {s['analysis_not_authorized_views']} |",
        f"| Declared source/target tasks | {s['declared_target_tasks']} |",
        f"| Complete / partial reference tasks | {s['reference_task_counts'].get('computed',0)} / {s['reference_task_counts'].get('partial',0)} |",
        f"| Complete primary quantitative reference tasks | {s['completed_primary_quantitative_tasks']} |",
        f"| Successful native reference fits / attempts | {s['model_fit_successes']} / {s['model_fit_attempts']} |",
        f"| Public source views joined to quantitative outcomes | {s['public_joined_source_views']} |"]
    path=Path('README.md');text=path.read_text(encoding='utf-8');start='<!-- scientific-status:start -->';end='<!-- scientific-status:end -->'
    before,rest=text.split(start,1);_,after=rest.split(end,1);path.write_text(before+start+'\n'+'\n'.join(status_lines)+'\n'+end+after,encoding='utf-8')
    text=path.read_text(encoding='utf-8')
    lines=[]
    for line in text.splitlines():
        if line.startswith('| M1 '):line=f"| M1 - Comprehensive structural characterization | Multidimensional X-only profile for every accessible eligible source | {s['computed_source_views']}/171 complete raw/SNV profiles; every source accounted for |"
        if line.startswith('| M3 '):line=f"| M3 - Broad supervised confrontation | Source x target x estimator x evaluation-design matrix | {s['completed_primary_quantitative_tasks']} complete primary quantitative tasks, plus context and plot sensitivity; failures retained |"
        lines.append(line)
    path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    attribution=['# Original source locators and aggregate scope','',
        'Public catalog names and URLs are used with owner authorization. Numeric publication follows source-specific aggregate permissions, independently of catalog tier. Raw data are not redistributed. Source locators below preserve attribution and let readers inspect original study terms.','',
        'The two aquatic-plant sources retain CC BY-NC 2.0 noncommercial attribution requirements documented in [the original source review](../benchmarks/alpha17/X-extension-summary.json). Other source notices and historical citations remain linked in [release history](../RELEASE_HISTORY.md).','']
    inventory=read('bank-inventory.json');permitted={r['dataset_id'] for r in x['sources'] if r['aggregate_permission'] in ['allowed','allowed_noncommercial']}
    for entry in inventory['entries']:
        if entry['dataset_id'] in permitted:
            attribution.append('- '+entry['dataset_id']+': '+', '.join('[original source]('+u+')' for u in entry['source_urls']))
    (ROOT/'source-attribution.md').write_text('\n'.join(attribution)+'\n',encoding='utf-8')
    atomic_json(ROOT/'rendered-status.json',{'status_source':'status.json','source_counts':s['source_execution_counts'],'reference_counts':s['reference_task_counts']})
    for path in [*ROOT.glob('*.svg'),*ROOT.glob('*.md')]:
        path.write_text('\n'.join(line.rstrip() for line in path.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8')
    print('RENDERED_SHARED_BANK_MATRICES_FIGURES_AND_README')

if __name__=='__main__':main()
