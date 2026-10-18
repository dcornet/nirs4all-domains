"""Confidential transport, scoped identities and evidence; no numerical kernels.

Private roots and keys are deliberately outside the Git workspace. Public export
is a different module/operation. Exceptions contain fixed codes only.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import stat
import subprocess
import uuid

from .storage import atomic_json, digest, encoded, fingerprint, safe_path

PROTOCOL = 'domains.private_corpus.v0.1'
STATES = frozenset({'allowed', 'denied', 'unknown', 'requires_owner_approval'})
RIGHTS = frozenset({'access', 'analysis', 'publish_aggregates', 'redistribute_raw'})
KINDS = frozenset({'observation', 'physical', 'reference', 'study', 'group', 'component'})


class PrivacyError(ValueError):
    """A safe code, without private exception chains or source values."""


def fail(code):
    raise PrivacyError(code) from None


def opaque_id():
    return str(uuid.uuid4())


def is_opaque(value):
    try:
        return isinstance(value, str) and str(uuid.UUID(value, version=4)) == value
    except (ValueError, AttributeError, TypeError):
        return False


def exact_fields(value, names, code='PRIVATE_CONTRACT_FIELDS_INVALID'):
    if not isinstance(value, dict) or set(value) != set(names):
        fail(code)


def _no_reparse(path):
    for part in [path, *path.parents]:
        if part.exists():
            info = part.lstat()
            if part.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400:
                fail('PRIVATE_ROOT_LINK_FORBIDDEN')


def protect_directory(path, workspace):
    """Create a task-owned directory; restrict/verify it before storing evidence.

    Windows ACL allows this owner and SYSTEM only. This does not restrict an
    administrator or another process under this same user account.
    """
    path, workspace = Path(path).absolute(), Path(workspace).resolve()
    _no_reparse(path)
    if path.resolve().is_relative_to(workspace) or workspace.is_relative_to(path.resolve()):
        fail('PRIVATE_ROOT_MUST_BE_OUTSIDE_WORKSPACE')
    if any((p / '.git').exists() for p in [path, *path.parents]):
        fail('PRIVATE_ROOT_MUST_BE_OUTSIDE_GIT')
    path.mkdir(parents=True, exist_ok=True)
    if os.name == 'nt':
        from .windows_security import WindowsAcl,WindowsAclError
        try:
            WindowsAcl().restrict(path)
        except WindowsAclError as error:
            fail('PRIVATE_ROOT_ACL_UNAVAILABLE_'+str(error))
        except Exception:
            fail('PRIVATE_ROOT_ACL_UNAVAILABLE')
    else:
        path.chmod(0o700)
        info = path.stat()
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
            fail('PRIVATE_ROOT_ACL_UNAVAILABLE')
    return path


def authorize(spec):
    """No publish/redistribution right is required for a local-private analysis."""
    exact_fields(spec, {'protocol', 'visibility', 'receipt_id', 'permissions',
                        'sensitive_handling', 'participation_public', 'source_scope'})
    if spec['protocol'] != PROTOCOL or spec['visibility'] not in ('public', 'local_private'):
        fail('PRIVATE_VISIBILITY_INVALID')
    if not is_opaque(spec['receipt_id']) or not isinstance(spec['source_scope'], str) or not spec['source_scope']:
        fail('PRIVATE_ADMISSION_SCOPE_INVALID')
    if type(spec['participation_public']) is not bool:
        fail('PARTICIPATION_PERMISSION_REQUIRED')
    exact_fields(spec['permissions'], RIGHTS)
    for name, right in spec['permissions'].items():
        exact_fields(right, {'status', 'evidence_receipt'})
        if right['status'] not in STATES:
            fail('PRIVATE_PERMISSION_STATE_INVALID')
        if right['status'] == 'allowed' and not is_opaque(right['evidence_receipt']):
            fail('PRIVATE_PERMISSION_EVIDENCE_REQUIRED')
        if name in ('access', 'analysis') and right['status'] != 'allowed':
            fail('PRIVATE_ACCESS_OR_ANALYSIS_NOT_AUTHORIZED')
    handling = spec['sensitive_handling']
    exact_fields(handling, {'status', 'evidence_receipt'})
    if handling['status'] != 'allowed' or not is_opaque(handling['evidence_receipt']):
        fail('PRIVATE_SENSITIVE_HANDLING_UNRESOLVED')
    if spec['visibility'] == 'public' and (not spec['participation_public'] or
            spec['permissions']['publish_aggregates']['status'] != 'allowed'):
        fail('PUBLIC_ADMISSION_NOT_AUTHORIZED')
    return fingerprint(spec)


def acquire_private(spec, provider):
    """Gate BEFORE invoking any source/provider callback; redact provider errors."""
    authorize(spec)
    try:
        return provider()
    except Exception:
        fail('PRIVATE_SOURCE_READ_FAILED')


class PrivateStore:
    def __init__(self, root, workspace):
        self.root = protect_directory(root, workspace)
        self.keys = protect_directory(self.root / 'keys', workspace)
        self.evidence = protect_directory(self.root / 'evidence', workspace)
        self.identities = protect_directory(self.root / 'identities', workspace)
        key = self.keys / 'scope.key'
        _no_reparse(key)
        if not key.exists():
            with key.open('xb') as stream:
                stream.write(secrets.token_bytes(32))
            if os.name != 'nt':
                key.chmod(0o600)
        self._key = key.read_bytes()
        if len(self._key) != 32 or key.is_symlink():
            fail('PRIVATE_SECRET_INVALID')

    def authenticate(self, value):
        return hmac.new(self._key, encoded(value), hashlib.sha256).hexdigest()

    def put(self, spec, payload, receipt_id=None):
        admission = authorize(spec)
        receipt = receipt_id or opaque_id()
        if not is_opaque(receipt):
            fail('PRIVATE_RECEIPT_INVALID')
        body = {'protocol': PROTOCOL, 'visibility': 'local_private', 'receipt_id': receipt,
                'admission_fingerprint': admission, 'admission': spec, 'payload': payload}
        try:
            fingerprint(body)
        except (ValueError, TypeError, OverflowError):
            fail('PRIVATE_EVIDENCE_NOT_FINITE_JSON')
        record = {**body, 'authentication': self.authenticate(body)}
        if len(encoded(record)) > 4194304:
            fail('PRIVATE_EVIDENCE_BUDGET_EXCEEDED')
        path = self.evidence / (receipt + '.json')
        if path.exists():
            if path.read_bytes() != encoded(record):
                fail('PRIVATE_EVIDENCE_IMMUTABLE')
        else:
            atomic_json(path, record)
        return receipt

    def get(self, receipt):
        if not is_opaque(receipt):
            fail('PRIVATE_RECEIPT_INVALID')
        try:
            record = json.loads((self.evidence / (receipt + '.json')).read_text(encoding='utf-8'))
            auth = record.pop('authentication')
            if not hmac.compare_digest(auth, self.authenticate(record)):
                fail('PRIVATE_EVIDENCE_AUTHENTICATION_FAILED')
            if record['receipt_id'] != receipt or authorize(record['admission']) != record['admission_fingerprint']:
                fail('PRIVATE_EVIDENCE_AUTHENTICATION_FAILED')
            return record
        except (OSError, KeyError, TypeError, json.JSONDecodeError):
            fail('PRIVATE_EVIDENCE_UNAVAILABLE')


class ScopedIdentities:
    """Exact original strings, scoped HMACs, persisted reverse collision checks."""
    def __init__(self, store):
        self.store = store
        self.path = store.identities / 'mapping.json'
        if self.path.exists():
            envelope = json.loads(self.path.read_text(encoding='utf-8'))
            body = envelope['mapping']
            if not hmac.compare_digest(envelope['authentication'], store.authenticate(body)):
                fail('PRIVATE_MAPPING_AUTHENTICATION_FAILED')
            self.mapping = body
        else:
            self.mapping = {}

    def identity(self, study, population, kind, original):
        if kind not in KINDS or any(not isinstance(v, str) or not v for v in (study, population, original)):
            fail('PRIVATE_IDENTITY_SCOPE_INVALID')
        contract = [PROTOCOL, study, population, kind, original]
        pseudonym = 'p_' + self.store.authenticate(contract)
        if pseudonym in self.mapping and self.mapping[pseudonym] != contract:
            fail('PRIVATE_PSEUDONYM_COLLISION')
        self.mapping[pseudonym] = contract
        return pseudonym

    def flush(self):
        atomic_json(self.path, {'mapping': self.mapping, 'authentication': self.store.authenticate(self.mapping)})

    def map_view(self, study, population, observations, components, split, *,
                 view_scope, relationship=None):
        if any(not isinstance(v, str) or not v or '\x00' in v for v in (study, population, view_scope)):
            fail('PRIVATE_IDENTITY_SCOPE_INVALID')
        if len(observations) != len(set(observations)) or set(observations) != set(components) or set(observations) != set(split):
            fail('COMPLETE_PRIVATE_IDENTITY_MAP_REQUIRED')
        # Unverified views intentionally cannot join by coincident original keys.
        scope = population + '\x00view:' + view_scope
        if relationship is not None:
            exact_fields(relationship, {'verified', 'evidence_receipt', 'study', 'population'})
            if relationship['verified'] is not True or not is_opaque(relationship['evidence_receipt']) or \
                    relationship['study'] != study or relationship['population'] != population:
                fail('PRIVATE_PAIRING_NOT_VERIFIED')
            scope = population + '\x00verified-pair'
        ids = {s: self.identity(study, scope, 'observation', s) for s in observations}
        mapped = {ids[s]: self.identity(study, scope, 'component', components[s]) for s in observations}
        # Relational checks use complete membership, never a scientific numeric kernel.
        before, after = {}, {}
        for s in observations:
            before.setdefault(components[s], set()).add(s)
            after.setdefault(mapped[ids[s]], set()).add(s)
        if any(len({split[s] for s in members})!=1 for members in before.values()):
            fail('PRIVATE_COMPONENT_CROSSES_SPLIT')
        if sorted(map(sorted, before.values())) != sorted(map(sorted, after.values())):
            fail('PRIVATE_COMPONENT_MEMBERSHIP_CHANGED')
        self.flush()
        return {'observation_ids': [ids[s] for s in observations], 'components': mapped,
                'split': {ids[s]: split[s] for s in observations},
                'identity_scope': 'dependency_preserved_not_independence_certified'}


def characterize_private(spec, reader, compute, store):
    """Reader supplies X only; compute can be the existing native X workflow.

    No target accessor is accepted/invoked. Neither raw spectra nor scores become
    evidence; the scientific callback must return compact evidence.
    """
    raw = acquire_private(spec, reader)
    required = {'source_id', 'axis', 'axis_unit', 'observation_ids', 'spectra', 'identity_evidence'}
    if not isinstance(raw, dict) or set(raw) != required:
        fail('PRIVATE_X_ONLY_TRANSPORT_REQUIRED')
    try:
        result = compute(raw)
        if not isinstance(result, dict) or result.get('test_target_accessed') is not False:
            fail('PRIVATE_X_ONLY_RESULT_REQUIRED')
        def inspect(v):
            if isinstance(v, dict):
                if set(v) & {'spectra', 'transport_only_scores', 'loadings', 'Y', 'Y_test', 'y_test'}:
                    fail('PRIVATE_COMPACT_EVIDENCE_REQUIRED')
                for child in v.values():
                    inspect(child)
            elif isinstance(v, list):
                for child in v:
                    inspect(child)
        inspect(result)
        return store.put(spec, result)
    except PrivacyError:
        raise
    except Exception:
        fail('PRIVATE_CHARACTERIZATION_FAILED')
