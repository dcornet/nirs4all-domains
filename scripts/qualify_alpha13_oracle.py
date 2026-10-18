"""Operational decision error rates, separate from natural-X cluster taxonomies."""
import json
import random
from alpha13_common import ROOT,PUBLIC,run,publish
from run_alpha13_calibration import oracle
from nirs4all_domains.stability_power import balanced_panel,decision_summary,project_draw,schedule
from nirs4all_domains.storage import atomic_json,digest,fingerprint


def main():
    frozen=json.loads((PUBLIC/'calibration-freeze.json').read_text());b=frozen['draw_count']
    contract={'task':{'task_id':fingerprint(['alpha13','oracle-decisions'])},'phase':'oracle-decision-calibration',
        'freeze_id':frozen['freeze_id'],'runner_sha256':digest(__file__),
        'power_bridge_sha256':digest('bridges/python/nirs4all_domains/stability_power.py')}
    def calculate(folder):
        ids=[f'oracle:{i:03}' for i in range(120)];labels=[i//40 for i in range(120)];units={s:s for s in ids};reference=oracle(ids,labels);rows=[]
        for count in [20,b]:
            for seed in frozen['perturbation_seeds']:
                for fraction in frozen['fractions']:
                    draws=schedule(ids,units,fraction,count,seed);panels=[balanced_panel(ids,labels,draws)]*2
                    for truth in ['stable','unstable','missing']:
                        records=[]
                        for number,draw in enumerate(draws):
                            if truth=='missing' and number%2:
                                records.append({'draw':number,'status':'failed','reason':'CONTROLLED_MISSING_COMPARISON'});continue
                            selected=[labels[ids.index(s)] for s in draw['observation_ids']]
                            if truth=='unstable':random.Random(seed+number).shuffle(selected)
                            records.append(project_draw(ids,reference,draw,oracle(draw['observation_ids'],selected),panels,number))
                        summary=decision_summary(reference,records,ids,120,panels,'Oracle known partition truth; no biological inference.')
                        classes=[s['value']['classification'] for s in summary['settings']]
                        rows.append({'draws':count,'seed':seed,'fraction':fraction,'truth':truth,'classifications':classes,
                            'false_robust':classes.count('robust_structure') if truth=='unstable' else None,
                            'false_fragile':classes.count('fragile_structure') if truth=='stable' else None,
                            'inconclusive':classes.count('insufficient_information')})
        result={'protocol_version':'domains.stability_power.v0.1','freeze_id':frozen['freeze_id'],'rows':rows,
            'new_pca_fits':0,'new_hdbscan_fits':0,'target_accessed':False,
            'scope':'Operational error rates conditional on three identity-perturbation designs, two fractions and two settings; not independent generated populations or real-bank prevalence.'}
        for count in [20,b]:
            r=[v for v in rows if v['draws']==count]
            result['B'+str(count)]={'stable_decisions':sum(len(v['classifications']) for v in r if v['truth']=='stable'),
                'unstable_decisions':sum(len(v['classifications']) for v in r if v['truth']=='unstable'),
                'false_robust':sum(v['false_robust'] or 0 for v in r),'false_fragile':sum(v['false_fragile'] or 0 for v in r),
                'stable_inconclusive':sum(v['inconclusive'] for v in r if v['truth']=='stable'),
                'missing_inconclusive':sum(v['inconclusive'] for v in r if v['truth']=='missing')}
        return result
    plan={'inputs':[],'scratch_bytes':4096,'evidence_bytes':16384,'expected_fits':0,'expected_permutations':0,
        'uncertainty':'Native ARI over known oracle labels; no spectra, PCA, HDBSCAN or model fit.'}
    store,receipt,value=run(contract,'P2',plan,calculate);publish(store,receipt,'oracle-calibration.json');atomic_json(ROOT/'oracle-receipt.json',receipt)
    print(json.dumps({k:v for k,v in value.items() if k.startswith('B')}))


if __name__=='__main__':main()
