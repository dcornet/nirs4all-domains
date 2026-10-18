"""Freeze descriptor families and pre-outcome roles; no target cells or models."""
import json
from pathlib import Path
from nirs4all_domains.bank import schema_check
from nirs4all_domains.dependence import state
from nirs4all_domains.falsification import freeze_roles
from nirs4all_domains.storage import atomic_json,digest,fingerprint

ROOT=Path('docs/benchmarks/alpha13')


def ref(path):return {'path':path,'sha256':digest(path)}


def main():
    common_controls=['Exact target definition and units','Whole physical/reference dependency components',
        'Matched training size and evaluation IDs','Independent study/group counts','Target-range extrapolation and composition',
        'Frozen model family/preprocessing','Fold-local fit/selection/refit; retained targets sealed']
    families=[
        ('H1',['stability.raw.six','stability.raw.eight','stability.snv.six','stability.snv.eight'],
         ['structural_stability.summary_refs -> settings[min_cluster_size=8,12].value.ari_summary/ari_p10/noise_agreement_p10/cluster_pair_support',
          'alpha13 conditions[raw,snv;fraction=.6,.8] -> domains.stability_power.v0.2 settings[8,12]'],
         'Raw/SNV, both fractions and both fixed parameters; original and revised support protocols retain distinct versions.',
         'Better-supported separation may anticipate greater structural-holdout deterioration.',
         'Matched D_RMSE and D_skill under admissible structural versus reference designs.',
         ['Supported stable separation with good transfer','Unstable partitions with fragile prediction']),
        ('H2',['raw.full_axis.radius_0.01.fraction'],
         ['representations.raw.value.neighborhoods.full_axis.relative_proximity[radius=.01].fraction',
          'Separately admitted train-fitted evaluation-neighbor analogue, never a full-source substitution'],
         'k=8 identity neighborhoods; distance/sqrt(full representation covariance trace); exact census and sampled queries kept distinct.',
         'Strong neighborhood overlap may favor in-support evaluation relative to genuine transfer.',
         'Matched D_RMSE/D_skill under independently admitted population transfer.',
         ['Strong overlap without reference advantage','Weak overlap with good transfer']),
        ('H3',['raw_snv.primary_partition_ari','raw_snv.full_axis.k8_set_overlap'],
         ['representation_agreement.value.partitions[0].value.ari_including_noise',
          'representation_agreement.value.full_axis_neighbors.metrics[k=8].set_overlap.mean'],
         'Identical original observations/axes and query IDs; raw/SNV fixed without HPO.',
         'Representation disagreement may anticipate pipeline-specific structural sensitivity.',
         'D_RMSE_PLS minus D_RMSE_Ridge, plus prespecified raw/SNV interaction on matched IDs.',
         ['Large geometric change with negligible model-response interaction','Similar responses across pipelines despite structural disagreement']),
        ('H4',['raw.pca.pc1_fraction','raw.pca.retained_variance_fraction','snv.pca.pc1_fraction','snv.pca.retained_variance_fraction'],
         ['representations[raw,snv].value.pca.pc1_fraction/retained_variance_fraction',
          'Separately qualified train-fitted continuous spectral support'],
         'At most 20 PCs with independent full trace; within-source dimensionless fractions.',
         'Continuous support extrapolation may matter without credible discrete groups.',
         'Matched error/skill deterioration under prespecified support changes.',
         ['Large support shifts with little deterioration','Predictions survive extrapolation despite weak group evidence']),
        ('H5',['full_axis.seven_registered_proximity_radii','independently_audited_identity_tier'],
         ['representations[raw,snv].value.neighborhoods.full_axis.relative_proximity',
          'identity_evidence and original physical/reference closure proofs'],
         'All seven frozen relative radii, identity provenance as a separate variable; no spectral-to-physical merge.',
         'Proximity with initially uncertain identities may identify split-validity changes after actual closure.',
         'Dependency-closure and split-validity audit; not a forced error-correlation endpoint.',
         ['Initially uncertain close objects verified independent without validity change','Closure has no apparent-performance effect under an admissible paired design'])]
    bindings=[]
    for h,ids,paths,scale,prediction,outcome,falsification in families:
        bindings.append({'hypothesis_id':h,'primary_descriptor_ids':ids,'descriptor_paths':paths,
            'representation_and_scale':scale,'population_scope':'Exact source/content/observation population; study relations and query support retained.',
            'provider':'Methods 1.3.6 / ABI 2.19 through public Preflight; DAG-ML 0.3.41 for any later admitted model.',
            'missingness_rule':'Unavailable/insufficient/nontrivial support failures remain missing, never favorable zero; no post-response family selection.',
            'qualitative_prediction':prediction,'future_response':outcome,'controls':common_controls,
            'effective_independent_support':'Independent original studies for confirmation; physical/assay groups within a study are not additional studies.',
            'admissible_falsification':falsification,
            'secondary_policy':'Other locked parameter/radius/representation descriptors are exploratory secondary comparisons; no selection by future scores.'})
    roles=[]
    for name in ['ecosis-ca2023','perten','litter-2024']:
        roles.append({'source_id':'history:'+name,'original_study_id':'study:'+name,'population_namespace':'historical:'+name,
            'role':'discovery','original_study_verified':False,'physical_reference_closure_verified':False,
            'untouched_outcomes':False,'exact_task_and_splits_frozen':False})
    candidates=[{'dataset_id':name,'candidate_original_study':study,'source_metadata_ref':source,
        'role':'not_admitted_yet','reference_and_assay_ownership':'awaiting_original_key_audit','outcomes_accessed':False}
        for name,study,source in [('ucph_tablet_nir','Dyrby et al. 2002 pharmaceutical tablets','https://ucphchemometrics.com/tablet/'),
            ('ohpl_soil_nir','Rinnan and Rinnan 2007 Abisko soil: 36 plots, three subsamples','https://ucphchemometrics.com/soilnir/'),
            ('ohpl_beer_nir','Norgaard et al. 2000 original beer experiment','https://github.com/nanxstats/OHPL/blob/master/man/beer.Rd'),
            ('ohpl_wheat_nir','Kalivas 1997 original wheat experiment','https://github.com/nanxstats/OHPL/blob/master/man/wheat.Rd')]]
    value={'schema_version':1,'protocol_version':'domains.falsification.v0.1',
        'hypothesis_register_ref':ref('docs/ALPHA12_HYPOTHESIS_REGISTER.md'),'future_outcome_ref':ref('docs/ALPHA12_FUTURE_OUTCOME_CONTRACT.md'),
        'operational_preregistration_ref':ref('docs/ALPHA13_SUPERVISED_PREREGISTRATION.md'),'descriptor_bindings':bindings,
        'study_roles':freeze_roles(roles,[]),'candidate_sources':candidates,
        'model_anchors':{'pls_components':[1,2,3],'ridge_alphas':[.01,.1,1.,10.,100.],
            'primary_preprocessing':'raw','prespecified_secondary':'native SNV','grid_selection':'native grouped inner CV only',
            'fast_aom':'requires separate admission/budget','tabpfn':'deferred, no installation or weights'},
        'response_definitions':{'D_RMSE':'RMSE_stress - RMSE_reference','skill':'1 - RMSE/RMSE_null',
            'D_skill':'S_stress - S_reference','interaction':'D_RMSE_PLS - D_RMSE_Ridge',
            'zero_null':'unavailable','unmatched_evaluation':'descriptive only; no pure structural treatment effect',
            'single_task_verdict':'potential counterexample, no automatic study-level rejection',
            'size_matching':'Existing whole-component size_match_rows with exact gap=0; unsuccessful search is unavailable, not proof no subset exists.',
            'multiplicity':'Future qualified study-level primary H1-H4 families, Holm; H5 separate validity endpoint. No tests run before power admission.'},
        'confirmation_power':state(reason='INDEPENDENT_SOURCE_COHORT_DESCRIPTOR_VARIATION_REFERENCE_OWNERSHIP_AND_OUTCOME_NOISE_NOT_YET_QUALIFIED',status='insufficient_information'),
        'pilot_admission':state(reason='EXACT_ORIGINAL_REFERENCE_IDENTITIES_TASK_SPLITS_AND_COST_NOT_YET_ADMITTED'),
        'test_target_accessed':False,'model_performance_used':False,'universal_shortcut_score':None}
    value['contract_id']=fingerprint(value);schema_check(value,'falsification-contract');path=ROOT/'falsification-contract.json'
    if path.exists():assert json.loads(path.read_text())==value
    atomic_json(path,value);print(json.dumps({'contract_id':value['contract_id'],'hypotheses':5,'admitted_confirmation_studies':0,'models_fitted':0}))


if __name__=='__main__':main()
