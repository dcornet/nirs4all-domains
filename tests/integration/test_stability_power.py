"""Prospective identity-design truth and native decision-layer comparisons."""
from fractions import Fraction
from itertools import combinations
import copy
import random
import unittest
from nirs4all_domains.dependence import state
from nirs4all_domains.stability_power import (balanced_panel,decision_summary,expected_exposure,
    exposure_masks,population,project_draw,schedule)


def oracle_reference(ids,labels):
    return {'cluster_settings':[state({'labels':labels,'n_clusters':len(set(labels)-{-1}),
        'noise_fraction':labels.count(-1)/len(labels),'min_cluster_size':size,
        'membership_summary':{'count':len(labels),'min':1.,'max':1.,'mean':1.,'sd':0.,'q25':1.,'median':1.,'q75':1.}}) for size in [8,12]]}


class StabilityPowerControls(unittest.TestCase):
    def fixture(self,n=120):
        ids=[f'o:{i:03}' for i in range(n)];return ids,{s:s for s in ids},[min(2,3*i//n) for i in range(n)]

    def decisions(self,b=80,mode='stable',labels=None):
        ids,units,default=self.fixture();labels=default if labels is None else labels
        reference=oracle_reference(ids,labels);draws=schedule(ids,units,.6,b,13031)
        panels=[balanced_panel(ids,labels,draws)]*2;records=[]
        for i,draw in enumerate(draws):
            if mode=='missing' and i%2:
                records.append({'draw':i,'status':'failed','reason':'CONTROLLED_MISSING_COMPARISON'});continue
            selected=[labels[ids.index(s)] for s in draw['observation_ids']]
            if mode=='unstable':random.Random(13037+i).shuffle(selected)
            records.append(project_draw(ids,reference,draw,oracle_reference(draw['observation_ids'],selected),panels,i))
        return decision_summary(reference,records,ids,len(units),panels,'Oracle observation-conditional design; no biological uncertainty.')

    def test_singleton_formula_exact(self):
        ids,u,_=self.fixture();r=expected_exposure(ids,u,.6,20)['different_component_expectation']['value']
        self.assertEqual(Fraction(r['numerator'],r['denominator']),20*Fraction(72*71,120*119))
        self.assertLess(r['value'],10.)

    def test_unequal_components_exact_enumeration(self):
        ids=list('abcdefghij');u={s:str(i//3) for i,s in enumerate(ids)}
        r=expected_exposure(ids,u,.6,20);groups=sorted(set(u.values()));m=r['selected_components']
        selections=list(combinations(groups,m));total=0
        for selected in selections:
            chosen=[s for s in ids if u[s] in selected];total+=len(chosen)*(len(chosen)-1)//2
        exact=20*Fraction(total,len(selections)*(len(ids)*(len(ids)-1)//2))
        self.assertEqual(exact,Fraction(r['mean_over_all_observation_pairs']['numerator'],r['mean_over_all_observation_pairs']['denominator']))
        self.assertEqual(r['same_component_expectation']['value']['value'],15.)
        self.assertEqual(r['different_component_expectation']['value']['value'],10.)

    def test_expectation_does_not_guarantee_every_pair(self):
        ids,u,labels=self.fixture();draws=schedule(ids,u,.6,20,13031);masks,_=exposure_masks(ids,draws)
        self.assertTrue(any((masks[a]&masks[b]).bit_count()<10 for a,b in combinations(ids,2)))
        self.assertFalse(balanced_panel(ids,labels,draws)['value']['planned_feasible'])

    def test_balanced_small_fragment_and_exposure_aware_allocation(self):
        ids,u,_=self.fixture();labels=[0]*112+[1]*8;draws=schedule(ids,u,.6,80,13031)
        panel=balanced_panel(ids,labels,draws)['value']
        self.assertTrue(panel['planned_feasible']);self.assertEqual(panel['coverage'][1]['n_possible_pairs'],28)
        self.assertGreaterEqual(panel['coverage'][1]['selected_pairs'],10)
        self.assertTrue(all(p['planned_exposures']>=10 for p in panel['within']+panel['between']))

    def test_whole_component_draws_preserve_repeated_acquisitions(self):
        ids,_,_=self.fixture();u={s:f'physical:{i//4}' for i,s in enumerate(ids)}
        for d in schedule(ids,u,.6,20,13031):
            chosen=set(d['observation_ids'])
            self.assertTrue(all(sum(s in chosen for s in ids if u[s]==g) in [0,4] for g in set(u.values())))

    def test_row_eligibility_differs_with_unequal_component_sizes(self):
        ids,_,_=self.fixture();u={s:'dominant' if i<91 else s for i,s in enumerate(ids)}
        _,eligible=exposure_masks(ids,schedule(ids,u,.6,80,13031))
        self.assertLess(sum(eligible),72)

    def test_perfect_partition_low_power_is_not_fragile(self):
        r=self.decisions(b=20)
        self.assertTrue(all(s['value']['ari_summary']['value']['min']==1. for s in r['settings']))
        self.assertTrue(all(s['value']['classification']=='insufficient_information' for s in r['settings']))

    def test_perfect_partition_supported_is_robust(self):
        self.assertTrue(all(s['value']['classification']=='robust_structure' for s in self.decisions()['settings']))

    def test_unstable_partition_with_power_is_fragile(self):
        self.assertTrue(all(s['value']['classification']=='fragile_structure' for s in self.decisions(mode='unstable')['settings']))

    def test_missing_comparisons_remain_inconclusive(self):
        self.assertTrue(all(s['value']['classification']=='insufficient_information' for s in self.decisions(mode='missing')['settings']))

    def test_all_noise_is_not_safe_or_robust(self):
        r=self.decisions(labels=[-1]*120)
        self.assertTrue(all(s['value']['classification']=='insufficient_information' for s in r['settings']))
        self.assertTrue(all(s['value']['continuum_classification']['status']=='unavailable' for s in r['settings']))

    def test_panel_cannot_silently_drop_clusters_to_meet_cap(self):
        ids,u,labels=self.fixture();p=balanced_panel(ids,labels,schedule(ids,u,.6,80,13031),cap=4)
        self.assertEqual(p['reason'],'PANEL_CAP_CANNOT_COVER_ALL_REFERENCE_CLUSTERS')

    def test_identity_order_and_label_renaming_do_not_choose_new_pairs(self):
        ids,u,labels=self.fixture();draws=schedule(ids,u,.6,80,13031)
        a=balanced_panel(ids,labels,draws)['value'];b=balanced_panel(ids[::-1],[v+20 for v in labels[::-1]],draws)['value']
        self.assertEqual([p['ids'] for p in a['within']],[p['ids'] for p in b['within']])

    def test_missing_component_map_is_rejected(self):
        ids,u,_=self.fixture();u.pop(ids[-1])
        with self.assertRaisesRegex(ValueError,'COMPLETE_UNIQUE'):population(ids,u)

    def test_foreign_draw_identity_is_rejected(self):
        ids,u,_=self.fixture();d=schedule(ids,u,.6,20,13031);d[0]['observation_ids'][0]='foreign'
        with self.assertRaisesRegex(ValueError,'DRAW_IDENTITY'):exposure_masks(ids,d)


if __name__=='__main__':unittest.main()
