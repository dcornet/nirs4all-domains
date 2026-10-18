"""Versioned experiment-specific identity exposure and stability decisions.

Native Methods owns PCA/HDBSCAN/ARI and descriptive summaries. These rational
inclusion expressions and finite identity counts define this resampling design;
they are not a general probability-distribution implementation.
"""
from collections import Counter
from fractions import Fraction
from functools import lru_cache
from itertools import combinations
import math
import random
from .dependence import state
from .predictive import native_summary
from .storage import fingerprint
from .unsupervised import component_draw,compare_partition

PROTOCOL='domains.stability_power.v0.2'
QUALITY={'median_ari':.9,'ari_p10':.8,'noise_p10':.9,'max_reference_noise':.4,
    'min_pair_exposures':10,'min_pairs_per_cluster':10,'median_pair_support':.8,
    'min_success_fraction':.9,'min_planned_candidate_coverage':.95}


def population(ids,components):
    if len(ids)<2 or len(set(ids))!=len(ids) or set(ids)!=set(components):
        raise ValueError('COMPLETE_UNIQUE_COMPONENT_IDENTITIES_REQUIRED')
    if any(not isinstance(s,str) or not s or not isinstance(components[s],str) or not components[s] for s in ids):
        raise ValueError('EXPLICIT_COMPONENT_NAMESPACES_REQUIRED')
    return Counter(components[s] for s in ids)


def rational(value):
    return {'numerator':value.numerator,'denominator':value.denominator,'value':float(value)}


