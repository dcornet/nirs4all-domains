"""Exact-contract partial draw recovery; never accept a similar scientific result."""
import json
from pathlib import Path
from .storage import fingerprint,atomic_json


def recover_draw(attempt_root,number,contract):
    found=[]
    for path in sorted(Path(attempt_root).glob('*/draw-'+str(number)+'.json')):
        record=json.loads(path.read_text())
        if record['contract']!=contract:
            raise ValueError('PARTIAL_DRAW_CONTRACT_MISMATCH')
        if record['value_sha256']!=fingerprint(record['value']):
            raise ValueError('PARTIAL_DRAW_CHECKPOINT_CORRUPT')
        found.append(record['value'])
    if not found:return None
    if any(value!=found[0] for value in found[1:]):
        raise ValueError('CONFLICTING_PARTIAL_DRAW_CHECKPOINTS')
    return found[0]


def checkpoint_draw(path,contract,value):
    return atomic_json(path,{'contract':contract,'value':value,'value_sha256':fingerprint(value)},34816)
