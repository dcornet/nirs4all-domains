import csv
from pathlib import Path
import tempfile
import unittest
from nirs4all_domains.keyed_source_x import read_keyed_x,verify_keyed_x


class KeyedSourceXControls(unittest.TestCase):
    def write(self,path,ids,target):
        with path.open('w',newline='') as out:
            w=csv.writer(out,delimiter=';');w.writerow(['key','reference','1000','1001'])
            for s in ids:w.writerow([s,target,ord(s),2])

    def test_reference_mutation_does_not_enter_projection_or_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'source.csv';self.write(path,['a','b'],'1.2');a=read_keyed_x(path,'key',['1000','1001'],'nm')
            self.write(path,['a','b'],'RETAINED_REFERENCE_MUST_NOT_BE_DECODED');b=read_keyed_x(path,'key',['1000','1001'],'nm')
            self.assertEqual(a,b)

    def test_permuted_rows_join_explicit_keys_and_never_claim_physical_independence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'source.csv';self.write(path,['b','a'],'invalid');source=read_keyed_x(path,'key',['1000','1001'],'nm')
            canonical={**source,'observation_ids':['c:a','c:b'],'spectra':list(reversed(source['spectra']))}
            proof=verify_keyed_x(source,canonical,{'c:a':'a','c:b':'b'})
            self.assertEqual(proof['exact_spectral_rows'],2);self.assertFalse(proof['physical_or_assay_independence_verified'])
            with self.assertRaisesRegex(ValueError,'ONE_TO_ONE'):verify_keyed_x(source,canonical,{'c:a':'a','c:b':'a'})

    def test_equal_counts_or_axis_mismatch_do_not_authorize_matching(self):
        source={'observation_ids':['a','b'],'spectra':[[1,2],[3,4]],'axis':[1000,1001],'axis_unit':'nm'}
        with self.assertRaisesRegex(ValueError,'ONE_TO_ONE'):verify_keyed_x(source,source,{})
        with self.assertRaisesRegex(ValueError,'AXES'):verify_keyed_x(source,{**source,'axis':[1000,1002]},{'a':'a','b':'b'})


if __name__=='__main__':unittest.main()
