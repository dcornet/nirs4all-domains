"""Additive external contracts reject unavailable/computed confusion and Y payloads."""
import copy
import json
from pathlib import Path
import unittest
import jsonschema
import nirs4all_domains


class UnsupervisedSchemaControls(unittest.TestCase):
    def row(self):
        missing={'status':'unavailable','reason':'NOT_MEASURED','value':None}
        return {'schema_version':1,'protocol_version':'domains.unsupervised.v0.1','record_id':'0'*64,
            'dataset_id':'fixture','source_id':'X','catalog_content':{'version':'1','content_hash':'1'*64,'descriptor_sha256':'2'*64},
            'source_dimensions':{},'identity_evidence':'observation_identity_only','population_relationship':missing,
            'representations':{'raw':missing,'snv':missing},'representation_agreement':missing,
            'structural_stability':missing,'metadata_agreement':missing,'split_support':missing,'resource_cost':{},
            'baseline_ref':{'path':'docs/example.json','sha256':'3'*64},'test_target_accessed':False,
            'universal_shortcut_score':None,'limitations':['Missing information is not low susceptibility.']}

    def schema(self):
        return json.loads((Path(nirs4all_domains.__file__).parent/'unsupervised-evidence.v1.schema.json').read_text())

    def test_packaged_root_schema_parity(self):
        self.assertEqual(self.schema(),json.loads(Path('schemas/unsupervised-evidence.v1.schema.json').read_text()))
        jsonschema.validate(self.row(),self.schema())

    def test_missing_result_cannot_be_reported_as_computed(self):
        row=copy.deepcopy(self.row());row['representations']['raw']={'status':'computed','reason':None,'value':None}
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(row,self.schema())

    def test_target_payload_and_arbitrary_global_score_are_rejected(self):
        for field,value in [('Y_test',[1,2]),('universal_shortcut_score',.99)]:
            row=copy.deepcopy(self.row());row[field]=value
            with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(row,self.schema())


if __name__=='__main__':unittest.main()
