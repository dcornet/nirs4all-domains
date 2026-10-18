"""Atomic compact prefixes, bound to exact population/provider/controller identity."""
import json
from pathlib import Path
from .storage import atomic_json,fingerprint


def recover_prefix(attempt_root,key,contract):
    found=[]
    for path in sorted(Path(attempt_root).glob('*/prefix-'+key+'.json')):
        entry=json.loads(path.read_text())
        if entry['contract']!=contract:raise ValueError('POWER_PREFIX_CONTRACT_MISMATCH')
        records=entry['records']
        if entry['records_sha256']!=fingerprint(records):raise ValueError('POWER_PREFIX_CHECKSUM_MISMATCH')
        if [v['draw'] for v in records]!=list(range(len(records))):raise ValueError('POWER_PREFIX_IS_NOT_CONTIGUOUS')
        found.append(records)
    if not found:return []
    longest=max(found,key=len)
    if any(records!=longest[:len(records)] for records in found):raise ValueError('CONFLICTING_POWER_PREFIXES')
    return longest


def save_prefix(path,contract,records):
    if [v['draw'] for v in records]!=list(range(len(records))):raise ValueError('POWER_PREFIX_IS_NOT_CONTIGUOUS')
    return atomic_json(path,{'contract':contract,'records':records,'records_sha256':fingerprint(records)},524288)
