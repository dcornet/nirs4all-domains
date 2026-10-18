"""Budgeted compact release evidence; existing numeric artifacts are immutable."""
from collections import Counter,defaultdict
import csv
import json
import os
from pathlib import Path
from alpha13_common import ROOT,PUBLIC,STATE,run,policy
from nirs4all_domains.storage import atomic_json,digest,fingerprint,tree_bytes


def read(path):return json.loads(Path(path).read_text())


def manifest():
    frozen=read(PUBLIC/'real-input-freeze.json');local=read(ROOT/'input-locators.json')
    artifacts=[{'path':p.relative_to(PUBLIC).as_posix(),'sha256':digest(p),'bytes':p.stat().st_size,'retention':'essential_evidence'}
        for p in sorted(PUBLIC.rglob('*')) if p.is_file() and p.name!='storage.json']
    value={'schema_version':1,'protocol_version':'domains.storage.v0.1','execution_id':fingerprint(['alpha13',frozen['freeze_id']]),
        'artifacts':artifacts,'cache_dependencies':[{'content_sha256':e['input_csv_sha256'],'bytes':Path(local[e['dataset_id']]['matrix']).stat().st_size,
            'provider':'Existing Datasets canonical X cache, separately source-rights admitted','access':'requires_authorization' if not e.get('reused_alpha12_reference') else 'public',
            'local_locator_key':e['dataset_id']+':X'} for e in frozen['entries']],
        'replay_grade':'requires_authorized_origin','measured_bytes':sum(p['bytes'] for p in artifacts),'optional_archives':[],
        'limitations':['Portable integrity verification does not reconstruct source X or native executed binaries.',
            'Exact scientific replay needs qualified provider/binary/controller hashes and authorized matching caches.',
            'Canonical/private-tier numeric caches and original archives are not redistributed.']}
    atomic_json(PUBLIC/'storage.json',value)


