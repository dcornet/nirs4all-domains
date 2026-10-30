"""D1 adversarial transport and real-provider qualification; no Y or real data."""
from copy import deepcopy
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from jsonschema import ValidationError
from nirs4all_domains.multiscale import describe, markdown, validate_descriptor
from nirs4all_domains.storage import fingerprint

ROOT = Path(__file__).resolve().parents[2]


def profile():
    native = {'native_status': 0, 'noise_label': -1, 'n_clusters': 2,
              'labels': [0, 0, 1, 1, -1], 'membership_strengths': [1, .8, 1, .9, 0],
              'cluster_persistence': [.2, .8], 'nonfinite_diagnostics': [],
              'hierarchy': [{'parent': -1, 'size': 5, 'label': -1, 'lambda_birth': 0, 'lambda_death': 1, 'stability': 5},
                            {'parent': 0, 'size': 2, 'label': 0, 'lambda_birth': 1, 'lambda_death': 2, 'stability': 1},
                            {'parent': 0, 'size': 2, 'label': 1, 'lambda_birth': 1, 'lambda_death': 3, 'stability': 2}]}
    parameters = {'min_cluster_size': 2, 'min_samples': 1, 'selection_method': 'eom', 'allow_single_cluster': False}
    return {'protocol_version': 'domains.unsupervised.v0.1', 'n_observations': 5,
            'representation': 'raw', 'pca': {'backend': 'synthetic fixture', 'eigenvalues': [2, 1]},
            'provider': {'version': '1.3.6+abi.2.19.0', 'abi': '2.19.0', 'binary_sha256': '0' * 64},
            'cluster_settings': [{'status': 'computed', 'reason': None, 'value': {
                'min_cluster_size': 2, 'min_samples': 1, 'n_clusters': 2,
                'labels': native['labels'].copy(), 'noise_fraction': .2,
                'hierarchy_evidence': {'status': 'computed', 'reason': None, 'value': {
                    'protocol_version': 'domains.hdbscan_transport.v1', 'parameters': parameters, 'hdbscan': native}}}}]}


def native(report):
    return report['cluster_settings'][0]['value']['hierarchy_evidence']['value']['hdbscan']


