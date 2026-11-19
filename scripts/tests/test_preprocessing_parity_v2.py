import copy
import hashlib
import json
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_preprocessing_parity as legacy
import check_preprocessing_parity_v2 as parity
from test_preprocessing_parity import binding_case


def seal(case):
    case['result'].pop('evidence_sha256', None)
    case['result']['evidence_sha256'] = legacy.fingerprint(case['result'])
    case['result_json'] = json.dumps(case['result'])
    case['result_json_sha256'] = hashlib.sha256(case['result_json'].encode()).hexdigest()


def artifacts(delta=0.0):
    a = binding_case()
    a['result']['reported_value'] = 1.0
    a['result']['representations'][0]['value']['comparisons'] = {'clusters': {'status': 'unavailable', 'reason': 'NOT_REQUESTED', 'value': None}}
    b = copy.deepcopy(a)
    b['result']['reported_value'] += delta
    b['original_wasm_request'] = copy.deepcopy(a['request'])
    seal(a)
    seal(b)
    common = {'fixture_sha256': 'f'*64, 'descriptor_bank_sha256': 'b'*64, 'new_real_scientific_fits': 0}
    return ({**common, 'protocol_version': 'domains.browser_preprocessing_sensitivity_wasm.v1', 'provider': {'version': legacy.VERSION}, 'cases': [a], 'refusals': []},
            {**common, 'protocol_version': 'domains.browser_preprocessing_sensitivity_native.v1', 'provider_version': legacy.VERSION, 'wasm_artifact_sha256': 'a'*64, 'cases': [b], 'refused_before_provider': []})


class VerificationV2(unittest.TestCase):
    def test_legitimate_different_result_digests_pass_only_with_numeric_tolerance(self):
        for delta, status in [(1e-12, 'passed'), (1e-4, 'failed')]:
            a, b = artifacts(delta)
            self.assertNotEqual(a['cases'][0]['result']['evidence_sha256'], b['cases'][0]['result']['evidence_sha256'])
            result = parity.qualify(a, b, 'a'*64)
            self.assertEqual(result['integrity'], 'passed')
            self.assertEqual(result['numeric_parity'], status)

    def test_corrupt_result_raw_or_canonical_integrity_fails(self):
        for key in ('evidence_sha256', 'result_json_sha256'):
            a, b = artifacts()
            target = b['cases'][0]['result'] if key == 'evidence_sha256' else b['cases'][0]
            target[key] = '0'*64
            with self.assertRaises(AssertionError):
                parity.qualify(a, b, 'a'*64)

    def test_self_consistent_outer_digest_cannot_bless_malformed_payload_fingerprints(self):
        a, b = artifacts()
        b['cases'][0]['result']['receipt']['provider_calls'] = [{'row_keys': ['a','b','c'], 'operation': 'pca', 'payload_sha256': 'bad', 'request_sha256': 'bad'}]
        seal(b['cases'][0])
        with self.assertRaisesRegex(AssertionError, 'INVALID_FINGERPRINT_SHAPE'):
            parity.qualify(a, b, 'a'*64)

    def test_wrong_provider_source_order_or_ancestor_is_not_numeric_tolerance(self):
        mutations = [lambda b: b.update(provider_version='1.4.1'),
                     lambda b: b['cases'][0]['request']['dataset'].update(content_sha256='0'*64),
                     lambda b: b['cases'][0]['request'].update(reference_keys=['c','b','a']),
                     lambda b: b['cases'][0].update(reference_case_id='other')]
        for mutate in mutations:
            a, b = artifacts()
            mutate(b)
            seal(b['cases'][0])
            with self.assertRaises(AssertionError):
                parity.qualify(a, b, 'a'*64)

    def test_status_count_unknown_hash_and_method_changes_remain_failures(self):
        for key, left, right in [('unknown_sha256','a'*64,'b'*64),('count',3,4),('method_id','pearson','spearman')]:
            a, b = artifacts()
            a['cases'][0]['result'][key] = left
            b['cases'][0]['result'][key] = right
            seal(a['cases'][0]); seal(b['cases'][0])
            self.assertEqual(parity.qualify(a, b, 'a'*64)['numeric_parity'], 'failed')

    def test_roles_are_structural_not_a_generic_hash_suffix_skip(self):
        self.assertEqual(parity.fingerprint_role('/evidence_sha256'), 'backend_result_integrity')
        self.assertIsNone(parity.fingerprint_role('/dataset/content_sha256'))
        self.assertIsNone(parity.fingerprint_role('/receipt/provider_calls/0/inputs/metadata/sha256'))
        self.assertIsNone(parity.fingerprint_role('/arbitrary/response_sha256'))
        self.assertEqual(parity.fingerprint_role('/representations/0/value/factors/0/receipt/pca_id'), 'backend_pca_evidence_identity')
        path='/representations/0/value/support/value/projection/value'
        self.assertEqual(parity.differences({'fit_state_sha256':'a'*64,'count':3},{'fit_state_sha256':'b'*64,'count':3},path=path),[])
        self.assertIsNone(parity.fingerprint_role('/arbitrary/fit_state_sha256'))
        self.assertIsNone(parity.fingerprint_role('/representations/0/value/factors/0/value/method_id'))
        self.assertEqual(len(parity.differences({'one': 1.0, 'two': 2.0}, {'one': 10.0, 'two': 20.0})), 2)


if __name__ == '__main__':
    unittest.main()
