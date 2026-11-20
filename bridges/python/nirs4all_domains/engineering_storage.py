"""Prospective owner storage policy; no cleanup or scientific reservations."""
from __future__ import annotations

import hmac
from datetime import date
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid

from .storage import atomic_json, digest, fingerprint, safe_path, serial_lease

MAX_ALLOWED = 50_000_000_000
MIN_RESERVE = 2_147_483_648
NAMESPACE = 'domains-owner-storage'
PROTOCOL = 'domains.engineering_storage.v1'


def fail(code):
    raise ValueError(code) from None


def integer(value):
    return type(value) is int and value >= 0


def sha(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


class EngineeringStorage:
    """Uses an existing PrivateStore key and keeps every measurement/decision."""

    def __init__(self, store, workspace, recipe):
        self.store = store
        self.workspace, self.recipe = Path(workspace).resolve(), Path(recipe).resolve()
        self.root = safe_path(store.root, NAMESPACE)

    def _write(self, relative, body):
        path = safe_path(self.store.root, relative)
        if relative.startswith(NAMESPACE + '/decisions/') and path.exists():
            fail('OWNER_POLICY_DECISION_IMMUTABLE')
        atomic_json(path, {'value': body, 'authentication': self.store.authenticate(body)})

    def _read(self, relative):
        try:
            envelope = json.loads(safe_path(self.store.root, relative).read_text(encoding='utf-8'))
            body = envelope['value']
            if set(envelope) != {'value', 'authentication'} or not hmac.compare_digest(
                    envelope['authentication'], self.store.authenticate(body)):
                fail('OWNER_POLICY_AUTHENTICATION_FAILED')
            return body
        except Exception:
            fail('OWNER_POLICY_UNAVAILABLE_OR_INVALID')

    def current(self):
        pointer = self._read(NAMESPACE + '/current.json')
        if not isinstance(pointer, dict) or set(pointer) != {'protocol', 'decision'} or pointer['protocol'] != PROTOCOL:
            fail('OWNER_POLICY_POINTER_INVALID')
        relative, seen, child, policy = pointer['decision'], set(), None, None
        while relative is not None:
            if not isinstance(relative, str) or not re.fullmatch(NAMESPACE + r'/decisions/[0-9a-f]{32}\.json', relative) or relative in seen:
                fail('OWNER_POLICY_POINTER_INVALID')
            seen.add(relative)
            parent = self._read(relative)
            self._validate_policy(parent)
            if child is not None and 'previous_policy_sha256' in child:
                preserved = ('baseline_combined_bytes', 'baseline_measurement', 'science_journal_sha256',
                             'authorized_max_bytes', 'reserve_free_bytes', 'recipe_sha256')
                if (child['previous_policy_sha256'] != fingerprint(parent)
                        or child['previous_local_cap_bytes'] != parent['effective_bytes']
                        or any(child[k] != parent[k] for k in preserved)):
                    fail('OWNER_POLICY_AMENDMENT_CHAIN_INVALID')
            if policy is None:
                policy = parent
            child, relative = parent, parent.get('previous_decision')
        if policy is None:
            fail('OWNER_POLICY_POINTER_INVALID')
        return policy

    @staticmethod
    def _validate_policy(p):
        try:
            numeric = ('authorized_max_bytes', 'effective_bytes', 'engineering_bytes',
                       'baseline_combined_bytes', 'previous_local_cap_bytes', 'reserve_free_bytes')
            if p['protocol'] != PROTOCOL or not all(integer(p[k]) for k in numeric):
                fail('OWNER_POLICY_INVALID')
            if not p['baseline_combined_bytes'] <= p['effective_bytes'] <= p['authorized_max_bytes'] <= MAX_ALLOWED:
                fail('OWNER_POLICY_LIMIT_EXCEEDED')
            if p['engineering_bytes'] > p['effective_bytes'] - p['baseline_combined_bytes'] or p['reserve_free_bytes'] < MIN_RESERVE:
                fail('OWNER_POLICY_LIMIT_EXCEEDED')
            if not all(sha(p[k]) for k in ('recipe_sha256', 'owner_request_sha256', 'science_journal_sha256')):
                fail('OWNER_POLICY_INVALID')
            if not isinstance(p['baseline_measurement'], str) or not re.fullmatch(NAMESPACE + r'/measurements/[0-9a-f]{32}\.json', p['baseline_measurement']):
                fail('OWNER_POLICY_INVALID')
            if 'previous_policy_sha256' in p and (not sha(p['previous_policy_sha256']) or p.get('previous_decision') is None):
                fail('OWNER_POLICY_INVALID')
            if not isinstance(p['decision_date'], str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', p['decision_date']):
                fail('OWNER_POLICY_INVALID')
            try:
                date.fromisoformat(p['decision_date'])
            except ValueError:
                fail('OWNER_POLICY_INVALID')
        except (KeyError, TypeError):
            fail('OWNER_POLICY_INVALID')

    def measure(self, recipe_sha256):
        """Invoke only the explicitly pinned, previously qualified numeric recipe."""
        try:
            if not sha(recipe_sha256) or digest(self.recipe) != recipe_sha256:
                fail('MEASUREMENT_RECIPE_DIGEST_MISMATCH')
            relative = NAMESPACE + '/measurements/' + uuid.uuid4().hex + '.json'
            receipt = safe_path(self.store.root, relative)
            receipt.parent.mkdir(parents=True, exist_ok=True)
            started = time.time()
            result = subprocess.run([sys.executable, str(self.recipe), str(receipt)],
                                    cwd=self.workspace, capture_output=True, timeout=300, check=False)
            if result.returncode != 0 or not receipt.is_file() or receipt.stat().st_mtime < started - 2:
                fail('MEASUREMENT_FAILED')
            if digest(self.recipe) != recipe_sha256:
                fail('MEASUREMENT_RECIPE_DIGEST_MISMATCH')
            measurement = {'value': json.loads(receipt.read_text(encoding='utf-8')),
                           'measured_at': time.time(), 'receipt': relative,
                           'receipt_sha256': digest(receipt), 'recipe_sha256': recipe_sha256}
            self._validate_measurement(measurement)
            return measurement
        except ValueError as exc:
            if str(exc) in {'MEASUREMENT_FAILED', 'MEASUREMENT_RECIPE_DIGEST_MISMATCH', 'MEASUREMENT_INVALID_OR_STALE'}:
                raise
            fail('MEASUREMENT_FAILED')
        except Exception:
            fail('MEASUREMENT_FAILED')

    def _validate_measurement(self, measurement):
        try:
            m = measurement['value']
            if not 0 <= time.time() - measurement['measured_at'] <= 300:
                fail('MEASUREMENT_INVALID_OR_STALE')
            receipt = safe_path(self.store.root, measurement['receipt'])
            if digest(receipt) != measurement['receipt_sha256'] or json.loads(receipt.read_text(encoding='utf-8')) != m:
                fail('MEASUREMENT_INVALID_OR_STALE')
            fields = ('combined_bytes', 'workspace_ceiling_bytes', 'campaign_ceiling_bytes',
                      'reserved_campaign_bytes', 'remaining_reservations_bytes', 'new_reservations', 'ceiling_increase')
            if not all(integer(m[k]) for k in fields) or not sha(m['journal_sha256']):
                fail('MEASUREMENT_INVALID_OR_STALE')
            if m['new_reservations'] != 0 or m['ceiling_increase'] != 0:
                fail('MEASUREMENT_INVALID_OR_STALE')
            if m['campaign_ceiling_bytes'] - m['reserved_campaign_bytes'] != m['remaining_reservations_bytes']:
                fail('MEASUREMENT_INVALID_OR_STALE')
            if not isinstance(m['free_volume_bytes'], dict) or not m['free_volume_bytes'] or not all(integer(v) for v in m['free_volume_bytes'].values()):
                fail('MEASUREMENT_INVALID_OR_STALE')
        except Exception:
            fail('MEASUREMENT_INVALID_OR_STALE')

    def activate(self, *, effective_bytes, engineering_bytes, authorized_max_bytes,
                 reserve_free_bytes, owner_request_sha256, decision_date, recipe_sha256):
        with serial_lease(self.root / 'controller.lock'):
            if safe_path(self.store.root, NAMESPACE + '/current.json').exists() or any((self.root / 'decisions').glob('*.json')):
                fail('OWNER_POLICY_ALREADY_ACTIVE_USE_AMEND')
            measurement = self.measure(recipe_sha256)
            m = measurement['value']
            p = dict(protocol=PROTOCOL, effective_bytes=effective_bytes, engineering_bytes=engineering_bytes,
                     authorized_max_bytes=authorized_max_bytes, reserve_free_bytes=reserve_free_bytes,
                     baseline_combined_bytes=m['combined_bytes'],
                     previous_local_cap_bytes=m['workspace_ceiling_bytes'],
                     owner_request_sha256=owner_request_sha256, decision_date=decision_date,
                     recipe_sha256=recipe_sha256, science_journal_sha256=m['journal_sha256'],
                     baseline_measurement=measurement['receipt'], previous_decision=None)
            self._validate_policy(p)
            if min(m['free_volume_bytes'].values()) < reserve_free_bytes:
                fail('INSUFFICIENT_PHYSICAL_RESERVE')
            decision = NAMESPACE + '/decisions/' + uuid.uuid4().hex + '.json'
            self._write(decision, p)
            self._write(NAMESPACE + '/current.json', {'protocol': PROTOCOL, 'decision': decision})
            return self._snapshot(p, measurement, 0)

    def amend(self, *, effective_bytes, engineering_bytes, authorized_max_bytes,
              reserve_free_bytes, owner_request_sha256, decision_date, recipe_sha256):
        """Amend explicit engineering/effective caps without resetting the baseline."""
        with serial_lease(self.root / 'controller.lock'):
            previous = self.current()
            unchanged = dict(authorized_max_bytes=authorized_max_bytes,
                             reserve_free_bytes=reserve_free_bytes, recipe_sha256=recipe_sha256)
            if any(value != previous[name] for name, value in unchanged.items()):
                fail('OWNER_POLICY_AMENDMENT_SCOPE_INVALID')
            p = {**previous, 'effective_bytes': effective_bytes, 'engineering_bytes': engineering_bytes,
                 'owner_request_sha256': owner_request_sha256, 'decision_date': decision_date,
                 'previous_local_cap_bytes': previous['effective_bytes'],
                 'previous_decision': self._read(NAMESPACE + '/current.json')['decision'],
                 'previous_policy_sha256': fingerprint(previous)}
            self._validate_policy(p)
            measurement = self.measure(previous['recipe_sha256'])
            p['amendment_measurement'] = measurement['receipt']
            result = self._snapshot(p, measurement, 0)
            if result['status'] != 'ready':
                fail('OWNER_POLICY_AMENDMENT_NOT_ADMISSIBLE')
            result['before_amendment'] = self._snapshot(previous, measurement, 0)
            decision = NAMESPACE + '/decisions/' + uuid.uuid4().hex + '.json'
            self._write(decision, p)
            self._write(NAMESPACE + '/current.json', {'protocol': PROTOCOL, 'decision': decision})
            return result

    def snapshot(self, requested_bytes=0):
        with serial_lease(self.root / 'controller.lock'):
            p = self.current()
            return self._snapshot(p, self.measure(p['recipe_sha256']), requested_bytes)

    def _snapshot(self, p, measurement, requested_bytes):
        self._validate_policy(p)
        self._validate_measurement(measurement)
        if not integer(requested_bytes) or measurement['recipe_sha256'] != p['recipe_sha256']:
            fail('ENGINEERING_REQUEST_INVALID')
        m = measurement['value']
        growth = max(0, m['combined_bytes'] - p['baseline_combined_bytes'])
        reasons = []
        if growth + requested_bytes > p['engineering_bytes']:
            reasons.append('ENGINEERING_ALLOWANCE_EXCEEDED')
        if m['combined_bytes'] + requested_bytes > p['effective_bytes']:
            reasons.append('EFFECTIVE_LOCAL_CAP_EXCEEDED')
        # Every volume must admit the full request; never sum overlapping disks.
        volumes = [{'free_bytes': free, 'reserve_bytes': p['reserve_free_bytes'],
                    'usable_bytes': max(0, free - p['reserve_free_bytes'])}
                   for free in m['free_volume_bytes'].values()]
        if any(v['free_bytes'] - v['reserve_bytes'] < requested_bytes for v in volumes):
            reasons.append('INSUFFICIENT_PHYSICAL_RESERVE')
        return dict(protocol=PROTOCOL, owner_policy_sha256=fingerprint(p),
                    status='denied' if reasons else 'ready', reasons=reasons,
                    actual_combined_bytes=m['combined_bytes'], authorized_max_bytes=p['authorized_max_bytes'],
                    effective_bytes=p['effective_bytes'], engineering_baseline_bytes=p['baseline_combined_bytes'],
                    engineering_allowance_bytes=p['engineering_bytes'], engineering_used_bytes=growth,
                    engineering_remaining_bytes=max(0, p['engineering_bytes'] - growth), requested_bytes=requested_bytes,
                    historical_reference={'inherited_workspace_ceiling_bytes': m['workspace_ceiling_bytes']},
                    scientific_ceiling_bytes=m['campaign_ceiling_bytes'], scientific_reserved_bytes=m['reserved_campaign_bytes'],
                    scientific_remaining_bytes=m['remaining_reservations_bytes'], journal_sha256=m['journal_sha256'],
                    volumes=volumes, measured_at=measurement['measured_at'], new_scientific_reservations=0)
