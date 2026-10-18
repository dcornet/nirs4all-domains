import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from nirs4all_domains.exploratory import admit
from nirs4all_domains.confrontation import admit as strict_admit


class ExploratoryAdmission(unittest.TestCase):
    def evidence(self):
        return {**{k: True for k in ['analysis_authorized', 'complete_X_qualified',
            'canonical_keyed_XY_verified', 'canonical_quantitative_target_declared',
            'development_scope_frozen_before_target_decode', 'retained_targets_sealed']},
            'target_unit_status': 'unspecified_canonical_units',
            **{k: 'a'*64 for k in ['canonical_X_sha256', 'canonical_Y_sha256', 'mapping_evidence_sha256']}}

    def test_unknown_physical_ownership_allows_only_exploratory_cv(self):
        e = self.evidence(); result = admit(e)
        self.assertEqual(result['evaluation_scope'], 'observation_CV_potentially_optimistic')
        self.assertFalse(result['independent_generalization'])
        self.assertFalse(result['real_fitting_authorized'])
        self.assertEqual(strict_admit(e)['tier'], 'X_only_qualified')

    def test_unverified_mapping_and_retained_scope_never_pass(self):
        for key in ['canonical_keyed_XY_verified', 'retained_targets_sealed',
                    'development_scope_frozen_before_target_decode', 'canonical_quantitative_target_declared']:
            with self.subTest(field=key):
                e = self.evidence(); e[key] = False
                self.assertEqual(admit(e)['tier'], 'X_only_observation_description')
        e = self.evidence(); e['mapping_evidence_sha256'] = 'partial'
        self.assertEqual(admit(e)['tier'], 'X_only_observation_description')
        e['mapping_evidence_sha256'] = 1
        self.assertEqual(admit(e)['tier'], 'X_only_observation_description')

    def test_known_groups_cannot_be_discarded(self):
        e = self.evidence(); e['known_dependencies_exist'] = True
        self.assertEqual(admit(e)['evaluation_scope'], 'observation_CV_potentially_optimistic')
        self.assertTrue(admit(e)['unresolved_dependency_risk'])
        e['verified_dependency_links_present'] = True
        self.assertEqual(admit(e)['tier'], 'exploratory_XY')
        e['known_links_preserved'] = True
        e['complete_verified_groups'] = True
        self.assertEqual(admit(e)['evaluation_scope'], 'verified_group_CV')
        self.assertFalse(admit(e)['independent_generalization'])

    def test_truthy_flags_and_outcomes_are_rejected(self):
        for val in [1, 'true', None]:
            e = self.evidence(); e['canonical_keyed_XY_verified'] = val
            self.assertEqual(admit(e)['tier'], 'X_only_observation_description')
        e = self.evidence(); e['rmse'] = .1
        with self.assertRaises(ValueError): admit(e)


class SafeInspection(unittest.TestCase):
    def test_documented_split_is_sealed_even_when_io_does_not_auto_apply_it(self):
        sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
        try:
            from prepare_alpha17_pilot import development_scope
        finally:
            sys.path.pop(0)
        rows=[{'observation_id':'development','sample_id':'s1','split_original':'calibration'},
              {'observation_id':'held','sample_id':'s2','split_original':'test'}]
        for applied in [False,True]:
            dev,retained,_=development_scope(rows,{'splits':[{'name':'original','applied':applied}]})
            self.assertEqual([r['observation_id'] for r in dev],['development'])
            self.assertEqual(retained,['held'])
        for broken in [[{**r,'split_original':''} for r in rows],
                       [{**rows[0],'partition':'test'},rows[1]],
                       [rows[0],{**rows[1],'sample_id':'s1'}]]:
            with self.assertRaises(ValueError):
                development_scope(broken,{'splits':[{'name':'original','applied':False}]})

    def test_shell_boundary_never_echoes_paths_or_exception_details(self):
        command = Path(__file__).resolve().parents[2]/'scripts/inspect_private_roots.py'
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'synthetic-sensitive-location.json'
            data = {k: 'SYNTHETIC_SECRET_PATH_'+k for k in
                    ['root', 'report_root', 'previous_report_root', 'source_root']}
            data['visibility'] = 'local_private'
            for value, valid in [(data, True), ({**data, 'extra': 'CANARY'}, False), (None, False)]:
                path.write_text(json.dumps(value) if value else '{broken', encoding='utf-8')
                r = subprocess.run([sys.executable, str(command), str(path)], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0 if valid else 2)
                self.assertEqual(r.stdout, 'PRIVATE_ROOT_CONFIG_'+('VALID' if valid else 'UNAVAILABLE')+'\n')
                self.assertEqual(r.stderr, '')
            missing = subprocess.run([sys.executable, str(command), str(Path(folder)/'MISSING_CANARY')], capture_output=True, text=True)
            self.assertEqual(missing.returncode, 2)
            self.assertEqual(missing.stdout, 'PRIVATE_ROOT_CONFIG_UNAVAILABLE\n')
            self.assertEqual(missing.stderr, '')
