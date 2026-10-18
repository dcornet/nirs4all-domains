"""Public synthetic adversaries for the missing original-manifest boundary."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nirs4all_domains.original_source import manifest_file, required_keyed_equivalence
from nirs4all_domains.storage import digest
from nirs4all_domains.confrontation import admit, dependency_map


class OriginalManifestBindings(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='domains-public-original-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.original = self.root/'declared'/'original.csv'
        self.original.parent.mkdir()
        self.original.write_text('key;signal;reference\na;1;7\n', encoding='utf-8')
        self.row = {'dataset_id': 'public-synthetic', 'file_name': 'original.csv',
            'local_path_if_any': str(self.original), 'sha256_or_partial_hash': digest(self.original)}

    def bind(self, row=None):
        return manifest_file(row or self.row, 'public-synthetic', [self.root])

    def test_exact_source_locator_and_content_binding(self):
        self.assertEqual(self.bind(), self.original.resolve())

    def test_unrelated_same_basename_is_not_a_locator(self):
        self.row['local_path_if_any'] = ''
        with self.assertRaisesRegex(ValueError, 'EXPLICIT_ORIGINAL_LOCAL_LOCATOR'):
            self.bind()

    def test_wrong_manifest_source_identity(self):
        self.row['dataset_id'] = 'different-source'
        with patch('nirs4all_domains.original_source.digest') as reader:
            with self.assertRaisesRegex(ValueError, 'SOURCE_IDENTITY_CONTRADICTION'):
                self.bind()
            reader.assert_not_called()

    def test_manifest_filename_contradiction(self):
        self.row['file_name'] = 'another.csv'
        with self.assertRaisesRegex(ValueError, 'FILENAME_CONTRADICTION'):
            self.bind()

    def test_original_content_mutation(self):
        self.original.write_text('changed', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'CONTENT_CONTRADICTION'):
            self.bind()

    def test_partial_hash_cannot_certify_full_content(self):
        self.row['sha256_or_partial_hash'] = self.row['sha256_or_partial_hash'][:16]
        with self.assertRaisesRegex(ValueError, 'FULL_ORIGINAL_CONTENT_HASH'):
            self.bind()

    def test_explicit_sha256_codec_prefix_preserves_full_digest(self):
        self.row['sha256_or_partial_hash'] = 'sha256:'+self.row['sha256_or_partial_hash']
        self.assertEqual(self.bind(), self.original.resolve())

    def test_missing_declared_file_does_not_fall_back_to_same_basename(self):
        self.row['local_path_if_any'] = str(self.root/'missing'/'original.csv')
        with self.assertRaisesRegex(ValueError, 'NOT_LOCALLY_AVAILABLE'):
            self.bind()

    def test_declared_relative_locator_keeps_complete_path(self):
        self.row['local_path_if_any'] = 'declared/original.csv'
        self.assertEqual(self.bind(), self.original.resolve())

    def test_relative_locator_ambiguity_is_refused(self):
        second = self.root/'second'
        other = second/'declared'/'original.csv'
        other.parent.mkdir(parents=True)
        other.write_bytes(self.original.read_bytes())
        self.row['local_path_if_any'] = 'declared/original.csv'
        with self.assertRaisesRegex(ValueError, 'UNAMBIGUOUS_DECLARED'):
            manifest_file(self.row, 'public-synthetic', [self.root, second])

    def test_path_escape_is_refused_even_with_matching_content(self):
        self.row['local_path_if_any'] = str(self.original)
        with self.assertRaisesRegex(ValueError, 'OUTSIDE_ADMITTED_ROOT'):
            manifest_file(self.row, 'public-synthetic', [self.root/'other'])


class OriginalKeyedReferenceFields(unittest.TestCase):
    def setUp(self):
        self.original = [{'key': 'a', 'specimen': 's1', 'assay': 'r1', 'unit': 'g/kg', 'value': 1.},
            {'key': 'b', 'specimen': 's2', 'assay': 'r2', 'unit': 'g/kg', 'value': 2.}]
        self.columns = ['specimen', 'assay', 'unit', 'value']

    def compare(self, canonical, original=None):
        return required_keyed_equivalence(self.original if original is None else original,
            canonical, key='key', columns=self.columns)

    def test_shuffled_original_keyed_xy_join(self):
        self.assertEqual(self.compare(list(reversed(self.original)))['status'], 'computed')

    def test_duplicate_source_key(self):
        with self.assertRaisesRegex(ValueError, 'DUPLICATE_ORIGINAL_KEY'):
            self.compare([self.original[0], self.original[0]])

    def test_wrong_specimen_attachment(self):
        changed = copy.deepcopy(self.original); changed[0]['specimen'] = 's2'
        with self.assertRaisesRegex(ValueError, 'VALUE_CONTRADICTION'):
            self.compare(changed)

    def test_wrong_assay_attachment(self):
        changed = copy.deepcopy(self.original); changed[0]['assay'] = 'r2'
        with self.assertRaisesRegex(ValueError, 'VALUE_CONTRADICTION'):
            self.compare(changed)

    def test_wrong_target_value(self):
        changed = copy.deepcopy(self.original); changed[0]['value'] = 2.
        with self.assertRaisesRegex(ValueError, 'VALUE_CONTRADICTION'):
            self.compare(changed)

    def test_target_unit_contradiction(self):
        changed = copy.deepcopy(self.original); changed[0]['unit'] = '%'
        with self.assertRaisesRegex(ValueError, 'VALUE_CONTRADICTION'):
            self.compare(changed)

    def test_both_missing_fields_are_not_equivalence(self):
        changed = copy.deepcopy(self.original)
        for row in changed: del row['assay']
        with self.assertRaisesRegex(ValueError, 'COMPLETE_EXPLICIT_ORIGINAL_FIELDS'):
            self.compare(changed, changed)

    def test_null_and_blank_required_fields(self):
        for missing in [None, '', '   ']:
            with self.subTest(missing=missing):
                changed = copy.deepcopy(self.original); changed[0]['assay'] = missing
                with self.assertRaisesRegex(ValueError, 'COMPLETE_EXPLICIT_ORIGINAL_FIELDS'):
                    self.compare(changed, changed)

    def test_nonfinite_reference_values(self):
        for missing in [float('nan'), float('inf'), -float('inf')]:
            with self.subTest(missing=missing):
                changed = copy.deepcopy(self.original); changed[0]['value'] = missing
                with self.assertRaisesRegex(ValueError, 'COMPLETE_EXPLICIT_ORIGINAL_FIELDS'):
                    self.compare(changed, changed)

    def test_incomplete_key_population(self):
        with self.assertRaisesRegex(ValueError, 'KEY_POPULATIONS_DIFFER'):
            self.compare(self.original[:1])

    def test_empty_correspondence_is_not_evidence(self):
        with self.assertRaisesRegex(ValueError, 'NONEMPTY_ORIGINAL'):
            self.compare([], [])

    def test_numeric_parity_does_not_establish_assay_independence(self):
        self.compare(self.original)
        result = admit({'analysis_authorized': True, 'complete_X_qualified': True,
            'original_keyed_XY_verified': True, 'target_meaning_units_verified': True,
            'development_scope_frozen_before_target_decode': True})
        self.assertEqual(result['tier'], 'XY_descriptive_qualified')
        self.assertIn('REFERENCE_ASSAY_OWNERSHIP_VERIFIED_REQUIRED', result['blockers'])

    def test_unknown_donor_batch_is_not_fixed_by_unique_observation_keys(self):
        result = admit({'analysis_authorized': True, 'complete_X_qualified': True})
        self.assertEqual(result['tier'], 'X_only_qualified')

    def test_technical_repetition_cannot_cross_partitions(self):
        rows = [{'observation_id': str(i), 'physical_id': 'same', 'reference_id': 'same',
            'assay_event_id': 'same', 'component_id': 'component', 'partition': p}
            for i, p in enumerate(['train', 'test'])]
        with self.assertRaisesRegex(ValueError, 'INDIVISIBLE'):
            dependency_map(rows)

    def test_shared_assay_remains_one_indivisible_component(self):
        rows = [{'observation_id': str(i), 'physical_id': 'specimen'+str(i), 'reference_id': 'same',
            'assay_event_id': 'same', 'component_id': 'component', 'partition': 'train'} for i in range(2)]
        self.assertEqual(len(dependency_map(rows)['rows']), 2)
        rows[1]['component_id'] = 'invented-independent-row'
        with self.assertRaisesRegex(ValueError, 'INDIVISIBLE'):
            dependency_map(rows)


if __name__ == '__main__':
    unittest.main()