def main():
    journal=read(STATE/'journal.json');records=[]
    for r in journal['runs'].values():
        if r['status']=='computed' and (ROOT/'evidence'/r['artifact']).is_file():
            assert digest(ROOT/'evidence'/r['artifact'])==r['sha256']
            records.append({k:r[k] for k in ['execution_id','task_id','stage','attempt','contract','sha256','bytes','duration_seconds']})
    controlled=read(PUBLIC/'controlled-qualification.json');real=read(PUBLIC/'real-stability.json');extension=read(PUBLIC/'x-only-extension.json')
    original_entries={e['dataset_id']:e for e in read(PUBLIC/'real-input-freeze.json')['entries']}
    phases={p.stem:read(p) for p in (ROOT/'phases').glob('*.json') if not p.stem.endswith('.worker')}
    contract={'task':{'task_id':fingerprint(['alpha13','compact-release-publication'])},'phase':'compact-publication',
        'record_hashes':[r['sha256'] for r in records],'runner_sha256':digest(__file__),
        'real_stability_sha256':digest(PUBLIC/'real-stability.json'),'extension_sha256':digest(PUBLIC/'x-only-extension.json')}
    def build(folder):
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        plt.rcParams['svg.hashsalt']='nirs4all-domains-alpha13'
        source_index={digest(p):p.as_posix() for root in ['scripts','bridges/python/nirs4all_domains'] for p in Path(root).glob('*.py')}
        source_bindings={h:source_index[h] for r in records for key,h in r['contract'].items() if isinstance(h,str) and h in source_index}
        outputs={'execution-contracts.json':{'records':records,'source_bindings':source_bindings,
            'reused_legacy_transport':read(ROOT/'calibration-transport-reuse.json'),
            'measured_cost_review':read(ROOT/'calibration-storage-review.json'),
            'scientific_source_version':'0.1.0a13','editable_metadata_during_science':'0.1.0a12',
            'scope':'Exact executed source contracts, including cached original-binary attribution; not retroactive alpha13 wheel execution.'},
            'resources.json':{'phase_observations':phases,'real_reference_pca_fits':4,'real_resampling_pca_fits':720,'real_hdbscan_attempts':1448,
                'controlled_unique_pca_fits':6498,'controlled_hdbscan_attempts':12996,'engineering_parity_pca_fits':68,'engineering_parity_hdbscan_attempts':136,
                'supervised_real_model_fits':0,'spectral_archive_download_bytes':3822359+431935,'native_expanded_cache_unique_bytes':tree_bytes([ROOT/'datasets-cache']),
                'real_native_cli_peak_observed_bytes':real['native_cli_lifetime_peak_resident_bytes'],
                'native_peak_scope':'Actual Windows native CLI lifetime peak through last request, excluding Python; not combined with Python peaks.',
                'calibration_native_peak':'unavailable; measured worker peaks exclude native child',
                'storage_policy':policy(),'campaign_reservations_observed_before_publication':journal['reserved_campaign_bytes'],
                'failed_attempts_retained':True,'historical_cleanup_or_migration':False,'upstream_modifications':False},
            'source-hierarchy-extension.json':{'nodes':[{'dataset_id':e['dataset_id'],'source_view':'canonical:X','original_study_reference':original_entries[e['dataset_id']]['original_study_reference'],
                'original_source_url':original_entries[e['dataset_id']]['original_source_url'],'source_hash':e['source_content_sha256'],'identity_scope':'observation_conditional',
                'original_numeric_correspondence':read(PUBLIC/'sources/tablet-original-key-audit.json')['original_x_correspondence'] if 'tablet' in e['dataset_id'] else
                    {'status':'unavailable','reason':'ORIGINAL_MAT_OR_RDA_KEYED_NUMERIC_EQUIVALENCE_NOT_QUALIFIED','value':None},
                'reference_assay_closure':{'status':'unavailable','reason':'ORIGINAL_ASSAY_DEPENDENCIES_NOT_VERIFIED','value':None}}
                for e in extension['records']], 'new_original_study_candidates':2,'admitted_confirmation_studies':0,
                'soil_original_and_ohpl_package_views_are_not_independent_studies':True,'canonical_rows_are_not_independent_studies':True,'target_accessed':False},
            'findings.json':{'findings':[
                {'observation':'B20 leaves all 12 stable oracle setting cases inconclusive; B60 resolves them without false operational decisions in the tested controls.',
                 'confidence':'Controlled decision-layer evidence, dependent settings; no real prevalence estimate.','consequence':'Pair exposure can limit power even under perfect grouping.','action':'Use the frozen revised design with per-task prospective feasibility gates.'},
                {'observation':'The real revised study has 6 robust, 17 fragile and 1 insufficient setting; no source passes every combination.',
                 'confidence':'Conditional complete-source algorithmic resampling, not independent biological sampling.','consequence':'More draws improve support without guaranteeing robust partitions.','action':'Retain every representation/setting and missingness state; do not select by future scores.'},
                {'observation':'Cartilage has four fragile raw and four robust SNV settings.',
                 'confidence':'Whole verified location components within five joints, donor/assay closure unresolved.','consequence':'Representation changes structural reproducibility.','action':'Keep raw/SNV prospectively locked for any later independently admitted predictive study.'},
                {'observation':'Biotron raw/.6/min_cluster_size12 has 52 eligible nontrivial ARI comparisons among 60 successful fits.',
                 'confidence':'Exact recorded conditional support count.','consequence':'Its 90 percent comparison-support gate fails despite adequate pair exposure.','action':'Report insufficient information, preserve degenerate comparisons and do not relax the gate.'},
                {'observation':'All 310 tablet spectra and axes match the original flat source through explicit observation/source keys.',
                 'confidence':'Exact field-projected transport equality, no target cells.','consequence':'Observation correspondence is strengthened; physical/assay independence remains unresolved.','action':'Keep original stability scope and obtain original dependency ownership before modeling.'},
                {'observation':'No new task satisfies original physical/reference closure and frozen group-safe model admission.',
                 'confidence':'Documented admission gaps, not a scientific verdict on H1-H5.','consequence':'Zero new supervised fits and zero admitted confirmation studies.','action':'Resolve source ownership and study-level power before a bounded PLS/Ridge confrontation.'}],
                'universal_shortcut_score':None}}
        paths=[]
        for name,value in outputs.items():
            path=folder/name;atomic_json(path,value);paths.append((name,path))
        table=folder/'stability-matrix.csv'
        with table.open('w',newline='',encoding='utf-8') as out:
            w=csv.writer(out);w.writerow(['dataset_id','representation','fraction','min_cluster_size','classification','eligible_ari_draws','attempted_draws','median_ari','ari_p10','pair_support'])
            for report in real['reports']:
                record=read(report['path'])
                for condition,state in record['conditions'].items():
                    if state['status']!='computed':continue
                    for setting in state['value']['settings']:
                        if setting['status']!='computed':continue
                        s=setting['value'];w.writerow([record['dataset_id'],condition.split('.')[0],condition.split('.',1)[1],s['min_cluster_size'],s['classification'],s['eligible_ari_draws'],s['attempted_draws'],s['ari_summary']['value']['median'] if s['ari_summary']['status']=='computed' else '',s['ari_p10'],s['gates']['pair_support']])
        paths.append(('stability-matrix.csv',table))
        fig,axes=plt.subplots(1,2,figsize=(10,4));colors={'robust_structure':'#287c8e','fragile_structure':'#c76a43','insufficient_information':'#abb4bc'}
        left=[controlled['prefix_classifications'],controlled['full_classifications']];right=[Counter(r['per_setting_classifications']) for r in real['reports']]
        for ax,counts,names,title in [(axes[0],left,['First 20','All 60'],'Controlled fixed-X settings'),(axes[1],right,['Tablets','Cartilage','Biotron'],'Real conditional settings')]:
            bottoms=[0]*len(counts)
            for cls,color in colors.items():
                heights=[v.get(cls,0) for v in counts];ax.bar(names,heights,bottom=bottoms,label=cls.replace('_structure','').replace('_',' '),color=color)
                bottoms=[a+b for a,b in zip(bottoms,heights)]
            ax.set_title(title);ax.set_ylabel('Setting cases');ax.spines[['top','right']].set_visible(False)
        axes[1].legend(fontsize=8);fig.suptitle('Support and fragility remain separate');fig.text(.5,.015,'Settings and perturbations are not independent studies; no shortcut probability.',ha='center',fontsize=9)
        fig.tight_layout(rect=[0,.05,1,.92]);figure=folder/'stability-support.svg';fig.savefig(figure,metadata={'Date':None});plt.close(fig)
        paths.append(('figures/stability-support.svg',figure))
        artifacts=[{'path':name,'scratch_name':path.name,'sha256':digest(path),'bytes':path.stat().st_size} for name,path in paths]
        return {'artifacts':artifacts,'target_accessed':False,'supervised_fits':0,'publication_bytes':sum(a['bytes'] for a in artifacts)}
    plan={'inputs':[],'scratch_bytes':3*1024*1024,'evidence_bytes':131072,'expected_fits':0,'expected_permutations':0,
        'uncertainty':'Compact derived tables, SVG and source/contracts/resource audits. Existing numerical artifacts are shared without duplication.'}
    store,receipt,value=run(contract,'P4',plan,build)
    scratch=store.scratch/receipt['execution_id']/'P4'/str(receipt['attempt'])
    for artifact in value['artifacts']:
        origin=scratch/artifact['scratch_name'];target=PUBLIC/artifact['path'];assert digest(origin)==artifact['sha256']
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert digest(target)==artifact['sha256']
        else:os.link(origin,target)
    atomic_json(ROOT/'publication-receipt.json',receipt)
    manifest();print(json.dumps({'publication_bytes':value['publication_bytes'],'artifacts':len(value['artifacts'])}))


if __name__=='__main__':main()
