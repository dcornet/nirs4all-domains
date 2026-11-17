"""Synthetic storage evidence only: no private config, datasets or science fits."""
import json
import contextlib
import io
from pathlib import Path
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nirs4all_domains.engineering_storage import EngineeringStorage, MAX_ALLOWED, MIN_RESERVE
from nirs4all_domains.privacy import PrivateStore
from nirs4all_domains.storage import digest, fingerprint


class EngineeringStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.workspace = root / 'workspace'
        self.workspace.mkdir()
        self.store = PrivateStore(root / 'private', self.workspace)
        self.source = self.workspace / 'numeric.json'
        self.raw = dict(combined_bytes=1000, workspace_ceiling_bytes=5000,
                        campaign_ceiling_bytes=4000, reserved_campaign_bytes=700,
                        remaining_reservations_bytes=3300, journal_sha256='a' * 64,
                        free_volume_bytes={'private-volume-a': MIN_RESERVE + 10000,
                                           'private-volume-b': MIN_RESERVE + 20000},
                        new_reservations=0, ceiling_increase=0)
        self.write_raw()
        self.recipe = self.workspace / 'recipe.py'
        self.recipe.write_text("import pathlib,sys\np=pathlib.Path(sys.argv[1])\np.write_bytes(pathlib.Path('numeric.json').read_bytes())\n", encoding='utf-8')
        self.controller = EngineeringStorage(self.store, self.workspace, self.recipe)
        self.arguments = dict(effective_bytes=10000, engineering_bytes=2000,
                              authorized_max_bytes=MAX_ALLOWED, reserve_free_bytes=MIN_RESERVE,
                              owner_request_sha256='b' * 64, decision_date='2026-11-17', recipe_sha256=digest(self.recipe))

    def write_raw(self):
        self.source.write_text(json.dumps(self.raw), encoding='utf-8')

    def activate(self, **overrides):
        return self.controller.activate(**(self.arguments | overrides))

    def test_growth_and_science_preservation(self):
        baseline = self.source.read_bytes()
        result = self.activate()
        self.assertEqual(result['owner_policy_sha256'], fingerprint(self.controller.current()))
        self.assertEqual(result['scientific_reserved_bytes'], 700)
        self.assertEqual(result['scientific_remaining_bytes'], 3300)
        self.assertEqual(result['journal_sha256'], 'a' * 64)
        self.assertEqual(self.source.read_bytes(), baseline)
        self.raw['combined_bytes'] = 2500
        self.write_raw()
        self.assertEqual(self.controller.snapshot(500)['status'], 'ready')
        result = self.controller.snapshot(501)
        self.assertEqual(result['reasons'], ['ENGINEERING_ALLOWANCE_EXCEEDED'])
        self.assertEqual(result['engineering_used_bytes'], 1500)
        self.assertNotIn('private-volume', json.dumps(result))
        self.assertEqual(result['new_scientific_reservations'], 0)

    def test_authentication_and_immutable_amendment_history(self):
        self.activate()
        self.assertEqual(self.controller.current()['previous_local_cap_bytes'], 5000)
        decisions = self.controller.root / 'decisions'
        old = next(decisions.glob('*.json'))
        original = old.read_bytes()
        self.activate(engineering_bytes=3000)
        self.assertEqual(len(list(decisions.glob('*.json'))), 2)
        self.assertEqual(old.read_bytes(), original)
        current = self.controller.current()
        self.assertEqual(current['previous_local_cap_bytes'], self.arguments['effective_bytes'])
        self.assertEqual(current['previous_decision'], old.relative_to(self.store.root).as_posix())
        with self.assertRaisesRegex(ValueError, '^OWNER_POLICY_DECISION_IMMUTABLE$'):
            self.controller._write(current['previous_decision'], current)
        self.assertEqual(old.read_bytes(), original)
        pointer = self.controller.root / 'current.json'
        body = json.loads(pointer.read_text())
        body['value']['decision'] = '../escape.json'
        pointer.write_text(json.dumps(body))
        with self.assertRaisesRegex(ValueError, 'OWNER_POLICY'):
            self.controller.current()

    def test_authenticated_unsafe_pointer_and_policy_tamper(self):
        self.activate()
        pointer = self.controller.root / 'current.json'
        original = pointer.read_bytes()
        self.controller._write('domains-owner-storage/current.json', {'protocol': 'domains.engineering_storage.v1', 'decision': '../escape.json'})
        with self.assertRaisesRegex(ValueError, 'POINTER_INVALID'):
            self.controller.current()
        pointer.write_bytes(original)
        path = next((self.controller.root / 'decisions').glob('*.json'))
        body = json.loads(path.read_text())
        body['value']['effective_bytes'] += 1
        path.write_text(json.dumps(body))
        with self.assertRaisesRegex(ValueError, 'OWNER_POLICY'):
            self.controller.current()

    def test_owner_max_and_effective_cap(self):
        with self.assertRaisesRegex(ValueError, 'LIMIT_EXCEEDED'):
            self.activate(authorized_max_bytes=MAX_ALLOWED + 1)
        self.activate(effective_bytes=3000)
        self.raw['combined_bytes'] = 3001
        self.write_raw()
        self.assertIn('EFFECTIVE_LOCAL_CAP_EXCEEDED', self.controller.snapshot()['reasons'])

    def test_low_physical_reserve_each_volume(self):
        self.activate()
        self.raw['free_volume_bytes']['private-volume-a'] = MIN_RESERVE + 4
        self.write_raw()
        self.assertIn('INSUFFICIENT_PHYSICAL_RESERVE', self.controller.snapshot(5)['reasons'])
        self.raw['free_volume_bytes']['private-volume-a'] = MIN_RESERVE - 1
        self.write_raw()
        with self.assertRaisesRegex(ValueError, 'PHYSICAL_RESERVE'):
            self.activate()

    def test_stale_invalid_and_recipe_pin(self):
        self.activate()
        measurement = self.controller.measure(self.arguments['recipe_sha256'])
        measurement['measured_at'] = time.time() - 301
        with self.assertRaisesRegex(ValueError, 'INVALID_OR_STALE'):
            self.controller._snapshot(self.controller.current(), measurement, 0)
        for field, invalid in [('combined_bytes', True), ('reserved_campaign_bytes', -1),
                               ('new_reservations', 1), ('ceiling_increase', 1), ('remaining_reservations_bytes', 7)]:
            before = self.raw[field]
            self.raw[field] = invalid
            self.write_raw()
            with self.assertRaisesRegex(ValueError, 'INVALID_OR_STALE'):
                self.controller.snapshot()
            self.raw[field] = before
        self.recipe.write_text('raise Exception("private path")', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, '^MEASUREMENT_RECIPE_DIGEST_MISMATCH$'):
            self.controller.snapshot()

    def test_receipt_tamper_and_failed_recipe_redaction(self):
        self.activate()
        measurement = self.controller.measure(self.arguments['recipe_sha256'])
        (self.store.root / measurement['receipt']).write_text('{}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, '^MEASUREMENT_INVALID_OR_STALE$'):
            self.controller._snapshot(self.controller.current(), measurement, 0)
        self.recipe.write_text('raise Exception("sensitive locator")', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, '^MEASUREMENT_FAILED$'):
            self.controller.measure(digest(self.recipe))

    def test_in_memory_measurement_tamper(self):
        self.activate()
        measurement = self.controller.measure(self.arguments['recipe_sha256'])
        measurement['value']['combined_bytes'] = 0
        with self.assertRaisesRegex(ValueError, '^MEASUREMENT_INVALID_OR_STALE$'):
            self.controller._snapshot(self.controller.current(), measurement, 0)

    def test_private_root_helper_does_not_print_values(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'scripts'))
        from inspect_private_roots import load_private_roots, main
        config = self.workspace / 'synthetic-config.json'
        value = dict(root='private root', report_root='private report', previous_report_root='old report',
                     source_root='private source', visibility='local_private')
        config.write_text(json.dumps(value), encoding='utf-8')
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(load_private_roots(config), value)
            self.assertEqual(main([str(config)]), 0)
            self.assertEqual(main([str(config), 'extra']), 2)
        self.assertEqual(output.getvalue(), 'PRIVATE_ROOT_CONFIG_VALID\nPRIVATE_ROOT_CONFIG_UNAVAILABLE\n')


if __name__ == '__main__':
    unittest.main()
