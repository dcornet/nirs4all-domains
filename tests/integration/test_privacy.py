"""Deliberately sensitive SYNTHETIC records; no real private source/secret."""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from nirs4all_domains.privacy import (PROTOCOL, PrivacyError, PrivateStore,
    ScopedIdentities, acquire_private, authorize, characterize_private, opaque_id,
    protect_directory)
from nirs4all_domains.disclosure import (PROTOCOL as DISCLOSURE, DisclosureBoundary,
    candidate, scan_bytes, suppress_partition, validate_outgoing, validate_public)
from nirs4all_domains.storage import digest, encoded, fingerprint

SENSITIVE = 'SYNTHETIC-confidential-specimen-9386'
SECRET_PATH = r'D:\synthetic-owner-only\private-source.csv'


def admission():
    return {'protocol': PROTOCOL, 'visibility': 'local_private', 'receipt_id': opaque_id(),
        'permissions': {k: {'status': 'allowed' if k in ('access', 'analysis') else 'unknown',
                           'evidence_receipt': opaque_id() if k in ('access', 'analysis') else None}
                       for k in ('access', 'analysis', 'publish_aggregates', 'redistribute_raw')},
        'sensitive_handling': {'status': 'allowed', 'evidence_receipt': opaque_id()},
        'participation_public': False, 'source_scope': 'SYNTHETIC-private-study'}


def publishable_admission():
    spec = admission()
    spec['permissions']['publish_aggregates'] = {'status': 'allowed', 'evidence_receipt': opaque_id()}
    spec['participation_public'] = True
    return spec


def indicator(value=.75):
    return {'indicator': 'pc1_fraction', 'statistic': 'median',
            'status': 'computed', 'reason': None, 'value': value}


def clearance(draft, receipt, prior=()):
    return {'decision': draft['decision'], 'candidate_sha256': fingerprint(draft),
        'reviewer_attestation': 'Synthetic explicit reviewer approval, not a real authorization.',
        'participation_approved': True, 'aggregate_fields_approved': True,
        'small_cell_and_linkage_reviewed': True, 'joint_prior_exports': list(prior),
        'source_receipts': [receipt]}


class PrivacyAdmissionControls(unittest.TestCase):
    def test_unknown_access_refuses_before_acquisition(self):
        spec = admission(); spec['permissions']['access']['status'] = 'unknown'; provider = Mock()
        with self.assertRaisesRegex(PrivacyError, 'NOT_AUTHORIZED'):
            acquire_private(spec, provider)
        provider.assert_not_called()

    def test_unknown_analysis_refuses_before_acquisition(self):
        spec = admission(); spec['permissions']['analysis']['status'] = 'requires_owner_approval'; provider = Mock()
        with self.assertRaises(PrivacyError): acquire_private(spec, provider)
        provider.assert_not_called()

    def test_denied_access_cannot_be_overridden_by_private_visibility(self):
        spec = admission(); spec['permissions']['access']['status'] = 'denied'
        with self.assertRaises(PrivacyError): authorize(spec)

    def test_analysis_allowed_without_redistribution(self):
        for state in ('denied', 'unknown'):
            spec = admission(); spec['permissions']['redistribute_raw']['status'] = state
            self.assertEqual(acquire_private(spec, lambda: 'authorized X'), 'authorized X')

    def test_allowed_requires_actual_evidence_receipt(self):
        spec = admission(); spec['permissions']['access']['evidence_receipt'] = None
        with self.assertRaisesRegex(PrivacyError, 'EVIDENCE_REQUIRED'): authorize(spec)

    def test_unknown_sensitive_handling_is_not_silently_not_applicable(self):
        spec = admission(); spec['sensitive_handling']['status'] = 'unknown'
        with self.assertRaisesRegex(PrivacyError, 'HANDLING_UNRESOLVED'): authorize(spec)

    def test_public_mode_cannot_override_publication_permission(self):
        spec = admission(); spec['visibility'] = 'public'
        with self.assertRaisesRegex(PrivacyError, 'PUBLIC_ADMISSION'): authorize(spec)

    def test_provider_failure_does_not_leak_name_path_or_chain(self):
        def bad(): raise ValueError(SENSITIVE + SECRET_PATH)
        try: acquire_private(admission(), bad)
        except PrivacyError as exc:
            self.assertEqual(str(exc), 'PRIVATE_SOURCE_READ_FAILED'); self.assertTrue(exc.__suppress_context__)
        else: self.fail('expected refusal')

    def test_unknown_permission_or_outcome_fields_fail_closed(self):
        for key in ('Y_test', 'model_performance', 'future_scores'):
            spec = admission(); spec[key] = [999]
            with self.assertRaises(PrivacyError): authorize(spec)


class PrivateEvidenceControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='domains-synthetic-privacy-')
        cls.store = PrivateStore(Path(cls.temp.name) / 'private', Path.cwd())

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def test_secret_mapping_and_files_are_outside_git(self):
        receipt = self.store.put(admission(), {'specimen': SENSITIVE})
        self.assertFalse(self.store.root.is_relative_to(Path.cwd()))
        self.assertNotIn(SENSITIVE, str(self.store.evidence / (receipt + '.json')))
        self.assertEqual(len((self.store.keys / 'scope.key').read_bytes()), 32)
        if os.name != 'nt': self.assertEqual(self.store.keys.stat().st_mode & 0o777, 0o700)

    def test_private_root_inside_workspace_is_refused(self):
        with self.assertRaisesRegex(PrivacyError, 'OUTSIDE_WORKSPACE'):
            protect_directory(Path.cwd() / '.audit/synthetic-forbidden', Path.cwd())

    def test_deterministic_scoped_pseudonym_and_retry(self):
        ids = ScopedIdentities(self.store)
        a = ids.identity('study-a', 'population-a', 'observation', SENSITIVE); ids.flush()
        self.assertEqual(ScopedIdentities(self.store).identity('study-a', 'population-a', 'observation', SENSITIVE), a)
        self.assertNotIn(SENSITIVE, a); self.assertNotIn(hashlib.sha256(SENSITIVE.encode()).hexdigest(), a)

    def test_unrelated_studies_and_kinds_do_not_join(self):
        ids = ScopedIdentities(self.store)
        a = ids.identity('study-a', 'pop', 'observation', '1')
        self.assertNotEqual(a, ids.identity('study-b', 'pop', 'observation', '1'))
        self.assertNotEqual(a, ids.identity('study-a', 'pop', 'physical', '1'))

    def test_collision_is_checked(self):
        ids = ScopedIdentities(self.store)
        with unittest.mock.patch.object(self.store, 'authenticate', return_value='0'*64):
            ids.identity('collision', 'pop', 'observation', 'one')
            with self.assertRaisesRegex(PrivacyError, 'COLLISION'):
                ids.identity('collision', 'pop', 'observation', 'two')

    def _view(self, view, relationship=None):
        return ScopedIdentities(self.store).map_view('study-pair', 'population', ['a', 'b', 'c'],
            {'a':'physical-1', 'b':'physical-1', 'c':'physical-2'},
            {'a':'train', 'b':'train', 'c':'test'}, view_scope=view, relationship=relationship)

    def test_verified_pairing_survives_views(self):
        proof = {'verified': True, 'evidence_receipt': opaque_id(), 'study':'study-pair', 'population':'population'}
        a, b = self._view('instrument-a', proof), self._view('instrument-b', proof)
        self.assertEqual(a, b)

    def test_unverified_views_cannot_join_by_coincident_rows(self):
        self.assertNotEqual(self._view('unverified-a')['observation_ids'], self._view('unverified-b')['observation_ids'])

    def test_false_pairing_proof_refused(self):
        with self.assertRaisesRegex(PrivacyError, 'PAIRING_NOT_VERIFIED'):
            self._view('bad', {'verified':False, 'evidence_receipt':opaque_id(), 'study':'study-pair', 'population':'population'})

    def test_components_and_exact_splits_survive(self):
        view = self._view('components'); a,b,c = view['observation_ids']
        self.assertEqual(view['components'][a], view['components'][b])
        self.assertNotEqual(view['components'][a], view['components'][c])
        self.assertEqual(view['split'], {a:'train', b:'train', c:'test'})
        self.assertEqual(view['identity_scope'], 'dependency_preserved_not_independence_certified')

    def test_no_public_artifact_from_successful_private_calculation(self):
        from scripts.generate_unsupervised_fixtures import scenario
        spectral = scenario('separated', n=48)['spectral']
        compute = Mock(return_value={'test_target_accessed': False, 'metric': .5})
        receipt = characterize_private(admission(), lambda: spectral, compute, self.store)
        self.assertEqual(self.store.get(receipt)['payload']['metric'], .5)
        self.assertFalse((self.store.root / 'public').exists())

    def test_actual_native_private_x_without_target_accessor(self):
        from scripts.generate_unsupervised_fixtures import scenario
        from nirs4all_domains.unsupervised import native_profile, query_design, compact_profile
        from n4m._ffi import library_path
        raw = scenario('gradient', n=48)['spectral']
        binary = Path(os.environ.get('N4DOMAINS_BIN', 'target/debug/n4domains' + ('.exe' if os.name == 'nt' else ''))).resolve()
        design = query_design(raw['observation_ids'], len(raw['axis']))
        def compute(x): return compact_profile(native_profile(x, 'raw', binary, Path(library_path()), design), design)
        receipt = characterize_private(admission(), lambda: raw, compute, self.store)
        self.assertFalse(self.store.get(receipt)['payload']['test_target_accessed'])
        self.assertEqual(self.store.get(receipt)['payload']['n_observations'], 48)

    def test_retained_target_payload_refused_before_numeric_call(self):
        from scripts.generate_unsupervised_fixtures import scenario
        raw = scenario('gradient', n=48)['spectral']; raw['Y_test'] = [999]*48; compute = Mock()
        with self.assertRaisesRegex(PrivacyError, 'X_ONLY_TRANSPORT'):
            characterize_private(admission(), lambda: raw, compute, self.store)
        compute.assert_not_called()

    def test_scores_and_spectra_are_not_compact_evidence(self):
        from scripts.generate_unsupervised_fixtures import scenario
        raw = scenario('gradient', n=48)['spectral']
        for field in ('spectra', 'transport_only_scores', 'Y_test', 'loadings'):
            with self.assertRaisesRegex(PrivacyError, 'COMPACT_EVIDENCE'):
                characterize_private(admission(), lambda:raw,
                    lambda _: {'test_target_accessed':False, 'nested':{field:[[123.45]]}}, self.store)

    def test_private_evidence_tampering_and_immutability(self):
        spec = admission(); receipt = self.store.put(spec, {'original':SENSITIVE})
        with self.assertRaisesRegex(PrivacyError, 'IMMUTABLE'): self.store.put(spec, {'changed':True}, receipt)
        path = self.store.evidence / (receipt+'.json'); value=json.loads(path.read_text()); value['payload']['original']='tampered'
        path.write_bytes(encoded(value))
        with self.assertRaisesRegex(PrivacyError, 'AUTHENTICATION'): self.store.get(receipt)


class PublicBoundaryControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='domains-synthetic-disclosure-')
        cls.store = PrivateStore(Path(cls.temp.name) / 'private', Path.cwd())

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def _record(self, public=True):
        return self.store.put(publishable_admission() if public else admission(), {'private_name':SENSITIVE})

    def test_export_requires_explicit_review_and_preserves_scientific_result(self):
        receipt=self._record(); path=self.store.evidence/(receipt+'.json'); before=digest(path)
        draft=candidate([indicator()]); destination=Path(self.temp.name)/(draft['receipt_id']+'.json')
        with self.assertRaisesRegex(PrivacyError, 'REVIEW_MISSING'): DisclosureBoundary(self.store).export(draft,destination)
        self.assertFalse(destination.exists()); self.assertEqual(digest(path),before)

    def test_nested_unknown_ids_spectra_scores_and_neighbors_are_rejected(self):
        for field in ('sample_id','spectra','PCA_scores','neighbors','path','source_sha256','Y','predictions'):
            draft=candidate([indicator()]); draft['indicators'][0][field]=SENSITIVE
            with self.assertRaisesRegex(PrivacyError, 'ALLOWLISTED'): validate_public(draft)

    def test_no_free_text_or_published_pseudonyms(self):
        for field,value in [('dataset_id', SENSITIVE),('source_id','p_'+'0'*64),('dimensions',[1,2]),('figure_metadata',{'X':[1,2]})]:
            draft=candidate(); draft[field]=value
            with self.assertRaises(PrivacyError): validate_public(draft)

    def test_metric_cannot_smuggle_array_nan_or_string(self):
        for value in ([1,2], SENSITIVE, float('nan'), float('inf'), True):
            with self.assertRaises(PrivacyError): candidate([indicator(value)])

    def test_status_reason_value_invariants(self):
        cell=indicator(); cell['status']='unavailable'
        with self.assertRaises(PrivacyError): candidate([cell])
        cell.update(value=None,reason='NUMERIC_UNAVAILABLE'); self.assertTrue(validate_public(candidate([cell])))

    def test_small_and_complementary_suppression(self):
        values=suppress_partition([2,10,20],5,total_released=True)
        self.assertEqual([c['suppressed'] for c in values],[True,True,False])
        self.assertEqual([c['value'] for c in values],[None,None,20])

    def test_single_cell_cannot_be_reconstructed_from_total(self):
        with self.assertRaisesRegex(PrivacyError, 'TOTAL_MUST_BE_SUPPRESSED'): suppress_partition([2,0],5,total_released=True)

    def test_minimum_is_policy_specific_not_one_anonymity_guarantee(self):
        self.assertFalse(suppress_partition([7,20],5)[0]['suppressed'])
        self.assertTrue(suppress_partition([7,20],10)[0]['suppressed'])
        self.assertIn('NOT_ANONYMITY_GUARANTEE',candidate()['limitations'])

    def test_rights_cannot_be_invented_by_reviewer(self):
        receipt=self._record(False); draft=candidate()
        with self.assertRaisesRegex(PrivacyError, 'PUBLICATION_NOT_ALLOWED'):
            DisclosureBoundary(self.store).review(draft,[receipt],clearance(draft,receipt))

    def test_confidential_participation_blocks_even_allowed_metrics(self):
        spec=publishable_admission(); spec['participation_public']=False
        receipt=self.store.put(spec,{}); draft=candidate()
        with self.assertRaisesRegex(PrivacyError,'PARTICIPATION_NOT_ALLOWED'):
            DisclosureBoundary(self.store).review(draft,[receipt],clearance(draft,receipt))

    def test_local_only_decision_has_no_public_file(self):
        receipt=self._record(); draft=candidate(); review=clearance(draft,receipt); review['decision']='local_only'
        self.assertEqual(DisclosureBoundary(self.store).review(draft,[receipt],review)['decision'],'local_only')

    def test_changed_candidate_invalidates_exact_approval(self):
        receipt=self._record(); draft=candidate([indicator()]); boundary=DisclosureBoundary(self.store)
        prior=[v['export_sha256'] for v in boundary._ledger()]
        boundary.review(draft,[receipt],clearance(draft,receipt,prior)); draft['indicators'][0]['value']=.6
        with self.assertRaisesRegex(PrivacyError, 'AUTHENTICATION'):
            boundary.export(draft,Path(self.temp.name)/(draft['receipt_id']+'.json'))

    def test_approved_export_then_cross_table_release_requires_joint_review(self):
        receipt=self._record(); boundary=DisclosureBoundary(self.store); draft=candidate([indicator()])
        prior=[v['export_sha256'] for v in boundary._ledger()]
        boundary.review(draft,[receipt],clearance(draft,receipt,prior))
        target=Path(self.temp.name)/(draft['receipt_id']+'.json'); boundary.export(draft,target)
        self.assertNotIn(SENSITIVE.encode(),target.read_bytes()); self.assertTrue(validate_public(json.loads(target.read_bytes())))
        second=candidate([indicator(.4)])
        with self.assertRaisesRegex(PrivacyError,'JOINT_RELEASE'):
            boundary.review(second,[receipt],clearance(second,receipt))
        boundary.export(draft,target)  # exact retry is permitted

    def test_review_attestation_and_truthy_flags_cannot_be_implicit(self):
        for field,value in [('reviewer_attestation',''),('participation_approved','true'),('small_cell_and_linkage_reviewed',1)]:
            receipt=self._record(); draft=candidate(); proof=clearance(draft,receipt); proof[field]=value
            with self.assertRaisesRegex(PrivacyError, 'EXPLICIT_REVIEW'):
                DisclosureBoundary(self.store).review(draft,[receipt],proof)

    def test_secret_unkeyed_fingerprint_or_path_in_any_surface_refused(self):
        secret=(self.store.keys/'scope.key').read_bytes(); sha=hashlib.sha256(b'synthetic private X').hexdigest()
        for surface in ('report.json','log.txt','figure.svg','figure.png','METADATA','trace.md','ci-fixture.csv','model.bin'):
            for value in (secret,SENSITIVE.encode(),sha.encode(),SECRET_PATH.encode()):
                with self.assertRaisesRegex(PrivacyError,'PRIVATE_CONTENT'):
                    scan_bytes(b'prefix:'+value,sensitive_literals=[secret,SENSITIVE,sha,SECRET_PATH])

    def test_encoded_secret_is_also_rejected(self):
        import base64
        secret=(self.store.keys/'scope.key').read_bytes()
        for encoded_secret in [secret.hex().encode(),base64.b64encode(secret)]:
            with self.assertRaisesRegex(PrivacyError,'PRIVATE_CONTENT'):
                scan_bytes(encoded_secret,sensitive_literals=[secret])

    def test_staged_filename_taint_detected(self):
        with self.assertRaisesRegex(PrivacyError,'PRIVATE_CONTENT'):
            validate_outgoing(SENSITIVE+'.csv',b'harmless',provenance={},sensitive_literals=[SENSITIVE])

    def test_claimed_public_label_does_not_launder_private_bytes(self):
        data=b'pretend public data'; sha=hashlib.sha256(data).hexdigest()
        with self.assertRaisesRegex(PrivacyError,'NOT_AUTHORIZED'):
            validate_outgoing('report.json',data,provenance={'visibility':'public','sha256':sha,'kind':'public_source'})

    def test_private_provenance_rejected_in_packages_fixtures_and_logs(self):
        data=b'123'; sha=hashlib.sha256(data).hexdigest()
        for path in ('wheel/module.py','sdist/fixture.json','ci/input.json','stdout.log'):
            with self.assertRaisesRegex(PrivacyError,'PUBLIC_PROVENANCE'):
                validate_outgoing(path,data,provenance={'visibility':'local_private','sha256':sha,'kind':'public_source'},authorized_public_hashes={'public_source':{sha}})

    def test_disguised_export_rejects_unknown_fields_despite_hash_roster(self):
        draft=candidate(); draft['secret']=SENSITIVE; data=encoded(draft); sha=hashlib.sha256(data).hexdigest()
        with self.assertRaisesRegex(PrivacyError,'EXPORT_SCHEMA'):
            validate_outgoing('export.json',data,provenance={'visibility':'public','sha256':sha,'kind':'sanitized_export'},authorized_public_hashes={'sanitized_export':{sha}})


if __name__ == '__main__': unittest.main()