def expected_exposure(ids,components,fraction,draws):
    sizes=population(ids,components);g=len(sizes);n=len(ids)
    if not .5<=fraction<=.9 or not isinstance(draws,int) or draws<1:raise ValueError('INVALID_FIXED_DESIGN')
    m=math.ceil(fraction*g);same=sum(s*(s-1)//2 for s in sizes.values());total=n*(n-1)//2
    p_same=Fraction(m,g);p_other=Fraction(m*(m-1),g*(g-1)) if g>1 else Fraction(0)
    average=(same*p_same+(total-same)*p_other)/total
    return {'n_observations':n,'n_components':g,'selected_components':m,'draws':draws,
        'component_size_counts':dict(sorted(Counter(sizes.values()).items())),
        'same_component_pairs':same,'different_component_pairs':total-same,
        'same_component_expectation':state(rational(draws*p_same)) if same else state(reason='NO_SAME_COMPONENT_PAIRS'),
        'different_component_expectation':state(rational(draws*p_other)) if total>same else state(reason='NO_DIFFERENT_COMPONENT_PAIRS'),
        'mean_over_all_observation_pairs':rational(draws*average),
        'expected_selected_observations':rational(Fraction(m*n,g)),
        'scope':'Uniform fixed-size whole-component sampling. Expectations do not guarantee each pair or effective comparison.'}


def schedule(ids,components,fraction,draws,seed):
    population(ids,components)
    return [component_draw(ids,components,fraction,d,seed) for d in range(draws)]


def exposure_masks(ids,draws):
    allowed=set(ids);masks={s:0 for s in ids};row_eligible=[]
    for number,draw in enumerate(draws):
        chosen=draw['observation_ids']
        if len(set(chosen))!=len(chosen) or not set(chosen)<=allowed:raise ValueError('DRAW_IDENTITY_SCOPE_VIOLATION')
        for s in chosen:masks[s]|=1<<number
        row_eligible.append(len(chosen)>=20 and len(chosen)>=.5*len(ids))
    return masks,row_eligible


def _pool(left,right,seed,limit=4096):
    return _cached_pool(tuple(sorted(left)),tuple(sorted(right)) if right is not None else None,seed,limit)


@lru_cache(maxsize=128)
def _cached_pool(left,right,seed,limit):
    total=len(left)*len(right) if right is not None else len(left)*(len(left)-1)//2
    if total<=limit:
        return tuple((a,b) for a in left for b in right) if right is not None else tuple(combinations(left,2))
    rng=random.Random(seed);result=set()
    for _ in range(20*limit):
        pair=(rng.choice(left),rng.choice(right)) if right is not None else tuple(sorted(rng.sample(left,2)))
        result.add(pair)
        if len(result)==limit:break
    return tuple(sorted(result))


@lru_cache(maxsize=65536)
def _pair_key(seed,a,b):
    return fingerprint([seed,a,b])


def balanced_panel(ids,labels,draws,seed=13043,cap=4096):
    if len(ids)!=len(labels) or len(set(ids))!=len(ids):raise ValueError('REFERENCE_LABEL_IDENTITY_MISMATCH')
    clusters={label:sorted(s for s,v in zip(ids,labels,strict=True) if v==label) for label in set(labels) if label>=0}
    ordered=sorted(clusters,key=lambda label:clusters[label]);masks,row_eligible=exposure_masks(ids,draws)
    pair_groups=list(combinations(ordered,2));pair_groups=sorted(pair_groups,key=lambda p:fingerprint([seed,clusters[p[0]],clusters[p[1]]]))[:64]
    desired=sum(min(32,len(v)*(len(v)-1)//2) for v in clusters.values())+sum(min(8,len(clusters[a])*len(clusters[b])) for a,b in pair_groups)
    if desired>cap:
        return {'status':'insufficient_information','reason':'PANEL_CAP_CANNOT_COVER_ALL_REFERENCE_CLUSTERS',
            'value':None,'required_slots':desired,'cap':cap}
    within=[];between=[];coverage=[]
    for label in ordered:
        members=clusters[label];pool=_pool(members,None,fingerprint([seed,members]));minimum=QUALITY['min_pair_exposures']
        exposed=[p for p in pool if (masks[p[0]]&masks[p[1]]).bit_count()>=minimum]
        chosen=sorted(exposed,key=lambda p:_pair_key(seed,*p))[:32]
        coverage.append({'reference_label':label,'n_reference_observations':len(members),
            'n_possible_pairs':len(members)*(len(members)-1)//2,'candidate_pairs':len(pool),
            'candidate_sampling':'census' if len(pool)==len(members)*(len(members)-1)//2 else 'bounded uniform pair proposals',
            'adequately_exposed_candidates':len(exposed),'candidate_coverage':len(exposed)/len(pool) if pool else None,
            'selected_pairs':len(chosen),'feasible':len(chosen)>=10 and bool(pool) and len(exposed)>=.95*len(pool)})
        within.extend({'ids':list(p),'reference_label':label,'planned_exposures':(masks[p[0]]&masks[p[1]]).bit_count()} for p in chosen)
    for a,b in pair_groups:
        pool=_pool(clusters[a],clusters[b],fingerprint([seed,clusters[a],clusters[b]]),limit=512)
        exposed=[p for p in pool if (masks[p[0]]&masks[p[1]]).bit_count()>=QUALITY['min_pair_exposures']]
        chosen=sorted(exposed,key=lambda p:_pair_key(seed,*p))[:8]
        between.extend({'ids':list(p),'reference_labels':[a,b],'planned_exposures':(masks[p[0]]&masks[p[1]]).bit_count()} for p in chosen)
    feasible=len(ordered)>=2 and bool(draws) and sum(row_eligible)>=.9*len(draws) and all(c['feasible'] for c in coverage)
    return {'status':'computed','reason':None,'value':{'within':within,'between':between,'coverage':coverage,
        'planned_feasible':feasible,'planned_draws':len(draws),'row_eligible_draws':sum(row_eligible),
        'between_cluster_pairs_selected':len(pair_groups),'between_cluster_pairs_total':len(clusters)*(len(clusters)-1)//2,
        'seed':seed,'cap':cap,'selection_scope':'Reference labels and planned identity exposures only; no resampled labels or Y.',
        'inference_scope':'Conditional balanced adequately exposed pair panel; not an unbiased all-pair census.'}}


def project_draw(ids,reference,draw,profile,panels,number):
    selected=draw['observation_ids'];settings=[]
    for i,(ref,native,panel) in enumerate(zip(reference['cluster_settings'],profile['cluster_settings'],panels,strict=True)):
        if ref['status']!='computed' or native['status']!='computed':
            settings.append(state(reason='REFERENCE_OR_DRAW_PARTITION_UNAVAILABLE'));continue
        labels=native['value']['labels']
        if len(labels)!=len(selected):raise ValueError('NATIVE_DRAW_IDENTITY_MISMATCH')
        comparison=compare_partition(ids,ref['value']['labels'],selected,labels)
        mapping=dict(zip(selected,labels,strict=True));exposed=0;same=0
        pairs=panel['value']['within']+panel['value']['between'] if panel['status']=='computed' else []
        for index,pair in enumerate(pairs):
            a,b=pair['ids']
            if a in mapping and b in mapping:
                exposed|=1<<index
                if mapping[a]>=0 and mapping[a]==mapping[b]:same|=1<<index
        settings.append(state({'comparison':comparison,'exposure_bits':format(exposed,'x'),'same_cluster_bits':format(same,'x'),
            'noise_fraction':native['value']['noise_fraction'],'n_clusters':native['value']['n_clusters'],
            'membership_summary':native['value']['membership_summary']}))
    return {'draw':number,'status':'computed','reason':None,'selected_ids_sha256':fingerprint(selected),
        'n_selected_observations':len(selected),'n_selected_components':len(draw['selected_units']),
        'settings':settings,'pca_fits':1,'hdbscan_attempts':2}


def _p10(values):
    return sorted(values)[max(0,math.ceil(.1*len(values))-1)] if values else None


def decision_summary(reference,records,ids,n_units,panels,scope):
    result=[]
    for index,(ref,panel) in enumerate(zip(reference['cluster_settings'],panels,strict=True)):
        if ref['status']!='computed':result.append(state(reason='REFERENCE_PARTITION_UNAVAILABLE'));continue
        pairs=panel['value']['within']+panel['value']['between'] if panel['status']=='computed' else []
        counts=[[0,0] for _ in pairs];valid=[];aris=[];noises=[]
        for record in records:
            if record['status']!='computed' or record['settings'][index]['status']!='computed':continue
            value=record['settings'][index]['value'];valid.append(value)
            ari=value['comparison']['ari_including_noise']
            if ari['status']=='computed':aris.append(ari['value'])
            noises.append(value['comparison']['noise_status_agreement'])
            exposed=int(value['exposure_bits'],16);same=int(value['same_cluster_bits'],16)
            if exposed<0 or same<0 or exposed>>len(pairs) or same>>len(pairs):raise ValueError('PAIR_BITS_OUTSIDE_FROZEN_PANEL')
            if same&~exposed:raise ValueError('COASSIGNMENT_WITHOUT_PAIR_EXPOSURE')
            for i,c in enumerate(counts):c[0]+=(exposed>>i)&1;c[1]+=(same>>i)&1
        pair_records=[{**p,'exposures':c[0],'same_nonnoise_cluster':c[1],
            'support':c[1]/c[0] if c[0] else None,'support_reason':None if c[0] else 'NO_EFFECTIVE_PAIR_EXPOSURES'} for p,c in zip(pairs,counts,strict=True)]
        clusters=[]
        for label in sorted({v for v in ref['value']['labels'] if v>=0}):
            v=[p['support'] for p in pair_records[:len(panel['value']['within'])] if p['reference_label']==label and p['exposures']>=10] if panel['status']=='computed' else []
            clusters.append({'reference_label':label,'n_pairs_exposed_at_least_10':len(v),
                'support_summary':state(native_summary(v)) if v else state(reason='NO_ADEQUATELY_EXPOSED_PAIRS')})
        attempted=len(records);execution=len(ids)>=30 and n_units>=20 and attempted>=20 and len(valid)>=.9*attempted
        eligible=bool(attempted) and len(aris)>=.9*attempted
        pair_support=bool(clusters) and all(c['n_pairs_exposed_at_least_10']>=10 for c in clusters)
        planned=panel['status']=='computed' and panel['value']['planned_feasible']
        quality=bool(eligible and native_summary(aris)['median']>=.9 and _p10(aris)>=.8 and noises and _p10(noises)>=.9
            and ref['value']['noise_fraction']<=.4 and ref['value']['n_clusters']>=2 and pair_support
            and all(c['support_summary']['value']['median']>=.8 for c in clusters))
        supported=execution and eligible and pair_support and planned
        classification='robust_structure' if supported and quality else 'fragile_structure' if supported else 'insufficient_information'
        result.append(state({'min_cluster_size':ref['value']['min_cluster_size'],'attempted_draws':attempted,'successful_draws':len(valid),
            'eligible_ari_draws':len(aris),'ari_summary':state(native_summary(aris)) if aris else state(reason='NO_ELIGIBLE_SHARED_PARTITIONS'),
            'ari_p10':_p10(aris),'noise_agreement_summary':state(native_summary(noises)) if noises else state(reason='NO_SUCCESSFUL_DRAWS'),
            'noise_agreement_p10':_p10(noises),'classification':classification,'cluster_pair_support':clusters,
            'pair_panel':{'within':pair_records[:len(panel['value']['within'])],'between':pair_records[len(panel['value']['within']):]} if panel['status']=='computed' else panel,
            'planned_panel':panel,'gates':{'execution_support':execution,'eligible_ari_support':eligible,'pair_support':pair_support,
                'planned_feasibility':planned,'quality':quality},'reference_cluster_counts':dict(sorted(Counter(v for v in ref['value']['labels'] if v>=0).items())),
            'scope':scope,'biological_sampling_uncertainty':False,
            'continuum_classification':state(reason='SEPARATE_CONTINUUM_PROTOCOL_NOT_QUALIFIED')}))
    return {'protocol_version':PROTOCOL,'settings':result,'n_reference_observations':len(ids),'n_declared_resampling_units':n_units,
        'unit_scope':scope,'quality_thresholds':QUALITY,'biologically_independent_unit_count':state(reason='NOT_ESTIMATED_BY_ALGORITHMIC_RESAMPLING')}
