import copy
import unittest
from nirs4all_domains.x_admission import authorize_x_source


def specification():
    return {'dataset_id':'example','content_version':'pinned','source_id':'X','catalog_tier':'private',
        'original_source_url':'https://example.org/original','provenance_urls':['https://example.org/original'],
        'permissions':{k:{'status':'allowed' if k!='redistribute_raw' else 'unknown','evidence':['original public-use statement'] if k!='redistribute_raw' else []}
            for k in ['access','local_analysis','publish_statistics','redistribute_raw']},
        'metadata_hashes':{'source':'f'*64},'identity_scope':'observation_conditional'}


class XAdmissionControls(unittest.TestCase):
    def test_original_permission_can_admit_private_tier_x_without_targets_or_physical_keys(self):
        value=authorize_x_source(specification())
        self.assertEqual(value['status'],'admitted_x_only')
        self.assertEqual(value['supervised_admission']['status'],'unavailable')
        self.assertEqual(value['numeric_original_equivalence']['status'],'unavailable')

    def test_public_tier_without_analysis_or_publication_rights_is_insufficient(self):
        for field in ['access','local_analysis','publish_statistics']:
            value=specification();value['catalog_tier']='public';value['permissions'][field]['status']='unknown'
            with self.assertRaisesRegex(ValueError,'NOT_AUTHORIZED'):authorize_x_source(value)

    def test_wrong_original_provenance_cannot_override_tier(self):
        value=specification();value['provenance_urls']=['https://example.org/another']
        with self.assertRaisesRegex(ValueError,'PROVENANCE'):authorize_x_source(value)

    def test_metadata_and_scores_cannot_invent_physical_identity(self):
        value=specification();value['identity_scope']='verified_physical_identity'
        with self.assertRaisesRegex(ValueError,'ORIGINAL_KEY_PROOF'):authorize_x_source(value)
        for field in ['Y_test','future_scores']:
            value=specification();value[field]=[999.]
            with self.assertRaisesRegex(ValueError,'OUTCOME_INPUT'):authorize_x_source(value)

    def test_raw_redistribution_permission_is_not_fabricated(self):
        value=authorize_x_source(specification())
        self.assertEqual(value['specification']['permissions']['redistribute_raw']['status'],'unknown')


if __name__=='__main__':unittest.main()
