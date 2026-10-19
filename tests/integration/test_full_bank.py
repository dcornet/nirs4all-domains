"""Scientific failure modes of the bounded owner-export adapter."""
import tempfile
from pathlib import Path
import unittest
import copy
from nirs4all_domains.full_bank import aligned_order,matrix_request,target_values,scores,reference_task,metadata_scope


class FullBankTests(unittest.TestCase):
    def test_counts_without_export_attestation_refused(self):
        with self.assertRaisesRegex(ValueError,'ATTESTATION'):
            aligned_order(['a','b'],None,None,owner_attested=False,same_export=True,n_y=2)

    def test_unkeyed_target_cannot_repair_conflicting_order(self):
        with self.assertRaisesRegex(ValueError,'CONFLICTING'):
            aligned_order(['a','b'],['b','a'],None,owner_attested=True,same_export=True,n_y=2)
        self.assertEqual(aligned_order(['a','b'],['b','a'],['b','a'],owner_attested=False,same_export=False,n_y=2),([1,0],'explicit_keys'))

    def test_unsorted_axis_preserves_columns_and_values(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'X.csv';path.write_text('observation_id;900;700;800\na;9;7;8\nb;6;4;5\n')
            request,axis=matrix_request({'matrix':str(path),'separator':';','source_id':'X','view_id':'synthetic/X','axis_unit':'nm'})
            self.assertEqual(request['spectra'],[[9,7,8],[6,4,5]])
            self.assertEqual(axis['original_labels'],['900','700','800'])
            self.assertEqual(request['axis'],[0,1,2]);self.assertEqual(request['axis_unit'],'feature_index')

    def test_retained_sentinel_filtered_before_float(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'Y.csv';path.write_text('target\n1\nNEVER_DECODE_RETAINED\n3\n')
            y,missing=target_values({'target_path':str(path),'target_separator':','},'target',{'development_indices':[0,2],'Y_order':[0,1,2]})
            self.assertEqual(y,{0:1.,2:3.});self.assertEqual(missing,0)

    def test_native_fixed_models_signal_and_mean(self):
        n=30;x=[[float(i),float(i%4)] for i in range(n)];y={i:2.*i+3 for i in range(n)}
        scope={'observation_ids':[str(i) for i in range(n)],'groups':[str(i//2) for i in range(n)],
               'group_columns':['synthetic_pairs'],'development_indices':list(range(n)),'n_retained':0,'n_purged_retained_component':0}
        a=reference_task(x,y,scope,{'task_id':'synthetic-signal'})
        self.assertEqual(a['model_fit_successes'],6)
        for family in ['pls','ridge']:
            self.assertGreater(a['families'][family]['pooled']['value']['skill']['value'],.95)
        b=scores([1.,3.],[2.,2.],[2.,2.]);self.assertAlmostEqual(b['skill']['value'],0.,delta=1e-10)
        singleton=scores([1.],[1.],[2.])
        self.assertEqual(singleton['rmse']['value'],0.)
        self.assertEqual(singleton['r2']['status'],'unavailable')
        from nirs4all_domains.predictive import group_folds
        rows=[{'physical_sample_id':str(i),'independence_group':str(i//2)} for i in range(n)]
        folds=group_folds(rows,2,18,'explicit-two-folds')
        alternate=reference_task(x,y,scope,{'task_id':'synthetic-signal'},folds=folds)
        self.assertEqual(alternate['model_fit_successes'],4)
        bad=copy.deepcopy(folds);a=bad['folds'][0]['train_sample_ids'][0];b=bad['folds'][0]['validation_sample_ids'][0]
        for fold in bad['folds']:
            for key in ['train_sample_ids','validation_sample_ids']:
                fold[key]=[b if v==a else a if v==b else v for v in fold[key]]
        from dag_ml import DagMlValidationError
        with self.assertRaisesRegex((ValueError,DagMlValidationError),'leaks group|Dependency component'):
            reference_task(x,y,scope,{'task_id':'synthetic-signal'},folds=bad)

    def test_transitive_declared_identity_purges_retained_component(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'X.csv').write_text('observation_id;900\na;1\nb;2\nc;3\nd;4\n')
            (root/'M.csv').write_text('observation_id;sample_id;joint_id;split_original\na;s1;j1;train\nb;s1;j2;train\nc;s2;j2;test\nd;s3;j3;train\n')
            (root/'Y.csv').write_text('target\nPURGED_A\nPURGED_B\nRETAINED_SENTINEL\n4\n')
            entry={'metadata_headers':['observation_id','sample_id','joint_id','split_original'],
                   'metadata_path':str(root/'M.csv'),'metadata_separator':';',
                   'target_headers':['target'],'target_path':str(root/'Y.csv'),'target_separator':';','target_rows':4}
            source={'view_id':'synthetic/X','matrix':str(root/'X.csv'),'separator':';','headers':['observation_id','900'],'n_observations':4}
            entry.update(dataset_id='synthetic',content_version='1')
            source.update(dataset_id='synthetic',content_version='1',source_id='X')
            from nirs4all_domains.storage import digest
            receipt={'export_id':'synthetic-export-1','owner_attested':True,'order_preserved':True,
                     'dataset_id':'synthetic','content_version':'1','source_id':'X',
                     'sha256':{k:digest(root/(k+'.csv')) for k in ['X','Y','M']}}
            with self.assertRaisesRegex(ValueError,'ATTESTATION'):
                metadata_scope(entry,source)
            bad=copy.deepcopy(receipt);bad['sha256']['Y']='0'*64
            with self.assertRaisesRegex(ValueError,'BINDING_MISMATCH'):
                metadata_scope(entry,source,export_contract=bad)
            scope=metadata_scope(entry,source,export_contract=receipt)
            self.assertEqual(scope['development_indices'],[3])
            self.assertEqual(scope['n_purged_retained_component'],2)
            self.assertEqual(target_values(entry,'target',scope),({3:4.},0))
            text=(root/'M.csv').read_text().replace(';train',';historical_splits_documented_not_applied').replace(';test',';historical_splits_documented_not_applied')
            (root/'M.csv').write_text(text);receipt['sha256']['M']=digest(root/'M.csv')
            no_native=metadata_scope(entry,source,export_contract=receipt)
            self.assertEqual(no_native['n_retained'],0)
            self.assertEqual(no_native['development_indices'],[0,1,2,3])
            (root/'Y.csv').write_text('observation_id;target\na;1\nb;2\nc;3\nd;4\n')
            entry['target_headers']=['observation_id','target']
            (root/'M.csv').write_text('sample_id\ns1\ns1\ns2\ns3\n')
            entry['metadata_headers']=['sample_id']
            with self.assertRaisesRegex(ValueError,'ATTESTATION'):
                metadata_scope(entry,source)
            receipt['sha256']={k:digest(root/(k+'.csv')) for k in ['X','Y','M']}
            self.assertEqual(metadata_scope(entry,source,export_contract=receipt)['development_indices'],[0,1,2,3])

if __name__=='__main__':unittest.main()
