import {describe,it,expect} from 'vitest';
import {factorRequest,factorSource,type FactorSource} from './factor';
import type {LocalDataset,BrowserReport} from './types';
import type {FactorAssociationRun} from '../FactorAssociationControls';
const run:FactorAssociationRun={factorId:'temperature',population:'train',correlationMethod:'spearman',inference:'descriptive',explicitTransductive:false};
const source:FactorSource={receipt:null,report:{schema_version:1,protocol_version:'domains.browser_x.v1',status:'computed',scope:{},metrics:{},input_sha256:'input',evidence_sha256:'evidence',test_target_accessed:false,raw_spectra_included:false} as BrowserReport};
function data():LocalDataset{
  return {input:{schema_version:1,dataset_id:'synthetic',source_id:'X',content_sha256:'a'.repeat(64),observation_ids:['a','t','b','p','c'],spectra:[],axis:[1000],axis_unit:'nm'},
    rowManifest:['train','test','train','predict','train'].map((partition,i)=>({key:['a','t','b','p','c'][i],partition,observation_id:null,original_partition:partition,source_id:'X'})) as LocalDataset['rowManifest'],
    metadata:[{name:'temperature',role:'factor',type:'numeric',unit:'°C',origin:'synthetic-design',evidence:'declared',derived_from_target:false,values:[0,999,20,888,null]},
      {name:'specimen',role:'specimen',type:'categorical',values:['s1','TEST','s2','PREDICT','s2']},
      {name:'target_derived',role:'factor',derived_from_target:true,values:['Y','Y','Y','Y','Y']}],
    partitions:[],headers:[],warnings:[],identityOrigin:'declared',importSpec:{content_version:'fixture'},license:'synthetic',mode:'user_computed_live'};
}
describe('F4.1 least-access factor projection',()=>{
  it('never reads X or Y, or nontrain M, and preserves missing versus zero and source evidence',()=>{
    const d=data();for(const key of ['rawX','targets'])Object.defineProperty(d,key,{get(){throw new Error(`${key}_READ`);}});
    Object.defineProperty(d.input,'spectra',{get(){throw new Error('X_READ');}});
    for(const f of d.metadata)for(const i of [1,3])Object.defineProperty(f.values,i,{get(){throw new Error('NONTRAIN_M_READ');}});
    const request=factorRequest(d,source,run);
    expect(request.factors[0].values).toEqual([0,20,null]);expect(request.factors[0].unit).toBe('°C');
    expect(request.pca.row_keys).toEqual(['a','b','c']);expect(request.access).toEqual({x:false,y_fields:[],m_fields:['temperature','specimen']});
    expect(request.dependencies[0].values).toEqual(['s1','s2','s2']);expect(request.correlation_method).toBe('spearman');expect(request.inference.plan).toBeNull();
    expect(request.pca.report).toEqual(source.report);expect(source.report.metrics).toEqual({});
  });
  it('does not recycle global PCA as train and requires explicit separate global consent',()=>{
    const global={operation:'global_descriptive_transductive',status:'computed',value:{structure:source.report},receipt:{}} as Parameters<typeof factorSource>[1][number];
    expect(factorSource('train',[global],null)).toBeUndefined();expect(factorSource('global_transductive',[global],null)?.report).toBe(source.report);
    expect(()=>factorRequest(data(),source,{...run,population:'global_transductive'})).toThrow('CONSENT');
    const r=factorRequest(data(),source,{...run,population:'global_transductive',explicitTransductive:true});
    expect(r.pca.row_keys).toEqual(['a','b','c','t']);expect(r.factors[0].values).toEqual([0,20,null,999]);
    expect(()=>factorRequest(data(),source,{...run,population:'unpartitioned'})).toThrow('CANNOT_HIDE');
  });
  it('rejects known Y-derived or ambiguous/mismatched factor mappings',()=>{
    expect(()=>factorRequest(data(),source,{...run,factorId:'target_derived'})).toThrow('INELIGIBLE');
    const d=data();d.rowManifest![1].key='a';expect(()=>factorRequest(d,source,run)).toThrow('AMBIGUOUS');
    const mismatch=data();mismatch.metadata[0].values.pop();expect(()=>factorRequest(mismatch,source,run)).toThrow('MAPPING');
  });
});
