"""Transport isolation and native parity; these are engineering fixtures."""
import copy
import json
import os
from pathlib import Path
import unittest

from nirs4all_domains.native_profile_stream import NativeProfileStream
from nirs4all_domains.unsupervised import native_profile
from scripts.generate_unsupervised_fixtures import scenario


class NativeProfileStreamControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from n4m._ffi import library_path
        cls.binary=Path(os.environ.get('N4DOMAINS_BIN','target/debug/n4domains'+('.exe' if os.name=='nt' else ''))).resolve()
        cls.library=Path(library_path()).resolve()

    def test_target_rejection_does_not_poison_next_exact_request(self):
        spectral=scenario('separated',n=48)['spectral']
        expected=native_profile(spectral,'raw',self.binary,self.library)
        with NativeProfileStream(self.binary,self.library) as stream:
            for key in ['Y_test','model_performance']:
                bad=copy.deepcopy(spectral);bad[key]=[999.]*48
                with self.assertRaisesRegex(RuntimeError,'unknown field'):stream.profile(bad,'raw')
            self.assertEqual(stream.profile(spectral,'raw'),expected)
        self.assertEqual(stream.process.returncode,0)
        self.assertFalse(stream.reader.is_alive())

    def test_malformed_json_recovers_without_a_native_fit(self):
        with NativeProfileStream(self.binary,self.library) as stream:
            stream.process.stdin.write('{not-json}\n');stream.process.stdin.flush()
            rejected=json.loads(stream.responses.get(timeout=10))
            self.assertEqual(rejected['status'],'failed')
            self.assertIsNone(rejected['value']);self.assertTrue(rejected['reason'])
            with self.assertRaisesRegex(RuntimeError,'missing field'):stream.request({})
        self.assertEqual(stream.process.returncode,0)

    def test_provider_and_binary_changes_rejected_before_request(self):
        spectral=scenario('gradient',n=48)['spectral']
        with NativeProfileStream(self.binary,self.library) as stream:
            with self.assertRaisesRegex(ValueError,'BINARY_SCOPE'):stream.profile(spectral,'raw',binary=self.binary.with_name('another-binary'))
            with self.assertRaisesRegex(ValueError,'PROVIDER_SCOPE'):stream.profile(spectral,'raw',library=self.library.with_name('another-library'))

    def test_query_subset_preserves_complete_reference_population(self):
        spectral=scenario('gradient',n=48)['spectral'];query=spectral['observation_ids'][::4]
        with NativeProfileStream(self.binary,self.library) as stream:
            value=stream.profile(spectral,'raw',design={'ids':query})
        self.assertEqual(value['n_observations'],48)
        neighbors=value['neighborhoods']['value']['full_axis']
        self.assertEqual(neighbors['n_reference'],48)
        self.assertEqual(neighbors['n_query'],len(query))
        self.assertFalse(neighbors['approximate'])


if __name__=='__main__':unittest.main()
