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

    def amend(self, **overrides):
        return self.controller.amend(**(self.arguments | overrides))

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
        self.amend(engineering_bytes=3000)
        self.assertEqual(len(list(decisions.glob('*.json'))), 2)
        self.assertEqual(old.read_bytes(), original)
        current = self.controller.current()
        self.assertEqual(current['previous_local_cap_bytes'], self.arguments['effective_bytes'])
        self.assertEqual(current['previous_decision'], old.relative_to(self.store.root.resolve()).as_posix())
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
        with self.assertRaisesRegex(ValueError, 'AMENDMENT_NOT_ADMISSIBLE'):
            self.amend()

    def test_amendment_preserves_initial_baseline_and_charged_growth(self):
        # A total allowance grows from 2 GiB to 4 GB; prior growth stays charged.
        initial = 18_663_326_977
        self.raw['combined_bytes'] = initial
        self.write_raw()
        self.arguments.update(effective_bytes=25_000_000_000, engineering_bytes=2_147_483_648)
        self.activate()
        baseline_policy = self.controller.current()
        self.raw['combined_bytes'] = initial + 1_500_000_000
        self.raw.update(reserved_campaign_bytes=800, remaining_reservations_bytes=3200, journal_sha256='c' * 64)
        self.write_raw()
        unchanged_source = self.source.read_bytes()
        result = self.amend(engineering_bytes=4_000_000_000, owner_request_sha256='d' * 64, decision_date='2026-11-18')
        self.assertEqual(result['engineering_baseline_bytes'], initial)
        self.assertEqual(result['engineering_used_bytes'], 1_500_000_000)
        self.assertEqual(result['engineering_remaining_bytes'], 2_500_000_000)
        self.assertEqual(result['scientific_reserved_bytes'], 800)
        self.assertEqual(result['scientific_remaining_bytes'], 3200)
        self.assertEqual(result['journal_sha256'], 'c' * 64)
        self.assertEqual(result['new_scientific_reservations'], 0)
        self.assertEqual(self.source.read_bytes(), unchanged_source)
        amended = self.controller.current()
        for key in ('baseline_combined_bytes', 'baseline_measurement', 'science_journal_sha256'):
            self.assertEqual(amended[key], baseline_policy[key])
        self.assertEqual(amended['previous_policy_sha256'], fingerprint(baseline_policy))
        # Additional amendments still refer to the original baseline.
        self.amend(engineering_bytes=4_000_000_000)
        self.assertEqual(self.controller.snapshot()['engineering_used_bytes'], 1_500_000_000)
        with self.assertRaises(TypeError):
            self.amend(engineering_bytes=4_000_000_000, baseline_combined_bytes=0)

    def test_activate_cannot_reset_existing_or_orphaned_history(self):
        self.activate()
        pointer = self.controller.root / 'current.json'
        before = pointer.read_bytes()
        self.raw['combined_bytes'] = 2000
        self.write_raw()
        with self.assertRaisesRegex(ValueError, '^OWNER_POLICY_ALREADY_ACTIVE_USE_AMEND$'):
            self.activate()
        self.assertEqual(pointer.read_bytes(), before)
        pointer.unlink()  # Synthetic interrupted/current-pointer loss cannot rebaseline.
        with self.assertRaisesRegex(ValueError, '^OWNER_POLICY_ALREADY_ACTIVE_USE_AMEND$'):
            self.activate()

    def test_amendment_scope_actual_caps_and_reserves_fail_without_publication(self):
        self.activate()
        pointer = self.controller.root / 'current.json'
        before = pointer.read_bytes()
        for field, invalid in [('authorized_max_bytes', MAX_ALLOWED + 1),
                               ('reserve_free_bytes', MIN_RESERVE - 1), ('recipe_sha256', 'c' * 64)]:
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, '^OWNER_POLICY_AMENDMENT_SCOPE_INVALID$'):
                self.amend(**{field: invalid})
        self.raw['combined_bytes'] = 4000
        self.write_raw()
        with self.assertRaisesRegex(ValueError, '^OWNER_POLICY_AMENDMENT_NOT_ADMISSIBLE$'):
            self.amend(engineering_bytes=2500)
        self.raw['combined_bytes'] = 10001
        self.write_raw()
        with self.assertRaisesRegex(ValueError, '^OWNER_POLICY_AMENDMENT_NOT_ADMISSIBLE$'):
            self.amend(engineering_bytes=9000)
        self.raw['combined_bytes'] = 2000
        self.raw['free_volume_bytes']['private-volume-a'] = MIN_RESERVE - 1
        self.write_raw()
        with self.assertRaisesRegex(ValueError, '^OWNER_POLICY_AMENDMENT_NOT_ADMISSIBLE$'):
            self.amend(engineering_bytes=3000)
        self.assertEqual(pointer.read_bytes(), before)
        self.assertEqual(len(list((self.controller.root / 'decisions').glob('*.json'))), 1)

    def test_effective_cap_amendment_preserves_cumulative_accounting_and_before_receipt(self):
        initial = 18_663_326_977
        self.raw.update(combined_bytes=initial, campaign_ceiling_bytes=2_023_410_176,
                        reserved_campaign_bytes=2_015_788_498, remaining_reservations_bytes=7_621_678)
        self.write_raw()
        self.arguments.update(effective_bytes=25_000_000_000, engineering_bytes=4_000_000_000)
        self.activate()
        previous = self.controller.current()
        self.raw['combined_bytes'] = 22_038_391_285
        self.write_raw()
        unchanged_source = self.source.read_bytes()
        result = self.amend(effective_bytes=30_000_000_000, engineering_bytes=8_000_000_000)
        current = self.controller.current()
        self.assertEqual(result['effective_bytes'], 30_000_000_000)
        self.assertEqual(result['engineering_allowance_bytes'], 8_000_000_000)
        self.assertEqual(result['engineering_baseline_bytes'], initial)
        self.assertEqual(result['engineering_used_bytes'], 3_375_064_308)
        self.assertEqual(result['engineering_remaining_bytes'], 4_624_935_692)
        before = result['before_amendment']
        self.assertEqual(before['effective_bytes'], 25_000_000_000)
        self.assertEqual(before['engineering_allowance_bytes'], 4_000_000_000)
        self.assertEqual(before['engineering_used_bytes'], result['engineering_used_bytes'])
        self.assertEqual(before['engineering_remaining_bytes'], 624_935_692)
        self.assertEqual(before['measured_at'], result['measured_at'])
        self.assertEqual(before['owner_policy_sha256'], fingerprint(previous))
        self.assertEqual(result['owner_policy_sha256'], fingerprint(current))
        self.assertEqual(current['previous_local_cap_bytes'], 25_000_000_000)
        self.assertEqual(current['previous_policy_sha256'], fingerprint(previous))
        for key in ('scientific_ceiling_bytes', 'scientific_reserved_bytes', 'scientific_remaining_bytes', 'journal_sha256'):
            self.assertEqual(before[key], result[key])
        self.assertEqual(self.source.read_bytes(), unchanged_source)
        self.assertEqual(len(list((self.controller.root / 'decisions').glob('*.json'))), 2)
        # The full chain must remain valid after another same-cap amendment.
        self.amend(effective_bytes=30_000_000_000, engineering_bytes=8_000_000_000)
        self.assertEqual(self.controller.current()['baseline_combined_bytes'], initial)

    def test_effective_cap_amendment_rejects_invalid_bounds_without_publication(self):
        self.activate()
        pointer = self.controller.root / 'current.json'
        before = pointer.read_bytes()
        for cap in (MAX_ALLOWED + 1, 999, 2999):
            with self.subTest(cap=cap), self.assertRaisesRegex(ValueError, '^OWNER_POLICY_LIMIT_EXCEEDED$'):
                self.amend(effective_bytes=cap)
        self.assertEqual(pointer.read_bytes(), before)
        self.assertEqual(len(list((self.controller.root / 'decisions').glob('*.json'))), 1)

    def test_effective_cap_amendment_still_requires_fresh_physical_margin(self):
        self.activate()
        self.raw['free_volume_bytes']['private-volume-a'] = MIN_RESERVE - 1
        self.write_raw()
        pointer = self.controller.root / 'current.json'
        before = pointer.read_bytes()
        with self.assertRaisesRegex(ValueError, '^OWNER_POLICY_AMENDMENT_NOT_ADMISSIBLE$'):
            self.amend(effective_bytes=12000, engineering_bytes=4000)
        self.assertEqual(pointer.read_bytes(), before)

    def test_effective_cap_predecessor_reference_is_authenticated(self):
        self.activate()
        self.amend(effective_bytes=12000, engineering_bytes=4000)
        pointer = self.controller._read('domains-owner-storage/current.json')
        path = self.store.root / pointer['decision']
        envelope = json.loads(path.read_text())
        envelope['value']['previous_local_cap_bytes'] = 12000
        envelope['authentication'] = self.store.authenticate(envelope['value'])
        path.write_text(json.dumps(envelope))
        with self.assertRaisesRegex(ValueError, '^OWNER_POLICY_AMENDMENT_CHAIN_INVALID$'):
            self.controller.current()

    def test_amendment_authenticates_prior_history(self):
        self.activate()
        self.amend(engineering_bytes=3000)
        previous = self.controller.current()['previous_decision']
        old = self.store.root / previous
        body = json.loads(old.read_text())
        body['value']['baseline_combined_bytes'] = 0
        old.write_text(json.dumps(body))
        with self.assertRaisesRegex(ValueError, 'OWNER_POLICY'):
            self.amend(engineering_bytes=4000)

    def test_authenticated_amendment_cannot_change_baseline_or_prior_digest(self):
        self.activate()
        self.amend(engineering_bytes=3000)
        pointer = self.controller._read('domains-owner-storage/current.json')
        path = self.store.root / pointer['decision']
        original = path.read_bytes()
        for field, invalid in [('baseline_combined_bytes', 0), ('previous_policy_sha256', 'c' * 64)]:
            envelope = json.loads(original)
            envelope['value'][field] = invalid
            envelope['authentication'] = self.store.authenticate(envelope['value'])
            path.write_text(json.dumps(envelope))
            with self.assertRaisesRegex(ValueError, '^OWNER_POLICY_AMENDMENT_CHAIN_INVALID$'):
                self.controller.current()
        path.write_bytes(original)

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
