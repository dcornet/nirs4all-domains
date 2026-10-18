"""Closed-schema exports with authenticated, explicit and cumulative review.

This is conservative disclosure control, not differential privacy or anonymity.
No API uploads or copies a private report to a public directory.
"""
from __future__ import annotations

import hashlib
import hmac
import base64
import json
import math
from pathlib import Path

from .privacy import exact_fields, fail, is_opaque, opaque_id
from .storage import atomic_json, digest, encoded, fingerprint

PROTOCOL = 'domains.disclosure.v0.1'
INDICATORS = frozenset({'pc1_fraction', 'pc5_fraction', 'retained_fraction',
    'near_coincidence_fraction', 'neighbor_overlap', 'partition_agreement',
    'noise_fraction', 'stability_ari', 'relative_skill', 'matched_skill_difference'})
STATISTICS = frozenset({'mean', 'median', 'p10', 'p90'})
OUTCOMES = frozenset({'approved_for_publication', 'approved_with_suppression',
                      'local_only', 'blocked_pending_review'})
REASONS = frozenset({'NOT_RELEASED', 'SOURCE_PERMISSION_MISSING', 'CONFIDENTIALITY_REVIEW_REQUIRED',
                    'SUPPRESSED', 'NUMERIC_UNAVAILABLE'})
LIMITATIONS = frozenset({'NOT_ANONYMITY_GUARANTEE', 'NOT_DIFFERENTIAL_PRIVACY',
    'OBSERVATION_CONDITIONAL', 'STUDY_OVERLAP_UNRESOLVED', 'NOT_SUPERVISED_VALIDATION',
    'NOT_REPRESENTATIVE_OF_NIRS', 'WITHIN_SOURCE_NORMALIZATION'})


def validate_public(value):
    exact_fields(value, {'protocol', 'visibility', 'receipt_id', 'review_id', 'policy_version',
                         'decision', 'indicators', 'counts', 'limitations'}, 'PUBLIC_FIELDS_NOT_ALLOWLISTED')
    if value['protocol'] != PROTOCOL or value['visibility'] != 'public' or \
            value['decision'] not in {'approved_for_publication', 'approved_with_suppression'}:
        fail('PUBLIC_VISIBILITY_INVALID')
    if not is_opaque(value['receipt_id']) or not is_opaque(value['review_id']) or value['policy_version'] != PROTOCOL:
        fail('PUBLIC_RECEIPTS_INVALID')
    if not isinstance(value['indicators'], list) or len(value['indicators']) > 32:
        fail('PUBLIC_INDICATORS_INVALID')
    seen = set()
    for cell in value['indicators']:
        exact_fields(cell, {'indicator', 'statistic', 'status', 'reason', 'value'}, 'PUBLIC_FIELDS_NOT_ALLOWLISTED')
        key = (cell['indicator'], cell['statistic'])
        if key in seen or key[0] not in INDICATORS or key[1] not in STATISTICS:
            fail('PUBLIC_INDICATOR_NOT_ALLOWLISTED')
        seen.add(key)
        if cell['status'] == 'computed':
            if cell['reason'] is not None or type(cell['value']) not in (int, float) or not math.isfinite(cell['value']):
                fail('PUBLIC_METRIC_INVARIANT_FAILED')
            if key[0] not in {'relative_skill', 'matched_skill_difference', 'partition_agreement', 'stability_ari'} and not 0 <= cell['value'] <= 1:
                fail('PUBLIC_METRIC_RANGE_FAILED')
            if key[0] in {'partition_agreement', 'stability_ari'} and not -1 <= cell['value'] <= 1:
                fail('PUBLIC_METRIC_RANGE_FAILED')
        elif cell['status'] != 'unavailable' or cell['reason'] not in REASONS or cell['value'] is not None:
            fail('PUBLIC_METRIC_INVARIANT_FAILED')
    if not isinstance(value['counts'], list) or len(value['counts']) > 32:
        fail('PUBLIC_COUNTS_INVALID')
    for cell in value['counts']:
        exact_fields(cell, {'cell', 'value', 'suppressed'}, 'PUBLIC_FIELDS_NOT_ALLOWLISTED')
        # Opaque enumeration cannot smuggle private category names.
        if not isinstance(cell['cell'], int) or isinstance(cell['cell'], bool) or cell['cell'] < 0 or type(cell['suppressed']) is not bool:
            fail('PUBLIC_COUNTS_INVALID')
        if cell['suppressed']:
            if cell['value'] is not None:
                fail('PUBLIC_COUNT_SUPPRESSION_INVALID')
        elif type(cell['value']) is not int or cell['value'] < 0:
            fail('PUBLIC_COUNTS_INVALID')
    if len({c['cell'] for c in value['counts']}) != len(value['counts']):
        fail('PUBLIC_COUNTS_INVALID')
    if not isinstance(value['limitations'], list) or any(v not in LIMITATIONS for v in value['limitations']):
        fail('PUBLIC_LIMITATION_NOT_ALLOWLISTED')
    if not {'NOT_ANONYMITY_GUARANTEE', 'NOT_DIFFERENTIAL_PRIVACY'} <= set(value['limitations']):
        fail('PUBLIC_PRIVACY_LIMITATIONS_REQUIRED')
    return True