class DescriptorTests(unittest.TestCase):
    def test_exact_support_and_no_mutation(self):
        report = profile(); before = deepcopy(report)
        result = describe(report); value = result['selected_structure']['value']
        self.assertEqual(report, before)
        self.assertEqual(result, describe(report))
        self.assertEqual(result['source']['content_sha256'], fingerprint(report))
        self.assertEqual([r['n_observations'] for r in value['clusters']], [2, 2])
        self.assertEqual([r['persistence']['value'] for r in value['clusters']], [.2, .8])
        self.assertEqual([r['hierarchy_node_index']['value'] for r in value['clusters']], [1, 2])
        self.assertEqual(value['noise_fraction'], .2)
        self.assertAlmostEqual(value['persistence_distribution']['value']['median'], .5, delta=1e-12)
        self.assertIn('not a resampling statistic', markdown(result))

    def test_all_noise_is_not_low_risk_or_proven_continuity(self):
        report = profile(); h = native(report)
        h.update(n_clusters=0, labels=[-1]*5, membership_strengths=[0]*5, cluster_persistence=[])
        h['hierarchy'] = h['hierarchy'][:1]
        report['cluster_settings'][0]['value'].update(noise_fraction=1, labels=h['labels'], n_clusters=0)
        result = describe(report); value = result['selected_structure']['value']
        self.assertEqual(value['persistence_distribution']['status'], 'not_applicable')
        self.assertEqual(value['n_noise'], 5)
        self.assertIn('does not establish continuity', result['finding']['observation'])

    def test_single_cluster_and_small_support(self):
        report = profile(); h = native(report)
        h.update(n_clusters=1, labels=[0, 0, -1, -1, -1], membership_strengths=[1, .8, 0, 0, 0], cluster_persistence=[.2])
        h['hierarchy'] = h['hierarchy'][:2]
        report['cluster_settings'][0]['value'].update(noise_fraction=.6, labels=h['labels'], n_clusters=1)
        result = describe(report)
        self.assertIn('multiple distinct populations are not established', result['finding']['observation'])
        self.assertEqual(result['selected_structure']['value']['clusters'][0]['n_observations'], 2)

    def test_missing_hierarchy_does_not_invent_nodes_or_remove_persistence(self):
        report = profile(); del native(report)['hierarchy']
        result = describe(report)
        self.assertEqual(result['hierarchy']['reason'], 'ORIGINAL_HIERARCHY_NOT_RETAINED')
        self.assertEqual(result['selected_structure']['value']['clusters'][0]['persistence']['value'], .2)
        report = profile(); del native(report)['hierarchy'][0]['lambda_birth']
        self.assertEqual(describe(report)['hierarchy']['reason'], 'ORIGINAL_HIERARCHY_FIELDS_NOT_RETAINED')

    def test_compact_history_lacks_persistence_without_fabrication(self):
        report = profile(); del report['cluster_settings'][0]['value']['hierarchy_evidence']
        result = describe(report); value = result['selected_structure']['value']
        self.assertEqual(value['n_selected_clusters'], 2)
        self.assertEqual(value['clusters'][0]['persistence']['reason'], 'PERSISTENCE_NOT_RETAINED')
        self.assertEqual(result['hierarchy']['status'], 'unavailable')
        del report['cluster_settings'][0]['value']['labels']
        self.assertEqual(describe(report)['selected_structure']['status'], 'unavailable')

    def test_nonfinite_persistence_is_unavailable_not_finite_subset_summary(self):
        report = profile(); native(report)['cluster_persistence'][0] = None
        native(report)['nonfinite_diagnostics'].append({'field': 'cluster_persistence', 'index': 0, 'native_value': 'undefined_nan'})
        value = describe(report)['selected_structure']['value']
        self.assertEqual(value['clusters'][0]['persistence']['status'], 'unavailable')
        self.assertEqual(value['clusters'][1]['persistence']['value'], .8)
        self.assertEqual(value['persistence_distribution']['reason'], 'INCOMPLETE_SELECTED_CLUSTER_PERSISTENCE')
        for invalid in (float('nan'), float('inf')):
            native(report)['cluster_persistence'][0] = invalid
            with self.assertRaises(ValueError): describe(report)

    def test_invalid_persistence_never_clamped(self):
        for invalid in (-1, True, 'strong'):
            report = profile(); native(report)['cluster_persistence'][0] = invalid
            self.assertEqual(describe(report)['selected_structure']['value']['clusters'][0]['persistence']['reason'], 'INVALID_NATIVE_PERSISTENCE')

    def test_native_count_and_tree_adversaries_are_rejected(self):
        for field, value in [('labels', [0]), ('labels', [0, 0, 2, 2, -1]), ('n_clusters', 3),
                             ('cluster_persistence', [.2]), ('membership_strengths', [1]*5)]:
            report = profile(); native(report)[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError): describe(report)
        for field, value in [('size', 1), ('label', 1), ('parent', 2)]:
            report = profile(); native(report)['hierarchy'][1][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError): describe(report)
        report = profile(); report['cluster_settings'][0]['value']['noise_fraction'] = 0
        with self.assertRaises(ValueError): describe(report)

    def test_frozen_configuration_mismatch_is_rejected(self):
        report = profile()
        report['cluster_settings'][0]['value']['hierarchy_evidence']['value']['parameters']['min_samples'] = 4
        with self.assertRaises(ValueError): describe(report)

    def test_degenerate_infinite_density_convention_is_visible(self):
        report = profile(); native(report)['cluster_persistence'] = [1, 1]
        native(report)['hierarchy'][1]['lambda_death'] = None
        native(report)['nonfinite_diagnostics'] = [{'field': 'hierarchy.lambda_death', 'index': 1, 'native_value': 'positive_infinity'}]
        result = describe(report)
        self.assertEqual(result['selected_structure']['value']['persistence_convention'], 'global_infinite_lambda_fallback_one')
        self.assertIn('without strong empirical support', markdown(result))

    def test_repeats_and_crossed_factors_do_not_create_independent_support(self):
        report = profile(); report['metadata'] = {'specimen': ['a']*5, 'genotype': ['a','b','a','b','a'], 'block': [1,1,2,2,3]}
        result = describe(report)
        for row in result['selected_structure']['value']['clusters']:
            self.assertEqual(row['independent_unit_support']['status'], 'unavailable')
        self.assertEqual(result['resampling_stability']['status'], 'unavailable')
        self.assertNotIn('metadata', result)

    def test_target_and_estimator_not_required_or_accessed(self):
        a = profile(); b = deepcopy(a); b.update(Y_test=[999]*5, estimator='never fitted')
        self.assertEqual(describe(a)['selected_structure'], describe(b)['selected_structure'])
        with patch('nirs4all_domains.multiscale.native_summary', side_effect=AssertionError('fit unavailable')):
            report = profile(); report['cluster_settings'][0].update(status='unavailable', reason='ZERO_SPECTRAL_VARIANCE', value=None)
            self.assertEqual(describe(report)['selected_structure']['reason'], 'ZERO_SPECTRAL_VARIANCE')

    def test_full_structure_report_keeps_technical_mean_unit_and_separate_B60(self):
        p = profile()
        report = {'protocol_version': 'domains.structure.v0.1', 'provider': p['provider'],
                  'population': {'selected_representation': 'technical_mean', 'partition': 'train'},
                  'settings': [{'parameters': p['cluster_settings'][0]['value']['hierarchy_evidence']['value']['parameters'],
                    'status': 'computed', 'reason': None, 'reference': {'observation_ids': list('abcde'),
                        'pca': {}, 'hdbscan': native(p), 'noise_fraction': .2},
                    'stability': {'successful_draws': 60, 'ari': .9}}]}
        result = describe(report)
        self.assertEqual(result['selected_structure']['value']['support_unit'], 'fitted representation row (technical mean)')
        self.assertEqual(result['separate_resampling_evidence_pointer'], '/settings/0/stability')
        self.assertEqual(result['resampling_stability']['status'], 'unavailable')

    def test_unknown_provider_does_not_gain_persistence_qualification(self):
        report = profile(); report['provider']['version'] = '999.0'
        self.assertEqual(describe(report)['selected_structure']['value']['clusters'][0]['persistence']['reason'], 'PROVIDER_PERSISTENCE_SEMANTICS_NOT_QUALIFIED')
        report = profile(); report['provider']['abi'] = [99, 0, 0]
        self.assertEqual(describe(report)['selected_structure']['value']['clusters'][0]['persistence']['reason'], 'PROVIDER_PERSISTENCE_SEMANTICS_NOT_QUALIFIED')

    def test_unavailable_summary_preserves_native_rows(self):
        with patch('nirs4all_domains.multiscale.native_summary', side_effect=ImportError()):
            value = describe(profile())['selected_structure']['value']
        self.assertEqual(value['clusters'][0]['persistence']['value'], .2)
        self.assertEqual(value['persistence_distribution']['status'], 'unavailable')

    def test_schema_parity_and_unsupported_claim_states(self):
        path = ROOT/'schemas/selected-branch-persistence.v1.schema.json'
        from nirs4all_domains import multiscale
        self.assertEqual(json.loads(path.read_text()), json.loads(Path(multiscale.__file__).with_name(path.name).read_text()))
        value = describe(profile())
        for key in ('resampling_stability',):
            bad = deepcopy(value); bad[key] = {'status':'computed','reason':None,'value':{'probability':.99}}
            with self.assertRaises(ValidationError): validate_descriptor(bad)
        bad = deepcopy(value); bad['universal_risk'] = .2
        with self.assertRaises(ValidationError): validate_descriptor(bad)

    def test_checked_public_example_binds_to_original_tree(self):
        folder = ROOT/'docs/examples/multiscale'
        source = json.loads((folder/'source-report.json').read_text())
        saved = json.loads((folder/'descriptor.json').read_text())
        validate_descriptor(saved)
        current = describe(source)
        self.assertEqual(current['source'], saved['source'])
        self.assertEqual(current['selected_structure']['value']['clusters'], saved['selected_structure']['value']['clusters'])
        self.assertEqual(current['hierarchy'], saved['hierarchy'])
        self.assertEqual(source['cluster_settings'][0]['value']['hierarchy_evidence']['value']['hdbscan']['n_clusters'], 3)

    def test_public_provider_fixture_content_is_pinned(self):
        from nirs4all_domains.storage import digest
        self.assertEqual(digest(ROOT/'tests/fixtures/multiscale/methods-hdbscan-v1.json'),
                         '294457336e820754b5047851760ea0d02391c1c552cd9420cc80223179297cd4')

    def test_cli_source_immutable_and_collision_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)/'report.json'; out = Path(directory)/'descriptor.json'
            source.write_text(json.dumps(profile())); before = source.read_bytes()
            command = [sys.executable, '-m', 'nirs4all_domains.multiscale', str(source)]
            subprocess.run([*command, '--out', str(out)], check=True, capture_output=True)
            self.assertEqual(source.read_bytes(), before)
            self.assertTrue(out.with_suffix('.md').exists())
            self.assertNotEqual(subprocess.run([*command, '--out', str(source)], capture_output=True).returncode, 0)
            self.assertEqual(source.read_bytes(), before)


class NativeProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binary = os.environ.get('N4DOMAINS_BIN')
        cls.library = os.environ.get('N4DOMAINS_METHODS_LIBRARY')
        if not cls.binary or not cls.library:
            raise unittest.SkipTest('explicit native binary/library required; CI executes this gate')
        fixture = json.loads((ROOT/'tests/fixtures/multiscale/methods-hdbscan-v1.json').read_text())
        case = fixture['cases'][0]
        flat = [struct.unpack('>d', bytes.fromhex(v))[0] for v in case['input_hex']]
        cls.spectral = {'source_id': 'public-synthetic-blobs', 'observation_ids': [f'o{i}' for i in range(case['rows'])],
            'identity_evidence': 'observation_identity_only', 'axis': [1, 2], 'axis_unit': 'logical',
            'spectra': [flat[i:i+2] for i in range(0, len(flat), 2)]}

    @classmethod
    def run_profile(cls, spectral, representation='raw', include=True):
        payload = {'spectral': spectral, 'representation': representation, 'query_ids': [], 'include_neighbors': False}
        command = [cls.binary, 'x-profile', '--methods-library', cls.library]
        if include: command.append('--include-hierarchy')
        return subprocess.run(command, input=json.dumps(payload), text=True, capture_output=True, timeout=60)

    def test_opt_in_native_transport_preserves_default_numerical_report(self):
        base = self.run_profile(self.spectral, include=False)
        extended = self.run_profile(self.spectral)
        self.assertEqual(base.returncode, 0, base.stderr); self.assertEqual(extended.returncode, 0, extended.stderr)
        old, new = json.loads(base.stdout), json.loads(extended.stdout)
        cleaned = deepcopy(new)
        for setting in cleaned['cluster_settings']: setting['value'].pop('hierarchy_evidence')
        self.assertEqual(old, cleaned)
        for index in (0, 1):
            result = describe(new, setting_index=index)
            self.assertEqual(result['selected_structure']['value']['n_observations'], 120)
            self.assertEqual(result['hierarchy']['status'], 'computed')
            self.assertEqual(result['selected_structure']['value']['persistence_distribution']['status'], 'computed')

    def test_raw_snv_geometries_remain_distinct(self):
        from nirs4all_domains.unsupervised import represent
        snv = represent(self.spectral, 'snv')
        result = self.run_profile(snv, 'snv')
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout); descriptor = describe(report)
        self.assertEqual(descriptor['representation']['name'], 'snv')
        self.assertEqual(descriptor['selected_structure']['value']['n_observations'], 120)
        self.assertEqual(descriptor['source']['content_sha256'], fingerprint(report))
        # Tied/duplicate SNV coordinates may trigger provider persistence conventions;
        # do not require the raw partition to survive this geometry change.
        self.assertNotEqual(snv['spectra'], self.spectral['spectra'])

    def test_zero_variance_spectra_fail_without_inventing_descriptor(self):
        spectral = deepcopy(self.spectral); spectral['spectra'] = [[1., 1.]]*120
        output = self.run_profile(spectral)
        self.assertNotEqual(output.returncode, 0)
        self.assertIn('ZERO_SPECTRAL_VARIANCE', output.stderr)


if __name__ == '__main__':
    unittest.main()
