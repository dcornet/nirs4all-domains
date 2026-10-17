"""Render compact tables and a standalone scientific SVG from published metrics."""
import csv
import json
from pathlib import Path

ROOT=Path('docs/benchmarks/alpha12')


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    matrix=json.loads((ROOT/'structural-matrix.json').read_text());rows=matrix['entries']
    aliases={r['dataset_id']:f'E{i+1:02}' for i,r in enumerate(rows)}
    table=[]
    for row in rows:
        a,b=(row['representations'][k] for k in ('raw','snv'))
        record={'alias':aliases[row['dataset_id']],'dataset_id':row['dataset_id'],'source_id':row['source_id'],
            'observations':row['source_dimensions']['n_observations'],'bands':row['source_dimensions']['n_variables'],
            'identity_evidence':row['identity_evidence'],'raw_status':a['status'],'snv_status':b['status'],
            'raw_reason':a['reason'],'snv_reason':b['reason']}
        for representation,value in [('raw',a),('snv',b)]:
            if value['status']=='computed':
                p=value['value'];c=p['cluster_settings'][0]['value'];n=p['neighborhoods']['full_axis']
                record.update({representation+'_retained_fraction':p['pca']['retained_variance_fraction'],
                    representation+'_pc1_fraction':p['pca']['pc1_fraction'],representation+'_clusters':c['n_clusters'],
                    representation+'_noise_fraction':c['noise_fraction'],representation+'_neighbor_mode':n['mode'],
                    representation+'_queries':n['n_query']})
        agreement=row['representation_agreement']
        if agreement['status']=='computed':
            ari=agreement['value']['partitions'][0]['value']['ari_including_noise']
            record['raw_snv_primary_ari']=ari['value']
            record['raw_snv_k8_set_overlap']=agreement['value']['full_axis_neighbors']['metrics'][-1]['set_overlap']['mean']
        s=row['structural_stability'];record['stability_status']=s['status']
        record['stability_classification']=s['value']['classification'] if s['status']=='computed' else ''
        table.append(record)
    columns=list(dict.fromkeys(k for r in table for k in r))
    with (ROOT/'structural-matrix.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=columns,lineterminator='\n');writer.writeheader();writer.writerows(table)
    lines=['# Alpha.12 public structural coverage','',
        '42 catalog entries; 39 complete-population raw/SNV profiles. Source views and citations are not independent studies.',
        'Full-axis neighborhoods use all reference rows: 22 complete-source query censuses, 17 prespecified partial-query descriptions.',
        '', '| Alias | Dataset/source | Observations × bands | Full-axis queries | Resampling |','|---|---|---:|---|---|']
    for r in table:
        label=r['dataset_id'];mode=r.get('raw_neighbor_mode',r['raw_status'])
        if 'raw_queries' in r:mode+=f" ({r['raw_queries']})"
        stability=r['stability_classification'] or r['stability_status']
        lines.append(f"| {r['alias']} | {label} | {r['observations']} × {r['bands']} | {mode} | {stability} |")
    lines.extend(['','Full identities, reasons, provider scope, partial-query uncertainty and hashes: [JSON matrix](structural-matrix.json).',
        '[CSV descriptors](structural-matrix.csv) provide the stable alias mapping. [Source hierarchy](source-hierarchy.json) retains unknown overlap.',
        'Resampling labels describe observed algorithmic reproducibility; all-noise/insufficient support is not low structural susceptibility.'])
    (ROOT/'COVERAGE.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    selected=[r for r in table if r['raw_status']==r['snv_status']=='computed']
    plt.rcParams.update({'svg.hashsalt':'nirs4all-domains-alpha12','font.size':9})
    fig,axes=plt.subplots(2,2,figsize=(11.6,8.5),layout='constrained')
    x=[r['raw_pc1_fraction'] for r in selected];y=[r['snv_pc1_fraction'] for r in selected]
    axes[0,0].scatter(x,y,s=24,alpha=.7);axes[0,0].plot([0,1],[0,1],color='.65',lw=.8)
    axes[0,0].set(xlabel='Raw first-PC fraction',ylabel='SNV first-PC fraction',xlim=(0,1.02),ylim=(0,1.02),title='Dominant variance changes with representation')
    x=[r['raw_clusters'] for r in selected];y=[r['snv_clusters'] for r in selected]
    limit=max(x+y)+1
    axes[0,1].scatter(x,y,s=24,alpha=.7);axes[0,1].plot([0,limit],[0,limit],color='.65',lw=.8)
    axes[0,1].set(xlabel='Raw primary HDBSCAN groups',ylabel='SNV primary HDBSCAN groups',title='Parameter-specific fragments, not stable populations')
    x=[r['raw_noise_fraction'] for r in selected];y=[r['snv_noise_fraction'] for r in selected]
    axes[1,0].scatter(x,y,s=24,alpha=.7);axes[1,0].plot([0,1],[0,1],color='.65',lw=.8)
    axes[1,0].set(xlabel='Raw noise fraction',ylabel='SNV noise fraction',xlim=(-.02,1.02),ylim=(-.02,1.02),title='Noise changes do not identify nuisance removal')
    ordered=sorted(selected,key=lambda r:r['raw_snv_k8_set_overlap'])
    colors=['#2166ac' if r['raw_neighbor_mode']=='complete_source' else '#d89032' for r in ordered]
    axes[1,1].bar(range(len(ordered)),[r['raw_snv_k8_set_overlap'] for r in ordered],color=colors,width=.85)
    axes[1,1].set_xticks(range(len(ordered)),[r['alias'] for r in ordered],rotation=90,fontsize=5.5)
    axes[1,1].set(ylim=(0,1.02),ylabel='Mean shared k=8 neighbor fraction',xlabel='Source alias; mapping in CSV',title='Raw/SNV neighborhood identity persistence')
    axes[1,1].legend(handles=[Patch(color='#2166ac',label='Query census'),Patch(color='#d89032',label='Query sample')],fontsize=7,loc='upper left')
    for row in selected:
        if row['stability_status']=='computed':
            axes[0,0].annotate(row['alias'],(row['raw_pc1_fraction'],row['snv_pc1_fraction']),fontsize=6,xytext=(3,2),textcoords='offset points')
    fig.suptitle('Alpha.12: observable structural descriptors across 39 public source views',fontsize=13)
    fig.supxlabel('Related views can share objects. Partial queries estimate observed-query geometry; no biological uncertainty or shortcut probability is shown.',fontsize=8)
    destination=ROOT/'figures/representation-sensitivity.svg';destination.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(destination,metadata={'Date':None,'Creator':'nirs4all-domains alpha.12 / Matplotlib '+matplotlib.__version__})
    # Matplotlib text output uses platform newlines; portable SHA binds LF bytes.
    destination.write_bytes(b'\n'.join(line.rstrip() for line in destination.read_bytes().splitlines())+b'\n')
    preview=Path('.audit/alpha12/representation-sensitivity.png');preview.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(preview,dpi=120);plt.close(fig)
    print(json.dumps({'table_rows':len(table),'figure':destination.as_posix(),'figure_bytes':destination.stat().st_size}))


if __name__=='__main__':main()
