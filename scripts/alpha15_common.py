"""Local-only evidence context and existing serial journal adapter."""
import json
from pathlib import Path
import shutil
from nirs4all_domains.privacy import PrivateStore, protect_directory
from nirs4all_domains.storage import StageStore, atomic_json, digest, fingerprint, tree_bytes


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


class Context:
    def __init__(self):
        self.cfg = read('.audit/alpha15/private-root.json')
        self.store = PrivateStore(self.cfg['root'], Path.cwd())
        self.root = protect_directory(self.cfg['report_root'], Path.cwd())
        self.policy = read('configs/bank/storage-policy-alpha15.json')
        self.approval = read('.audit/alpha15/budget-approval.json')
        assert self.approval['owner_approved'] and not self.approval['real_supervised_pilot_authorized']
        assert self.approval['workspace_ceiling'] == self.policy['workspace_max_bytes']
        self.freeze = self.auth('execution-freeze.json', 'freeze')
        self.audit = self.auth('screening-rights-reviewed.json', 'audit')
        self.old_report = self.auth('confidential-release-report.json', 'report')
        self.files = sorted({s['matrix'] for s in self.freeze['sources']} |
            {p for s in self.freeze['sources'] for p in s.get('other_participating_files', [])})
        closure_inputs = self.root/'closure-input-accounting.json'
        if closure_inputs.exists():
            accounting = read(closure_inputs)
            assert accounting['authentication'] == self.store.authenticate(accounting['value'])
            self.files = sorted(set(self.files) | {p['path'] for p in accounting['value']['original_and_canonical_inputs']})
        self.scheduler = StageStore('results/alpha9-perten-keyed/state',
            protect_directory(self.root/'scratch', Path.cwd()),
            protect_directory(self.root/'stages', Path.cwd()), Path.cwd(), self.policy)

    def auth(self, path, key):
        envelope = read(self.store.root/path)
        assert envelope['authentication'] == self.store.authenticate(envelope[key])
        return envelope[key]

    def save(self, name, value):
        return atomic_json(self.root/name, {'value': value, 'authentication': self.store.authenticate(value)})

    def load(self, name):
        value = read(self.root/name)
        assert value['authentication'] == self.store.authenticate(value['value'])
        return value['value']

    def guard(self, extra=0):
        used = tree_bytes([Path.cwd(), self.store.root, *self.files])
        assert used+extra <= self.policy['workspace_max_bytes'], 'ALPHA15_COMBINED_STORAGE_LIMIT'
        assert all(shutil.disk_usage(p).free >= extra+self.policy['reserve_free_bytes'] for p in ['C:/', 'D:/'])
        ledger = read(self.scheduler.root/'journal.json')
        assert ledger['reserved_campaign_bytes'] <= self.policy['campaign_bytes']
        assert ledger['reserved_campaign_bytes']-self.approval['previous_campaign_reserved'] <= self.approval['new_reservation_envelope']
        return {'combined_bytes': used, 'reserved_campaign_bytes': ledger['reserved_campaign_bytes'],
            'alpha15_reservations': ledger['reserved_campaign_bytes']-self.approval['previous_campaign_reserved']}

    def record_closure_inputs(self):
        """Reproducible original-input accounting after the bounded inspection."""
        closure = read(self.load('source-closure-v2.json')['artifact_path'])
        paths = set()
        for record in closure['investigations']:
            paths.update(p['path'] for p in record['files']+record['original_file_inspections'])
            paths.update(str(Path(self.cfg['source_root'])/record['dataset_id']/name) for name in record['headers'])
        items = [{'path': p, 'bytes': Path(p).stat().st_size, 'sha256': digest(p)} for p in sorted(paths)]
        path = self.root/'closure-input-accounting.json'
        if path.exists():
            assert self.load(path.name)['original_and_canonical_inputs'] == items, 'CLOSURE_INPUT_CHANGED'
        else:
            self.save(path.name, {'visibility': 'local_private', 'original_and_canonical_inputs': items})
        self.files = sorted(set(self.files) | paths)
        self.guard()

    def run(self, phase, inputs, callback):
        # One frozen controller per completed work package. Resume verifies its
        # immutable evidence; editing a later reporting script cannot refit X.
        saved = self.root/(phase+'.json')
        if saved.exists():
            value = self.load(saved.name)
            assert value['inputs'] == inputs, 'ALPHA15_COMPLETED_STAGE_INPUT_CHANGED'
            assert digest(value['artifact_path']) == value['artifact_sha256']
            return read(value['artifact_path'])
        private = {'phase': phase, 'inputs': inputs, 'protocol': 'domains.alpha15.synthesis.v0.1'}
        # Explicit revisions share the original work-package cumulative cap.
        task = self.store.authenticate(['alpha15-task', phase.split('-v')[0]])
        contract = {'task': {'task_id': task}, 'visibility': 'local_private',
            'private_contract_receipt': self.store.authenticate(private), 'protocol': private['protocol']}
        plan = {'inputs': [], 'scratch_bytes': 2*1024*1024, 'evidence_bytes': 2*1024*1024,
            'expected_fits': 0, 'expected_permutations': 0,
            'uncertainty': 'Existing compact evidence only; native descriptor summaries, no spectral or supervised fits.'}
        self.guard(plan['scratch_bytes']+plan['evidence_bytes'])
        ledger = read(self.scheduler.root/'journal.json')
        old = ledger['runs'].get(fingerprint(contract)+':P4')
        if not (old and old['status'] == 'computed'):
            assert ledger['reserved_campaign_bytes']-self.approval['previous_campaign_reserved']+4194304 <= self.approval['new_reservation_envelope']
        def bounded(folder):
            try:
                value = callback(folder)
                assert tree_bytes([folder]) < 2*1024*1024
                return value
            except Exception as exc:
                # Detailed exceptions never reach the shared/public journal.
                self.save(phase+'-failure.json', {'exception_type': type(exc).__name__, 'detail': str(exc)})
                raise ValueError('PROTECTED_ALPHA15_STAGE_FAILED') from None
        receipt, value = self.scheduler.run(contract, 'P4', plan, bounded)
        if value is None:
            raise ValueError('ALPHA15_STAGE_UNAVAILABLE')
        path = self.scheduler.evidence/receipt['artifact']
        self.save(saved.name, {'inputs': inputs, 'artifact_path': str(path),
            'artifact_sha256': digest(path), 'receipt': receipt})
        self.guard()
        return value
