"""Partial scientific work can resume only at the identical frozen draw identity."""
import json
from pathlib import Path
import tempfile
import unittest
from nirs4all_domains.unsupervised_checkpoint import checkpoint_draw,recover_draw


class PartialDrawControls(unittest.TestCase):
    def test_completed_prefix_survives_attempt_boundary_without_refit(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);contract={'source':'fixed','binary':'fixed','draw':0}
            value={'labels':[0,0,1],'selected_indices':[1,2,4]}
            checkpoint_draw(root/'1/draw-0.json',contract,value)
            (root/'2').mkdir()
            self.assertEqual(recover_draw(root,0,contract),value)
            self.assertIsNone(recover_draw(root,1,{**contract,'draw':1}))

    def test_changed_source_or_provider_cannot_reuse_partial_fit(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);contract={'source':'a','binary':'b'}
            checkpoint_draw(root/'1/draw-0.json',contract,{'labels':[0,1]})
            for changed in ({**contract,'source':'changed'},{**contract,'binary':'changed'}):
                with self.assertRaisesRegex(ValueError,'CONTRACT_MISMATCH'):recover_draw(root,0,changed)

    def test_corrupted_partial_labels_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path=root/'1/draw-0.json';contract={'draw':0}
            checkpoint_draw(path,contract,{'labels':[0,1]})
            data=json.loads(path.read_text());data['value']['labels']=[1,1];path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'CHECKPOINT_CORRUPT'):recover_draw(root,0,contract)


if __name__=='__main__':unittest.main()