def suppress_partition(counts, minimum, *, total_released=False):
    """One exhaustive partition only; overlapping marginals need joint review.

    Complementary suppression prevents subtraction from a separately reviewed
    exact total. It provides no universal guarantee about external knowledge.
    """
    if type(minimum) is not int or minimum < 2 or not isinstance(counts, list) or \
            any(type(v) is not int or v < 0 for v in counts):
        fail('DISCLOSURE_PARTITION_INVALID')
    hidden = {i for i, n in enumerate(counts) if 0 < n < minimum}
    if total_released and len(hidden) == 1:
        other = sorted((n, i) for i, n in enumerate(counts) if n > 0 and i not in hidden)
        if not other:
            fail('DISCLOSURE_TOTAL_MUST_BE_SUPPRESSED')
        hidden.add(other[0][1])
    return [{'cell': i, 'value': None if i in hidden else n, 'suppressed': i in hidden}
            for i, n in enumerate(counts)]


def candidate(indicators=(), counts=(), *, suppressed=False, limitations=()):
    """A draft only. Returned bytes remain PRIVATE until an exact review exists."""
    value = {'protocol': PROTOCOL, 'visibility': 'public', 'receipt_id': opaque_id(),
             'review_id': opaque_id(), 'policy_version': PROTOCOL,
             'decision': 'approved_with_suppression' if suppressed else 'approved_for_publication',
             'indicators': list(indicators), 'counts': list(counts),
             'limitations': sorted(set(limitations) | {'NOT_ANONYMITY_GUARANTEE', 'NOT_DIFFERENTIAL_PRIVACY'})}
    validate_public(value)
    return value


class DisclosureBoundary:
    """Local approval bound to exact candidate bytes and all earlier releases.

    An explicit review is an independent operation, never called by scientific
    execution. Caller supplies an owner/reviewer attestation retained locally.
    The attestation is not evidence that the software can verify legal authority.
    """
    def __init__(self, store):
        self.store = store
        self.root = store.root / 'disclosure'
        self.root.mkdir(exist_ok=True)
        self.ledger = self.root / 'ledger.json'

    def _ledger(self):
        if not self.ledger.exists():
            return []
        value = json.loads(self.ledger.read_text(encoding='utf-8'))
        if not hmac.compare_digest(value['authentication'], self.store.authenticate(value['releases'])):
            fail('DISCLOSURE_LEDGER_AUTHENTICATION_FAILED')
        return value['releases']

    def review(self, draft, source_receipts, clearance):
        validate_public(draft)
        exact_fields(clearance, {'decision', 'candidate_sha256', 'reviewer_attestation',
            'participation_approved', 'aggregate_fields_approved', 'joint_prior_exports',
            'small_cell_and_linkage_reviewed', 'source_receipts'}, 'DISCLOSURE_REVIEW_FIELDS_INVALID')
        if clearance['decision'] not in OUTCOMES:
            fail('DISCLOSURE_OUTCOME_INVALID')
        if clearance['decision'] in {'local_only', 'blocked_pending_review'}:
            return {'decision': clearance['decision'], 'reason': 'CONFIDENTIALITY_REVIEW_REQUIRED'}
        if clearance['decision'] != draft['decision'] or clearance['candidate_sha256'] != fingerprint(draft) or \
                not isinstance(clearance['reviewer_attestation'], str) or not clearance['reviewer_attestation'].strip() or \
                any(clearance[k] is not True for k in ('participation_approved', 'aggregate_fields_approved', 'small_cell_and_linkage_reviewed')):
            fail('DISCLOSURE_EXPLICIT_REVIEW_REQUIRED')
        if not source_receipts or len(source_receipts) != len(set(source_receipts)) or sorted(source_receipts) != sorted(clearance['source_receipts']):
            fail('DISCLOSURE_SOURCE_ROSTER_INVALID')
        bindings = {}
        for receipt in source_receipts:
            record = self.store.get(receipt)
            if record['admission']['permissions']['publish_aggregates']['status'] != 'allowed':
                fail('DISCLOSURE_SOURCE_PUBLICATION_NOT_ALLOWED')
            if record['admission']['participation_public'] is not True:
                fail('DISCLOSURE_PARTICIPATION_NOT_ALLOWED')
            bindings[receipt] = fingerprint(record)
        prior = sorted(r['export_sha256'] for r in self._ledger())
        if prior != sorted(clearance['joint_prior_exports']):
            fail('DISCLOSURE_JOINT_RELEASE_REVIEW_REQUIRED')
        proof = {'draft': draft, 'clearance': clearance, 'source_bindings': bindings, 'prior': prior}
        path = self.root / (draft['review_id'] + '.json')
        if path.exists():
            fail('DISCLOSURE_REVIEW_IMMUTABLE')
        atomic_json(path, {'proof': proof, 'authentication': self.store.authenticate(proof)})
        return {'decision': draft['decision'], 'review_id': draft['review_id']}

    def export(self, draft, destination):
        """Publish only approved sanitized bytes; retain private inputs on error."""
        validate_public(draft)
        try:
            value = json.loads((self.root / (draft['review_id'] + '.json')).read_text(encoding='utf-8'))
        except (OSError, ValueError):
            fail('DISCLOSURE_REVIEW_MISSING')
        proof = value['proof']
        if not hmac.compare_digest(value['authentication'], self.store.authenticate(proof)) or proof['draft'] != draft:
            fail('DISCLOSURE_REVIEW_AUTHENTICATION_FAILED')
        for receipt, expected in proof['source_bindings'].items():
            if fingerprint(self.store.get(receipt)) != expected:
                fail('DISCLOSURE_SOURCE_BINDING_CHANGED')
        ledger = self._ledger()
        sha = fingerprint(draft)
        previous = [r for r in ledger if r['export_sha256'] == sha]
        if not previous and sorted(r['export_sha256'] for r in ledger) != proof['prior']:
            fail('DISCLOSURE_JOINT_RELEASE_REVIEW_REQUIRED')
        destination = Path(destination)
        if destination.suffix != '.json' or destination.name != draft['receipt_id'] + '.json':
            fail('PUBLIC_EXPORT_OPAQUE_JSON_PATH_REQUIRED')
        if destination.exists() and destination.read_bytes() != encoded(draft):
            fail('PUBLIC_EXPORT_IMMUTABLE')
        # Record intent first. An interruption can only leave an approved ledger
        # entry without a file; exact retries are safe and do not skip review.
        if not previous:
            ledger.append({'export_sha256': sha, 'receipt_id': draft['receipt_id'],
                           'review_id': draft['review_id'], 'visibility': 'public'})
            atomic_json(self.ledger, {'releases': ledger, 'authentication': self.store.authenticate(ledger)})
        atomic_json(destination, draft)
        return {'receipt_id': draft['receipt_id'], 'sha256': digest(destination), 'visibility': 'public'}


