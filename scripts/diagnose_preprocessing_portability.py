#!/usr/bin/env python3
"""Diagnose published F4.3 numerical differences; this is NEVER a parity-pass gate.

No provider/kernel is called. Source and backend-own evidence bindings are
validated before test-only Gram/error calculations. Any numeric disagreement
keeps qualification failed; unexamined/hash-only differences are not waived.
"""
import argparse
import collections
import copy
import hashlib
import json
import check_preprocessing_parity as p
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('wasm','native','out'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    wasm,native_artifact=p.read(args.wasm),p.read(args.native)
    p.require(wasm['protocol_version']=='domains.browser_preprocessing_sensitivity_wasm.v1' and native_artifact['protocol_version']=='domains.browser_preprocessing_sensitivity_native.v1','ARTIFACT_PROTOCOL_MISMATCH')
    p.require(wasm['provider']['version']==native_artifact['provider_version']==p.VERSION,'PINNED_PROVIDER_REQUIRED')
    p.require(native_artifact['wasm_artifact_sha256']==hashlib.sha256(args.wasm.read_bytes()).hexdigest(),'EXACT_WASM_ARTIFACT_BINDING_REQUIRED')
    p.require(wasm['fixture_sha256']==native_artifact['fixture_sha256'] and wasm['descriptor_bank_sha256']==native_artifact['descriptor_bank_sha256'],'FIXTURE_OR_BANK_CHANGED')
    p.require(wasm['new_real_scientific_fits']==native_artifact['new_real_scientific_fits']==0,'REAL_FITS_FORBIDDEN')
    wc,native=p.indexed(wasm['cases']),p.indexed(native_artifact['cases'])
    p.require(list(wc)==list(native),'CASE_ORDER_OR_IDS_CHANGED')
    wp,np={},{}
    for cid,case in wc.items():
        other=native[cid]
        p.require(p.same(case['request'],other['original_wasm_request']),'ORIGINAL_WASM_REQUEST_CHANGED')
        p.require(p.same({k:v for k,v in case['request'].items() if k!='frozen_reference'},{k:v for k,v in other['request'].items() if k!='frozen_reference'}),'ORIGINAL_INPUT_PLAN_OR_METADATA_CHANGED')
        p.require(case.get('reference_case_id')==other.get('reference_case_id'),'REFERENCE_ANCESTOR_CHANGED')
        for item,previous,label in ((case,wp,'wasm'),(other,np,'native')):
            text=item.get('result_json')
            p.require(isinstance(text,str) and item.get('result_json_sha256')==hashlib.sha256(text.encode()).hexdigest(),'RAW_RUST_JSON_LINK_REQUIRED')
            p.require(p.same(json.loads(text),item['result']),'RAW_RUST_JSON_SEMANTIC_MISMATCH')
            p.verify_result(item,previous,cid+'/'+label)
        wp[cid],np[cid]=case,other
    failures=[];counts=collections.Counter();coordinate_diagnostics=[]

    def failure(context,category,path,left,right):
        item={**context,'category':category,'path':path,'wasm':left,'native':right}
        if isinstance(left,(int,float)) and not isinstance(left,bool) and isinstance(right,(int,float)) and not isinstance(right,bool):
            item['absolute_error']=abs(left-right)
            item['relative_error']=abs(left-right)/max(abs(left),abs(right)) if left or right else 0.0
        failures.append(item)

    def compare(a,b,path,context,category):
        counts[category]+=1
        if isinstance(a,bool) or isinstance(b,bool):
            if type(a) is not type(b) or a!=b:failure(context,category,path,a,b)
        elif isinstance(a,(int,float)) and isinstance(b,(int,float)):
            valid=a==b if isinstance(a,int) and isinstance(b,int) else p.close(a,b)
            if not valid:failure(context,category,path,a,b)
        elif isinstance(a,dict) and isinstance(b,dict):
            if a.keys()!=b.keys():failure(context,category,path+'/fields',sorted(a),sorted(b));return
            for key in a:compare(a[key],b[key],path+'/'+key,context,category)
        elif isinstance(a,list) and isinstance(b,list):
            if len(a)!=len(b):failure(context,category,path+'/length',len(a),len(b));return
            for i,(x,y)in enumerate(zip(a,b)):compare(x,y,path+'/'+str(i),context,category)
        elif a!=b or type(a)is not type(b):failure(context,category,path,a,b)

    def statuses(a,b,path,context,category):
        compare(a['status'],b['status'],path+'/status',context,category)
        compare(a['reason'],b['reason'],path+'/reason',context,category)
        return a['status']==b['status']=='computed'

    def report(rep):
        return (rep['value']['structure'].get('value')or{}).get('report',{}).get('metrics',{})

    for case in wasm['cases']:
        cid=case['id'];other=native[cid];maps={}
        for a,b in zip(case['result']['representations'],other['result']['representations']):
            context={'case':cid,'representation':a['id']}
            compare(a['status'],b['status'],'representation/status',context,'status')
            compare(a['reason'],b['reason'],'representation/reason',context,'status')
            if a['status']!=b['status'] or a['status']!='computed':continue
            av,bv=a['value'],b['value'];am,bm=report(a),report(b);signs=[];eigen=[]
            if am and bm:
                if statuses(am['pca'],bm['pca'],'pca',context,'pca_status'):
                    aa,bb=am['pca']['value'],bm['pca']['value'];eigen=aa['eigenvalues']
                    for key in ['eigenvalues','full_moments','resolution','unresolved','n_components_requested','n_components_resolved']:
                        compare(aa[key],bb[key],'pca/'+key,context,'pca_values')
                    compare(p.gram(aa['scores']),p.gram(bb['scores']),'pca/score_gram',context,'pca_geometry')
                    for j in range(len(eigen)):
                        sign=1 if sum(x[j]*y[j]for x,y in zip(aa['scores'],bb['scores']))>=0 else -1
                        signs.append(sign)
                        error=max(abs(x[j]-sign*y[j])for x,y in zip(aa['scores'],bb['scores']))
                        if not all(p.close(x[j],sign*y[j])for x,y in zip(aa['scores'],bb['scores'])):
                            coordinate_diagnostics.append({**context,'component':j+1,'eigenvalue':eigen[j],'max_abs_score_error':error})
                if statuses(am['density'],bm['density'],'density',context,'density_status'):
                    try:maps[a['id']]=p.align_density(am['density'],bm['density'],case['request']['reference_keys'],cid+'/'+a['id'])
                    except AssertionError as e:failure(context,'density_partition','density/partition',str(e),'different');maps[a['id']]=None
                    aa,bb=am['density']['value'],copy.deepcopy(bm['density']['value'])
                    for key in ['n_clusters','noise_count','membership']:
                        compare(aa[key],bb[key],'density/'+key,context,'density_values')
                    mapping=maps[a['id']]
                    if mapping is not None:
                        bb['persistence']=[bb['persistence'][next(k for k,v in mapping.items()if v==i)]for i in range(len(mapping))]
                        compare(aa['persistence'],bb['persistence'],'density/persistence',context,'density_values')
                for metric in ['raw_neighbors','projected_neighbors']:
                    if statuses(am[metric],bm[metric],metric,context,'neighbor_status'):
                        compare(am[metric]['value'],bm[metric]['value'],metric,context,'neighbor_summary')
            for fi,(fa,fb)in enumerate(zip(av['factors'],bv['factors'])):
                if not statuses(fa,fb,'factor/'+str(fi),context,'factor_status'):continue
                for field_a,field_b in zip(fa['value']['factors'],fb['value']['factors']):
                    for j,(ca,cb)in enumerate(zip(field_a['components'],field_b['components'])):
                        factor_context={**context,'factor':field_a['factor_id'],'component':j+1,'eigenvalue':eigen[j]if j<len(eigen)else None,'eigenvalues_indistinguishable_at_tolerance':j<len(eigen)and any(k!=j and p.close(eigen[j],v)for k,v in enumerate(eigen))}
                        da,db=ca['descriptive'],cb['descriptive']
                        if not statuses(da,db,'factor/descriptive',factor_context,'factor_status'):continue
                        x,y=da['value'],copy.deepcopy(db['value'])
                        sign=signs[j]if j<len(signs)else 1
                        if x['measure']in('pearson_r','spearman_rho'):
                            y['estimate']*=sign;y['owner_output']['coefficient']*=sign
                        compare(x['estimate'],y['estimate'],'factor/estimate',factor_context,'factor_estimate')
                        compare(x['owner_output'],y['owner_output'],'factor/owner_output',factor_context,'factor_owner_output')
            ca,cb=av['comparisons']['neighbors'],bv['comparisons']['neighbors']
            if statuses(ca,cb,'neighbor_comparison',context,'neighbor_comparison_status'):
                compare(ca['value'],cb['value'],'neighbor_comparison/value',context,'neighbor_comparison')
            ca,cb=av['comparisons']['clusters'],bv['comparisons']['clusters']
            if statuses(ca,cb,'cluster_comparison',context,'cluster_comparison_status'):
                aa,bb=ca['value'],copy.deepcopy(cb['value'])
                for key in ['n_total','n_joint','raw_noise_count','representation_noise_count','both_noise_count','raw_noise_to_assigned_count','raw_assigned_to_noise_count']:
                    compare(aa[key],bb[key],'cluster_comparison/'+key,context,'cluster_counts')
                if statuses(aa['ari'],bb['ari'],'cluster_comparison/ari',context,'cluster_ari_status'):
                    compare(aa['ari']['value'],bb['ari']['value'],'cluster_comparison/ari/value',context,'cluster_ari')
                ja,jb=aa['cluster_jaccard'],bb['cluster_jaccard']
                if statuses(ja,jb,'cluster_comparison/jaccard',context,'cluster_jaccard_status'):
                    rm,cm=maps.get('raw'),maps.get(a['id'])
                    if rm is not None and cm is not None:
                        ri=[next(k for k,v in rm.items()if v==i)for i in range(len(rm))]
                        ci=[next(k for k,v in cm.items()if v==i)for i in range(len(cm))]
                        v=jb['value']
                        for key in ['jaccard','intersections']:v[key]=[[v[key][i][j]for j in ci]for i in ri]
                        v['sizes_a']=[v['sizes_a'][i]for i in ri];v['sizes_b']=[v['sizes_b'][j]for j in ci]
                        compare(ja['value'],v,'cluster_comparison/jaccard/value',context,'cluster_jaccard')
            if statuses(av['support'],bv['support'],'support',context,'support_status'):
                sa,sb=av['support']['value'],bv['support']['value']
                if statuses(sa['monitoring'],sb['monitoring'],'monitoring',context,'monitoring_status'):
                    compare(sa['monitoring']['value'],sb['monitoring']['value'],'monitoring/value',context,'monitoring_values')
                if statuses(sa['projection'],sb['projection'],'projection',context,'projection_status'):
                    aa,bb=sa['projection']['value'],sb['projection']['value']
                    compare(aa['components'],bb['components'],'projection/components',context,'projection_values')
                    compare(p.gram(aa['train_scores']+aa['test_scores']),p.gram(bb['train_scores']+bb['test_scores']),'projection/combined_score_gram',context,'projection_geometry')

    receipt={'status':'DIAGNOSTIC_ONLY_NOT_A_PARITY_GATE','scope':'Published numerical/statistical subtrees only; no derived hash exception or qualification waiver','cases':len(wasm['cases']),'tolerance':{'absolute':p.TOLERANCE,'relative':p.TOLERANCE},'comparisons':dict(counts),'failure_counts':dict(collections.Counter(item['category']for item in failures)),'failures':failures,'coordinate_diagnostics_not_primary_PCA_gate':coordinate_diagnostics,'new_real_scientific_fits':0}
    receipt['qualification']='NOT_QUALIFIED; diagnostic enumeration does not establish parity'
    receipt['bindings_verified']=len(wasm['cases'])
    receipt['inputs']={'wasm_sha256':hashlib.sha256(args.wasm.read_bytes()).hexdigest(),'native_sha256':hashlib.sha256(args.native.read_bytes()).hexdigest(),'provider':p.VERSION,'raw_rust_json_links_verified':True}
    with args.out.open('x',encoding='utf-8')as f:json.dump(receipt,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({'status':receipt['status'],'cases':receipt['cases'],'failure_counts':receipt['failure_counts'],'failures_total':len(failures),'affected_cases':len({x['case']for x in failures}),'coordinate_diagnostic_count':len(coordinate_diagnostics)}))
    return 1 if failures else 0


if __name__=='__main__':
    raise SystemExit(main())
