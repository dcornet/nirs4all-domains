"""Record the owner's source-resolution resource decision, without fitting."""
import json
from pathlib import Path

from nirs4all_domains.privacy import PrivateStore
from nirs4all_domains.storage import atomic_json


def main():
    cfg = json.loads(Path('.audit/alpha16/private-root.json').read_text())
    store = PrivateStore(cfg['root'], Path.cwd())
    approval = {
        'owner_approved': True, 'owner_statement': 'Valider le plan hors pilote',
        'owner_decision_date': '2026-10-18', 'workspace_ceiling': 16289597121,
        'campaign_ceiling': 805306368, 'previous_campaign_reserved': 733347282,
        'new_reservation_envelope': 50331648, 'candidate_cumulative_bytes': 6291456,
        'additional_original_bytes': 67108864, 'public_document_bytes': 4194304,
        'real_supervised_pilot_authorized': False,
        'new_PCA_HDBSCAN_B60_authorized': False,
        'scope': 'Original-reference closure and qualified development-only XY; separate approval before any real supervised fit.'}
    for path, value in [
        (Path('.audit/alpha16/budget-approval.json'), approval),
        (Path(cfg['report_root'])/'owner-resource-approval.json',
         {'approval': approval, 'authentication': store.authenticate(approval)})]:
        if path.exists():
            assert json.loads(path.read_text()) == value
        else:
            atomic_json(path, value)
    print('ALPHA16_RESOURCE_APPROVAL_RECORDED; REAL_PILOT_NOT_AUTHORIZED')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('ALPHA16_APPROVAL_RECORD_REFUSED')
        raise SystemExit(2) from None
