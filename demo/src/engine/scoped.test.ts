import {describe,it,expect} from 'vitest';
import {scopedRequest} from './scoped';
import type {LocalDataset} from './types';

function data():LocalDataset{
  const roles=['train','test','train','predict','train','test'] as const;
  return {input:{schema_version:1,dataset_id:'synthetic-scoped',source_id:'X',content_sha256:'a'.repeat(64),
    observation_ids:roles.map((_,i)=>`row-${i}`),spectra:[],axis:[2000,1000],axis_unit:'nm'},
    rawX:[[10,1],[90,9],[20,2],[999,999],[30,3],[80,8]],
    rowManifest:roles.map((partition,i)=>({key:`row-${i}`,observation_id:`source-${i}`,partition,original_partition:partition,source_id:'X'})),
    metadata:[{name:'batch',role:'group',type:'numeric',origin:'declared',evidence:'declared',derived_from_target:'unknown',values:[1,9,2,999,3,8]},
      {name:'instrument',role:'instrument',type:'categorical',values:['A','B','A','P','A','B']},
      {name:'derived',role:'factor',derived_from_target:true,values:['Y','Y','Y','Y','Y','Y']}],
    targets:[{name:'hidden_target',type:'numeric',unit:'g',origin:'test-fixture',values:[11,123456789,22,654321,33,987654321],mask:[true,true,true,true,true,true]}],
    partitions:[],headers:['2000','1000'],warnings:[],importSpec:{},identityOrigin:'declared',license:'synthetic',mode:'user_computed_live'};
}
describe('F4 least-access worker payloads',()=>{
  it('does not read any target, or test/prediction M/X values, for train structure',()=>{
    const d=data();
    Object.defineProperty(d,'targets',{get(){throw new Error('TARGET_VALUE_READ');}});
    for(const i of [1,3,5]){
      Object.defineProperty(d.rawX!,i,{get(){throw new Error('NONTRAIN_X_READ');}});
      Object.defineProperty(d.metadata[0].values,i,{get(){throw new Error('NONTRAIN_M_READ');}});
    }
    const r=scopedRequest(d,'train_structure');
    expect(r.x?.matrix).toEqual([[10,1],[20,2],[30,3]]);
    expect(r.reference_keys).toEqual(['row-0','row-2','row-4']);expect(r.query_keys).toEqual([]);
    expect(r.metadata).toHaveLength(1);expect(r.metadata[0].values).toEqual([1,2,3]);
    expect(r.metadata[0].kind).toBe('categorical');expect(r.metadata[0].derived_from_target).toBeNull();
    expect(r.access.y_fields).toEqual([]);expect(r.fit).toBe('train');
  });
  it('identity audit sends identity M only, without reading X or Y',()=>{
    const d=data();Object.defineProperty(d,'rawX',{get(){throw new Error('X_READ');}});
    // Presence of the imported matrix is a declaration; projection must not inspect any cell.
    Object.defineProperty(d,'rawX',{value:new Proxy([],{get(_target,property){if(property==='length')return 6;throw new Error('X_CELL_READ');}})});
    Object.defineProperty(d,'targets',{get(){throw new Error('Y_READ');}});
    const r=scopedRequest(d,'integrity_audit',{diagnostic:'declared_identities'});
    expect(r.x).toBeNull();expect(r.access.x).toBe(false);expect(r.metadata.map(m=>m.name)).toEqual(['batch','instrument']);
  });
  it('metadata-only operations exclude X, Y and declared target-derived M',()=>{
    const d=data();const r=scopedRequest(d,'cross_partition_metadata_audit');
    expect(r.x).toBeNull();expect(r.access.y_fields).toEqual([]);
    expect(r.metadata.map(m=>m.name)).toEqual(['batch','instrument']);
    expect(r.metadata[0].values).toEqual([1,2,3,9,8]);
  });
  it('support preserves distinct complete train/test populations and excludes prediction',()=>{
    const r=scopedRequest(data(),'train_reference_test_query');
    expect(r.reference_keys).toEqual(['row-0','row-2','row-4']);expect(r.query_keys).toEqual(['row-1','row-5']);
    expect(r.x?.matrix).toEqual([[10,1],[20,2],[30,3],[90,9],[80,8]]);expect(r.fit).toBe('none');
    expect(JSON.stringify(r)).not.toContain('123456789');expect(JSON.stringify(r)).not.toContain('987654321');
  });
  it('never grants global consent implicitly and preserves missing cells for a local Rust refusal',()=>{
    const d=data();d.rawX![0][0]=null;
    expect(scopedRequest(d,'global_descriptive_transductive').explicit_transductive).toBe(false);
    const r=scopedRequest(d,'global_descriptive_transductive',{explicit_transductive:true});
    expect(r.explicit_transductive).toBe(true);expect(r.x?.matrix[0][0]).toBeNull();expect(r.fit).toBe('transductive');
  });
});
