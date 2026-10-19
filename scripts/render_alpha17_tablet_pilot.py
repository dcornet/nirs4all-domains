"""Render already published aggregate errors; no fits or numerical backend."""
import json
import os
from pathlib import Path


def main():
    os.environ['MPLCONFIGDIR']=str(Path('.audit/alpha17/mpl-cache').resolve())
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    matplotlib.rcParams['svg.fonttype']='none'
    matplotlib.rcParams['svg.hashsalt']='nirs4all-domains-alpha17-tablet'
    value=json.loads(Path('docs/benchmarks/alpha17/tablet-pilot-summary.json').read_text())
    rows=sorted(value['contexts'],key=lambda r:r['source_type']);fig,ax=plt.subplots(figsize=(8,4))
    for offset,model,color,label in [(-.25,'raw_pls','#2166ac','Raw PLS'),(0,'raw_ridge','#b2182b','Raw Ridge'),(.25,None,'#999999','Training-only null')]:
        errors=[r['models'][model or 'raw_pls']['scores' if model else 'null']['value']['rmse']['value'] for r in rows]
        ax.bar([i+offset for i in range(len(rows))],errors,width=.24,color=color,label=label)
    ax.set_xticks(range(len(rows)),[r['source_type']+f" (n={r['n_evaluation']})" for r in rows])
    ax.set_xlabel('Held-out original Type context');ax.set_ylabel('RMSE, percentage points mass/mass')
    ax.set_title('Exploratory context holdout: pooled improvement conceals an adverse context')
    ax.legend(frameon=False);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    fig.text(.5,.015,'All Type A targets are below training support. Physical/assay independence remains unknown.',ha='center',fontsize=8)
    output=Path('docs/figures/alpha17-tablet-pilot.svg')
    fig.tight_layout(rect=[0,.04,1,1]);fig.savefig(output,metadata={'Date':None,'Creator':'nirs4all-domains aggregate science'});plt.close(fig)
    output.write_text('\n'.join(line.rstrip() for line in output.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8')
    print('ALPHA17_TABLET_AGGREGATE_FIGURE_RENDERED; NO_FITS')


if __name__=='__main__':main()
