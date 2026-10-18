"""Actual synthetic CSV/native execution through the shared budget scheduler."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nirs4all_domains.privacy import PrivateStore, PrivacyError, opaque_id, ScopedIdentities
from nirs4all_domains.private_batch import PrivateBatch
from nirs4all_domains.storage import digest
from test_privacy import admission


class PrivateBatchControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pandas as pd
        from scripts.generate_unsupervised_fixtures import scenario
        from n4m._ffi import library_path
        cls.temp=tempfile.TemporaryDirectory(prefix='domains-synthetic-private-batch-')
        root=Path(cls.temp.name);cls.workspace=root/'workspace';cls.workspace.mkdir()
        cls.store=PrivateStore(root/'protected',cls.workspace)
        cache=root/'authorized-cache';cache.mkdir();path=cache/'X.csv'
        raw=scenario('gradient',n=48)['spectral']
        frame=pd.DataFrame(raw['spectra'],columns=raw['axis']);frame.insert(0,'observation_id',raw['observation_ids'])
        frame.to_csv(path,sep=';',index=False)
        cls.source={'admission':admission(),'matrix':str(path),'authorized_cache_root':str(cache),
            'source_id':'X','identity_evidence':'observation_identity_only','source_sha256':digest(path),
            'evidence_upper_bytes':512*1024,'scratch_upper_bytes':4096,'shape':[48,len(raw['axis'])],
            'study_scope':'SYNTHETIC-study','population_scope':'SYNTHETIC-population',
            'source_receipt_id':opaque_id(),'evidence_receipt_id':opaque_id(),'axis_unit':'nm',
            'original_axis_qualification':{'status':'unavailable','reason':'SYNTHETIC_GRID_ONLY','value':None}}
        cls.policy={'campaign_bytes':16*1024*1024,'per_task_bytes':4*1024*1024,'evidence_bytes':4*1024*1024,
            'workspace_max_bytes':1024*1024*1024,'reserve_free_bytes':1024,'max_concurrency':1}
        cls.approval={'workspace_ceiling':cls.policy['workspace_max_bytes'],'campaign_ceiling':cls.policy['campaign_bytes'],'owner_approved':True}
        cls.binary=Path(os.environ.get('N4DOMAINS_BIN','target/debug/n4domains'+('.exe' if os.name=='nt' else ''))).resolve()
        cls.library=Path(library_path()).resolve()

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def _batch(self,policy=None,approval=None):
        return PrivateBatch(self.store,state_root=self.workspace/'state',workspace=self.workspace,
            policy=policy if policy is not None else self.policy,
            approval=approval if approval is not None else self.approval,binary=self.binary,library=self.library)

    def test_missing_owner_budget_approval_refused(self):
        with self.assertRaisesRegex(PrivacyError,'RESOURCE_APPROVAL'):
            self._batch(approval={})

    def test_budget_refusal_precedes_native_fit(self):
        policy={**self.policy,'campaign_bytes':1}
        approval={**self.approval,'campaign_ceiling':1}
        with patch('nirs4all_domains.private_batch.NativeProfileStream') as native:
            with self.assertRaisesRegex(PrivacyError,'NEW_RESERVATION_ENVELOPE_EXCEEDED'):
                self._batch(policy,approval).profile(self.source)
            native.assert_not_called()

    def test_real_private_profiles_and_exact_cache_reuse(self):
        batch=self._batch();result=batch.profile(self.source)
        self.assertFalse(result['cache_hit'])
        value=self.store.get(result['receipt_id'])['payload']
        self.assertEqual(set(value['representations']),{'raw','snv'})
        self.assertEqual(value['new_pca_fits'],2);self.assertFalse(value['test_target_accessed'])
        self.assertTrue(all(v['n_observations']==48 for v in value['representations'].values()))
        journal=self.workspace/'state/journal.json';before=journal.read_bytes()
        with patch('nirs4all_domains.private_batch.NativeProfileStream') as native:
            self.assertTrue(batch.profile(self.source)['cache_hit']);native.assert_not_called()
        self.assertEqual(journal.read_bytes(),before)
        # Full private source paths and study names never enter common journal.
        self.assertNotIn(self.source['matrix'],before.decode())
        self.assertNotIn('SYNTHETIC-study',before.decode())
        self.assertFalse((self.workspace/'docs').exists())

    def test_unknown_rights_refuse_before_source_digest(self):
        source=copy.deepcopy(self.source);source['admission']['permissions']['access']['status']='unknown'
        batch=self._batch()
        with patch('nirs4all_domains.private_batch.digest') as read:
            with self.assertRaisesRegex(PrivacyError,'NOT_AUTHORIZED'):batch.profile(source)
            read.assert_not_called()

    def test_target_path_is_refused_before_decoding(self):
        source=copy.deepcopy(self.source);source['matrix']=str(Path(source['matrix']).with_name('Y.csv'))
        batch=self._batch()
        with patch('nirs4all_domains.private_batch.spectral_request') as decode:
            with self.assertRaisesRegex(PrivacyError,'SPECTRAL_MATRIX_PATH'):batch.profile(source)
            decode.assert_not_called()

    def test_failed_stage_publication_recovers_private_fit_without_refitting(self):
        from nirs4all_domains.storage import atomic_json as actual_write
        source=copy.deepcopy(self.source);source['evidence_receipt_id']=opaque_id();source['source_receipt_id']=opaque_id()
        batch=self._batch()
        stage_root=(self.store.root/'stages').resolve()
        interruptions=[]
        def interrupted(path,*args,**kwargs):
            # StageStore resolves its artifact path; Windows TEMP may use a
            # short-name alias. Compare the same resolved namespace on both sides.
            if Path(path).resolve().is_relative_to(stage_root):
                interruptions.append(True)
                raise OSError('SYNTHETIC_STAGE_PUBLICATION_INTERRUPTION')
            return actual_write(path,*args,**kwargs)
        with patch('nirs4all_domains.storage.atomic_json',side_effect=interrupted):
            with self.assertRaisesRegex(PrivacyError,'STAGE_NOT_COMPUTED'):batch.profile(source)
        self.assertEqual(interruptions,[True])
        self.assertTrue((self.store.evidence/(source['evidence_receipt_id']+'.json')).is_file())
        before=json.loads((self.workspace/'state/journal.json').read_text())['reserved_campaign_bytes']
        with patch('nirs4all_domains.private_batch.NativeProfileStream') as native:
            self.assertFalse(batch.profile(source)['cache_hit']);native.assert_not_called()
        after=json.loads((self.workspace/'state/journal.json').read_text())['reserved_campaign_bytes']
        self.assertGreater(after,before) # failed reservation retained; explicit retry charged

    def test_component_crossing_split_is_refused(self):
        with self.assertRaisesRegex(PrivacyError,'CROSSES_SPLIT'):
            ScopedIdentities(self.store).map_view('study','population',['a','b'],{'a':'physical','b':'physical'},
                {'a':'train','b':'test'},view_scope='synthetic-view')


if __name__=='__main__':unittest.main()
