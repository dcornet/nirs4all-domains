"""Fixed semantic priority for deeper cases, independent of predictive scores."""
PRIORITY = ('active_w_w','moisture','protein','nmass','n_pc_dry','nmass_percent',
    'nmass_perc','n_mass_mg_g','n_mass_g_g','n','n___dm','pct_nitrogen',
    'n_g_m2','n_area','chlorophyll','chl_g_m2','lma','lma_g_m2','lma_g_m2',
    'lma_value_g/m2','som','c_pc_dry','cmass','c','sla','plant_age')


def eligible_tasks(f,view,semantics):
    tasks=[t for t in f['tasks'] if t['view_id']==view and t['metadata_eligible'] and not semantics[t['task_id']]['excluded'] and semantics[t['task_id']]['target_evidence']=='catalog_quantitative_outcome_assay_independence_unverified']
    return sorted(tasks,key=lambda t:(PRIORITY.index(t['target'].lower()) if t['target'].lower() in PRIORITY else len(PRIORITY),t['target']))
