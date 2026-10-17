"""Paired X field isolation and exact keyed correspondence before numerical work."""
import csv
from pathlib import Path
import tempfile
import unittest
from nirs4all_domains.paired_x import read_litter_view,match_litter_views


class PairedXControls(unittest.TestCase):
    def write(self,path,ids,target):
        with path.open('w',newline='') as stream:
            writer=csv.writer(stream);writer.writerow(['ID','Nmass','400','401','402'])
            writer.writerows([[s,target,ord(s),1,2] for s in ids])

    def test_target_mutation_does_not_change_source_x_or_pairing(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'source.csv';self.write(path,['a','b','c'],'1.25')
            a=read_litter_view(path,'view',axis=(400,401,402))
            self.write(path,['a','b','c'],'INVALID_AND_CONTRADICTORY_Y_TEST')
            b=read_litter_view(path,'view',axis=(400,401,402))
            self.assertEqual(a,b)
            self.assertNotIn('Nmass',a)

    def test_reordered_views_join_original_keys_and_preserve_unpaired_parent(self):
        with tempfile.TemporaryDirectory() as folder:
            left,right=Path(folder)/'left.csv',Path(folder)/'right.csv'
            self.write(left,['a','b','c'],'invalid');self.write(right,['c','a'],'invalid')
            a=read_litter_view(left,'left',axis=(400,401,402));b=read_litter_view(right,'right',axis=(400,401,402))
            views,proof=match_litter_views(a,b)
            self.assertEqual(views[0]['spectra'],views[1]['spectra'])
            self.assertEqual(proof['left_only'],['b'])
            self.assertEqual(len(a['spectra']),3)
            self.assertEqual(proof['parent_observation_counts'],[3,2])

    def test_duplicate_original_keys_are_refused_without_aggregation(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'source.csv';self.write(path,['a','a'],'invalid')
            with self.assertRaisesRegex(ValueError,'UNIQUE_ORIGINAL'):read_litter_view(path,'view',axis=(400,401,402))

    def test_axis_mismatch_is_not_interpolated(self):
        a={'axis':[400,401],'axis_unit':'nm','observation_ids':['a'],'spectra':[[1,2]]}
        with self.assertRaisesRegex(ValueError,'IDENTICAL_ORIGINAL'):match_litter_views(a,{**a,'axis':[400,402]})


if __name__=='__main__':unittest.main()
