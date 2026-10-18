"""Reuse protected evidence and the original cumulative journal; fixed diagnostics."""
import json
from pathlib import Path
import shutil

from nirs4all_domains.privacy import PrivateStore, protect_directory
from nirs4all_domains.storage import StageStore, atomic_json, digest, fingerprint, tree_bytes


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


class Context:
    def __init__(self):
        self.cfg = read('.audit/alpha16/private-root.json')
        self.store = PrivateStore(self.cfg['root'], Path.cwd())
        self.root = protect_directory(self.store.root/'alpha17', Path.cwd())
        self.policy = read('configs/bank/storage-policy-alpha16.json')
        self.approval = {'owner_approved': True, 'owner_statement': 'Valider ce plan hors pilote',
            'decision_date': '2026-10-18', 'baseline_combined_bytes': 15871325243,
            'additional_combined_bytes': 335544320, 'previous_campaign_reserved': 771096018,
            'new_reservation_envelope': 8388608, 'transcript_input_bytes': 67108864,
            'real_fitting_authorized': False, 'new_X_campaign_authorized': False,
            'new_original_evidence_received': False,
            'amendment': 'Existing-bank scientific synthesis and exploratory admission; no repeated source closure. Ordinary aggregates follow source permissions, not catalog tier.'}
        path = self.root/'owner-resource-approval.json'
        if path.exists():
            assert self.load(path.name) == self.approval
        else:
            self.save(path.name, self.approval)
        freeze = self.auth(self.store.root/'execution-freeze.json', 'freeze')
        old = self.auth(self.store.root/'alpha15/closure-input-accounting.json')
        current = self.auth(self.store.root/'alpha16/participating-inputs.json')
        self.files = sorted({s['matrix'] for s in freeze['sources']} |
            {p for s in freeze['sources'] for p in s.get('other_participating_files', [])} |
            {p['path'] for p in old['original_and_canonical_inputs']} | set(current))
        self.scheduler = StageStore('results/alpha9-perten-keyed/state',
            protect_directory(self.root/'scratch', Path.cwd()),
            protect_directory(self.root/'stages', Path.cwd()), Path.cwd(), self.policy)
        if not (self.root/'historical-preservation.json').exists():
            self.save('historical-preservation.json', {
                'files': {str(p.relative_to(self.store.root)): digest(p) for p in self.store.root.rglob('*')
                    if p.is_file() and not p.is_relative_to(self.root)},
                'journal': read(self.scheduler.root/'journal.json')})

    def auth(self, path, key='value'):
        e = read(path)
        assert e['authentication'] == self.store.authenticate(e[key]), 'HISTORICAL_AUTHENTICATION_FAILED'
        return e[key]

    def save(self, name, value):
        return atomic_json(self.root/name, {'value': value, 'authentication': self.store.authenticate(value)})

    def load(self, name):
        return self.auth(self.root/name)

    def phase(self, name):
        pointer = self.auth(self.store.root/'alpha15'/(name+'.json'))
        assert digest(pointer['artifact_path']) == pointer['artifact_sha256']
        return read(pointer['artifact_path'])

    def guard(self, extra=0, paths=()):
        transcripts = self.load('incident-inputs.json') if (self.root/'incident-inputs.json').exists() else []
        assert sum(Path(p).stat().st_size for p in transcripts) <= self.approval['transcript_input_bytes'], 'TRANSCRIPT_INPUT_CAP'
        candidates = self.load('candidate-inputs.json') if (self.root/'candidate-inputs.json').exists() else []
        assert sum(Path(p).stat().st_size for p in set(candidates)|set(paths)) <= 33554432, 'CANONICAL_KEY_PROJECTION_INPUT_CAP'
        used = tree_bytes([Path.cwd(), self.store.root, *self.files, *transcripts, *candidates, *paths])
        assert used+extra <= min(self.policy['workspace_max_bytes'],
            self.approval['baseline_combined_bytes']+self.approval['additional_combined_bytes']), 'ALPHA17_COMBINED_CAP'
        assert all(shutil.disk_usage(p).free >= extra+self.policy['reserve_free_bytes'] for p in ['C:/','D:/'])
        ledger = read(self.scheduler.root/'journal.json')
        assert 0 <= ledger['reserved_campaign_bytes']-self.approval['previous_campaign_reserved'] <= self.approval['new_reservation_envelope'], 'ALPHA17_RESERVATION_CAP'
        assert ledger['reserved_campaign_bytes'] <= self.policy['campaign_bytes']
        return {'combined_bytes': used, 'campaign_reserved_bytes': ledger['reserved_campaign_bytes']}

    def run(self, name, callback):
        pointer = self.root/(name+'.json')
        if pointer.exists():
            value = self.load(pointer.name)
            assert digest(value['artifact_path']) == value['artifact_sha256']
            return read(value['artifact_path'])
        self.guard(4194304)
        ledger = read(self.scheduler.root/'journal.json')
        assert ledger['reserved_campaign_bytes']+4194304 <= self.approval['previous_campaign_reserved']+8388608
        contract = {'task': {'task_id': self.store.authenticate(['alpha17', name])},
                    'protocol': 'domains.alpha17.existing_evidence.v0.1', 'visibility': 'local_private'}
        plan = {'inputs': [], 'scratch_bytes': 2097152, 'evidence_bytes': 2097152,
                'expected_fits': 0, 'expected_permutations': 0,
                'uncertainty': 'Existing compact profiles and incident metadata only; no numerical target or new spectral fit.'}
        def bounded(folder):
            try:
                value = callback(folder)
                self.guard()
                return value
            except Exception as error:
                self.save(name+'-failure.json', {'type': type(error).__name__, 'detail': str(error)})
                raise ValueError('ALPHA17_PROTECTED_STAGE_FAILED') from None
        receipt, value = self.scheduler.run(contract, 'P4', plan, bounded)
        if value is None:
            raise ValueError('ALPHA17_STAGE_UNAVAILABLE')
        artifact = self.scheduler.evidence/receipt['artifact']
        self.save(pointer.name, {'artifact_path': str(artifact), 'artifact_sha256': digest(artifact), 'receipt': receipt})
        self.guard()
        return value

    def preservation(self):
        baseline = self.load('historical-preservation.json')
        assert all(digest(self.store.root/p) == sha for p,sha in baseline['files'].items()), 'HISTORICAL_PRIVATE_BYTES_CHANGED'
        ledger = read(self.scheduler.root/'journal.json')
        assert all(ledger['runs'][k] == v for k,v in baseline['journal']['runs'].items()), 'HISTORICAL_RUN_CHANGED'
        assert all(ledger['task_reserved_bytes'][k] >= v for k,v in baseline['journal']['task_reserved_bytes'].items())
        return self.guard()
