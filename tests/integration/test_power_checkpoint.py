import json
from pathlib import Path
import tempfile
import unittest
from nirs4all_domains.power_checkpoint import recover_prefix,save_prefix
from nirs4all_domains.storage import atomic_json


class PowerCheckpointControls(unittest.TestCase):
    def test_longest_exact_prefix_recovers_without_duplicate_draws(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);c={'source':'frozen','provider':'native','seed':13}
            a=[{'draw':i,'status':'computed'} for i in range(3)]
            save_prefix(root/'1/prefix-raw.json',c,a[:1]);save_prefix(root/'2/prefix-raw.json',c,a)
            self.assertEqual(recover_prefix(root,'raw',c),a)

    def test_corrupt_provider_or_checksum_refuses_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);c={'provider':'native:sha'};path=root/'1/prefix-raw.json'
            save_prefix(path,c,[{'draw':0}])
            with self.assertRaisesRegex(ValueError,'CONTRACT'):recover_prefix(root,'raw',{'provider':'other'})
            data=json.loads(path.read_text());data['records'][0]['fit_changed']=True;atomic_json(path,data)
            with self.assertRaisesRegex(ValueError,'CHECKSUM'):recover_prefix(root,'raw',c)

    def test_diverging_or_noncontiguous_prefixes_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);c={'seed':13};save_prefix(root/'1/prefix-raw.json',c,[{'draw':0,'x':1}])
            save_prefix(root/'2/prefix-raw.json',c,[{'draw':0,'x':2}])
            with self.assertRaisesRegex(ValueError,'CONFLICTING'):recover_prefix(root,'raw',c)
            with self.assertRaisesRegex(ValueError,'CONTIGUOUS'):save_prefix(root/'bad.json',c,[{'draw':1}])


if __name__=='__main__':unittest.main()