def scan_bytes(data, *, sensitive_literals=()):
    """Secondary literal defense; strict schemas/provenance remain primary.

    Caller supplies locally authorized sensitive canaries, never prints matches.
    Includes JSON escaping, UTF-8/UTF-16 and common path slash representations.
    """
    if not isinstance(data, bytes):
        fail('OUTGOING_BYTES_REQUIRED')
    for item in sensitive_literals:
        if isinstance(item, bytes):
            variants = [item, item.hex().encode(), base64.b64encode(item)]
        elif isinstance(item, str) and item:
            variants = [item.encode(), item.encode('utf-16-le'),
                        json.dumps(item, ensure_ascii=True)[1:-1].encode(),
                        item.replace('\\', '/').encode()]
        else:
            fail('OUTGOING_TAINT_REGISTRY_INVALID')
        if any(v and v in data for v in variants):
            fail('OUTGOING_PRIVATE_CONTENT_DETECTED')
    return True


def validate_outgoing(path, data, *, provenance, sensitive_literals=(), authorized_public_hashes=None):
    """Use with actual staged blobs, logs, figure bytes and package members."""
    scan_bytes(str(path).encode(), sensitive_literals=sensitive_literals)
    scan_bytes(data, sensitive_literals=sensitive_literals)
    exact_fields(provenance, {'visibility', 'sha256', 'kind'})
    if provenance['visibility'] != 'public' or hashlib.sha256(data).hexdigest() != provenance['sha256']:
        fail('OUTGOING_PUBLIC_PROVENANCE_REQUIRED')
    # An object cannot authorize itself by changing its visibility label. This
    # roster comes from baseline Git blobs, synthetic fixture review, or the
    # authenticated disclosure ledger, not the report being checked.
    if authorized_public_hashes is None or provenance['sha256'] not in authorized_public_hashes.get(provenance['kind'], set()):
        fail('OUTGOING_PROVENANCE_NOT_AUTHORIZED')
    if provenance['kind'] == 'sanitized_export':
        try:
            validate_public(json.loads(data))
        except (ValueError, TypeError, UnicodeDecodeError):
            fail('OUTGOING_EXPORT_SCHEMA_INVALID')
    elif provenance['kind'] not in {'public_source', 'synthetic_fixture', 'historical_public', 'reviewed_documentation', 'public_log'}:
        fail('OUTGOING_KIND_NOT_ALLOWLISTED')
    return True
