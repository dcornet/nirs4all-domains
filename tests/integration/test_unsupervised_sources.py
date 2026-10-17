"""Provenance evidence cannot be replaced by filenames, counts or names."""
import unittest
from nirs4all_domains.unsupervised_sources import relation


class UnsupervisedSourceControls(unittest.TestCase):
    def test_similar_names_and_equal_counts_do_not_establish_overlap(self):
        a={'name':'leaf-v1','n':100};b={'name':'leaf-v2','n':100}
        self.assertEqual(relation(a,b)['status'],'not_identifiable')

    def test_shared_citation_does_not_establish_physical_pairing(self):
        r=relation({'cited_study_references':['paper']},{'cited_study_references':['paper']})
        self.assertEqual(r['status'],'exploratory')
        self.assertIsNone(r['value']['physical_overlap']['value'])

    def test_verified_original_namespace_and_keys_establish_same_objects(self):
        a={'physical_namespace':'study:bag','original_keys_verified':True,'original_keys':['a','b']}
        b={**a,'original_keys':['b','c']}
        r=relation(a,b)['value']
        self.assertEqual(r['n_shared_physical_keys'],1)
        self.assertIsNone(r['biological_independence']['value'])

    def test_same_key_text_in_other_namespaces_is_not_same_object(self):
        a={'physical_namespace':'study:a','original_keys_verified':True,'original_keys':['1']}
        b={**a,'physical_namespace':'study:b'}
        self.assertEqual(relation(a,b)['status'],'not_identifiable')

    def test_unverified_matching_keys_remain_unverified(self):
        a={'physical_namespace':'study:a','original_keys_verified':False,'original_keys':['1']}
        self.assertEqual(relation(a,a)['status'],'not_identifiable')

    def test_source_revisions_are_grouped_without_independence_claim(self):
        a={'original_package_id':'original'}
        r=relation(a,{**a,'revision':2})['value']
        self.assertEqual(r['source_relationship'],'same_original_source_package')
        self.assertEqual(r['physical_overlap']['status'],'unavailable')


if __name__=='__main__':unittest.main()
