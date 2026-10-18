"""Prospective contracts fail closed; no scientific result is relabeled."""
import copy
import json
from pathlib import Path
import unittest
import jsonschema

from nirs4all_domains.bank import schema_check
from nirs4all_domains.storage import digest,fingerprint


class Alpha13ContractControls(unittest.TestCase):
    def contract(self):
        return json.loads(Path('docs/benchmarks/alpha13/falsification-contract.json').read_text())

    def test_frozen_hypotheses_and_outcomes_are_bound_exactly(self):
        c=self.contract();schema_check(c,'falsification-contract')
        expected=c.pop('contract_id');self.assertEqual(fingerprint(c),expected)
        for name in ['hypothesis_register_ref','future_outcome_ref','operational_preregistration_ref']:
            self.assertEqual(digest(c[name]['path']),c[name]['sha256'])
        self.assertEqual(c['study_roles']['independent_confirmation_studies'],0)
        self.assertFalse(c['test_target_accessed']);self.assertFalse(c['model_performance_used'])

    def test_five_bindings_cannot_silently_duplicate_or_replace_a_hypothesis(self):
        c=self.contract();c['descriptor_bindings'][4]=copy.deepcopy(c['descriptor_bindings'][0])
        with self.assertRaises(jsonschema.ValidationError):schema_check(c,'falsification-contract')

    def test_unavailable_confirmation_power_cannot_contain_a_fabricated_value(self):
        c=self.contract();c['confirmation_power']['value']=.95
        with self.assertRaises(jsonschema.ValidationError):schema_check(c,'falsification-contract')

    def test_target_or_performance_inputs_cannot_be_admitted_by_schema(self):
        for key in ['test_target_accessed','model_performance_used']:
            c=self.contract();c[key]=True
            with self.assertRaises(jsonschema.ValidationError):schema_check(c,'falsification-contract')

    def test_x_only_source_schema_cannot_promote_reference_ownership(self):
        from nirs4all_domains.x_admission import authorize_x_source
        from test_x_admission import specification
        value=authorize_x_source(specification());schema_check(value,'x-source-admission')
        value['supervised_admission']={'status':'computed','reason':None,'value':True}
        with self.assertRaises(jsonschema.ValidationError):schema_check(value,'x-source-admission')


if __name__=='__main__':unittest.main()
