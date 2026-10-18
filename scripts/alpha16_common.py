"""Version-scoped protected evidence using the existing shared stage journal."""
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
        self.root = protect_directory(self.cfg['report_root'], Path.cwd())
        self.previous = Path(self.cfg['previous_report_root'])
        self.policy = read('configs/bank/storage-policy-alpha16.json')
        self.approval = read('.audit/alpha16/budget-approval.json')
        assert self.approval['owner_approved'] and not self.approval['real_supervised_pilot_authorized']
        assert self.approval['workspace_ceiling'] == self.policy['workspace_max_bytes']
        self.freeze = self.auth(self.store.root/'execution-freeze.json', 'freeze')
        self.audit = self.auth(self.store.root/'screening-rights-reviewed.json', 'audit')
        old = self.auth(self.previous/'closure-input-accounting.json')
        self.baseline_files = sorted({s['matrix'] for s in self.freeze['sources']} |
            {p for s in self.freeze['sources'] for p in s.get('other_participating_files', [])} |
            {p['path'] for p in old['original_and_canonical_inputs']})
        self.input_path = self.root/'participating-inputs.json'
        self.inputs = self.load(self.input_path.name) if self.input_path.exists() else {}
        self.scheduler = StageStore('results/alpha9-perten-keyed/state',
            protect_directory(self.root/'scratch', Path.cwd()),
            protect_directory(self.root/'stages', Path.cwd()), Path.cwd(), self.policy)

    def auth(self, path, key='value'):
        envelope = read(path)
        assert envelope['authentication'] == self.store.authenticate(envelope[key]), 'PRIVATE_AUTHENTICATION_FAILED'
        return envelope[key]

    def save(self, name, value):
        return atomic_json(self.root/name, {'value': value, 'authentication': self.store.authenticate(value)})

    def load(self, name):
        return self.auth(self.root/name)

    def prior(self, phase):
        pointer = self.auth(self.previous/(phase+'.json'))
        assert digest(pointer['artifact_path']) == pointer['artifact_sha256']
        return read(pointer['artifact_path'])

    def participate(self, paths):
        pending = dict(self.inputs)
        prospective = {str(Path(p).resolve()): Path(p).stat().st_size for p in paths}
        baseline = {str(Path(p).resolve()) for p in self.baseline_files}
        additional = sum(v['bytes'] for p, v in pending.items() if p not in baseline)
        additional += sum(size for p, size in prospective.items() if p not in baseline and p not in pending)
        assert additional <= self.approval['additional_original_bytes'], 'ADDITIONAL_ORIGINAL_INPUT_CAP'
        self.guard(paths=list(prospective))
        for item in paths:
            path = str(Path(item).resolve())
            entry = {'path': path, 'bytes': Path(path).stat().st_size, 'sha256': digest(path)}
            assert path not in pending or pending[path] == entry, 'PARTICIPATING_INPUT_CHANGED'
            pending[path] = entry
        self.save(self.input_path.name, pending)
        self.inputs = pending

    def guard(self, extra=0, paths=()):
        used = tree_bytes([Path.cwd(), self.store.root, *self.baseline_files, *self.inputs, *paths])
        assert used+extra <= self.policy['workspace_max_bytes'], 'ALPHA16_COMBINED_STORAGE_LIMIT'
        assert all(shutil.disk_usage(p).free >= extra+self.policy['reserve_free_bytes'] for p in ['C:/', 'D:/'])
        ledger = read(self.scheduler.root/'journal.json')
        delta = ledger['reserved_campaign_bytes']-self.approval['previous_campaign_reserved']
        assert 0 <= delta <= self.approval['new_reservation_envelope'], 'ALPHA16_CAMPAIGN_ENVELOPE'
        assert ledger['reserved_campaign_bytes'] <= self.policy['campaign_bytes']
        return {'combined_bytes': used, 'reserved_campaign_bytes': ledger['reserved_campaign_bytes'],
            'alpha16_reservations': delta}

    def run(self, phase, candidate, inputs, callback, reserve=2097152):
        saved = self.root/(phase+'.json')
        if saved.exists():
            pointer = self.load(saved.name)
            assert pointer['inputs'] == inputs, 'COMPLETED_STAGE_INPUT_CHANGED'
            assert digest(pointer['artifact_path']) == pointer['artifact_sha256']
            return read(pointer['artifact_path'])
        private = {'phase': phase, 'inputs': inputs, 'protocol': 'domains.alpha16.original_reference.v0.1'}
        task = self.store.authenticate(['alpha16-source-resolution', candidate])
        contract = {'task': {'task_id': task}, 'visibility': 'local_private',
            'private_contract_receipt': self.store.authenticate(private), 'protocol': private['protocol']}
        plan = {'inputs': [], 'scratch_bytes': reserve//2, 'evidence_bytes': reserve-reserve//2,
            'expected_fits': 0, 'expected_permutations': 0,
            'uncertainty': 'Bounded original-reference projection; no real supervised fit.'}
        self.guard(reserve)
        ledger = read(self.scheduler.root/'journal.json')
        old = ledger['runs'].get(fingerprint(contract)+':P4')
        if not (old and old['status'] == 'computed'):
            assert ledger['task_reserved_bytes'].get(task, 0)+reserve <= self.approval['candidate_cumulative_bytes'], 'ALPHA16_CANDIDATE_CUMULATIVE_CAP'
            assert ledger['reserved_campaign_bytes']-self.approval['previous_campaign_reserved']+reserve <= self.approval['new_reservation_envelope']
        def bounded(folder):
            try:
                value = callback(folder)
                self.guard()
                return value
            except Exception as exc:
                self.save(phase+'-failure.json', {'exception_type': type(exc).__name__, 'detail': str(exc)})
                raise ValueError('PROTECTED_ALPHA16_STAGE_FAILED') from None
        receipt, value = self.scheduler.run(contract, 'P4', plan, bounded)
        if value is None:
            raise ValueError('ALPHA16_STAGE_UNAVAILABLE')
        path = self.scheduler.evidence/receipt['artifact']
        self.save(saved.name, {'inputs': inputs, 'artifact_path': str(path),
            'artifact_sha256': digest(path), 'receipt': receipt})
        self.guard()
        return value
