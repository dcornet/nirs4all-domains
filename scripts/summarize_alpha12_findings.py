"""No-fit findings with observation, confidence, consequence and action."""
from collections import Counter
import json
from pathlib import Path
from nirs4all_domains.storage import atomic_json,digest


def main():
    root=Path('docs/benchmarks/alpha12');matrix=json.loads((root/'structural-matrix.json').read_text())
    summary=matrix['descriptive_distributions'];settings=Counter();gates=Counter()
    for path in (root/'stability').glob('*.json'):
        for s in json.loads(path.read_text())['settings']:
            if s['status']=='computed':
                settings[s['value']['classification']]+=1
                gates.update(k for k,v in s['value']['gates'].items() if not v)
    def finding(key,observation,confidence,consequence,action):
        return dict(id=key,observation=observation,confidence=confidence,consequence=consequence,action=action)
    result={'protocol_version':'domains.unsupervised.v0.1','matrix_sha256':digest(root/'structural-matrix.json'),
        'counts':matrix['counts'],'setting_classifications':dict(settings),'failed_gates_overlapping':dict(gates),
        'findings':[
        finding('coverage',{'catalog_entries':42,'raw_snv_sources':39,'variable_metadata_sources':37,
            'complete_neighbors':22,'partial_query_neighbors':17},
            'Exact executed-record counts; not independent-population prevalence.',
            'Two publicly resolved EcoSIS admissions extend X-only coverage; all blockers remain visible.',
            'Retain exact source/version/rights and query support in all comparisons.'),
        finding('representation',{'partition_ari':summary['representation_pairs']['primary_partition_ari'],
            'k8_overlap':summary['representation_pairs']['full_axis_k8_set_overlap']},
            'Native paired geometry on identical IDs/axes: 37 nontrivial ARIs and 39 neighbor comparisons.',
            'Observed partitions/neighbors are representation-sensitive; this does not identify nuisance removal.',
            'Carry raw/SNV descriptors separately into frozen future pipeline-by-split hypotheses.'),
        finding('dimension',{'raw':summary['raw']['effective_dimension'],'snv':summary['snv']['effective_dimension'],
            'n_exact_per_representation':12,'n_unavailable_per_representation':27},
            'Exact full moments on the admitted subset; the subset is computationally selected.',
            'Truncated PCA is useful without pretending to provide full effective dimension.',
            'Keep missing full moments explicit and propose a public streamed exact-moment API.'),
        finding('stability',{'sources':7,'draws':560,'hdbscan_attempts':1120,'classifications':dict(settings),
            'overall_robust_sources':0,'failed_gates_overlapping':dict(gates)},
            'Observed conditional algorithmic stability; no biological intervals. Pair exposure at .6 is underpowered.',
            'Four supported combinations do not qualify whole sources; insufficient support does not establish fragility.',
            'Calibrate pair-panel size/exposure on controlled X before any new real-data stability extension.'),
        finding('source_overlap',{'historical_physical_ownership_entries':4,'original_key_namespaces_rechecked':2,
            'cited_reference_groups':70,'independent_study_count':None},
            'Exact namespace/key proof for Cartilage/litter; unknown cross-view physical overlap elsewhere.',
            'Catalog entries, related views and citations cannot support independent-study prevalence.',
            'Resolve study/population closure before discovery/confirmation separation.'),
        finding('paired_views',{'n_matched_original_objects':321,'parent_counts':[322,321],
            'contrast_ref':'paired-x-comparison.json'},
            'Original ID join and field projection exclude Y; no biological closure claim.',
            'Preparation changes observed geometry on the same objects, not new-object generalization.',
            'Keep the separately qualified historical train-fitted support probe distinct.'),
        finding('hypotheses',{'real_supervised_model_fits':0,'tabpfn_fits':0,'hypotheses':'H1-H5'},
            'Frozen X-only indicators and outcome definitions; predictive validity remains untested.',
            'No shortcut-learning or future performance claim is established by alpha.12.',
            'Test on independently separated original studies, retaining potential falsification cases.')],
        'test_target_accessed':False,'model_performance_used':False,'universal_shortcut_score':None}
    atomic_json(root/'findings.json',result)


if __name__=='__main__':main()
