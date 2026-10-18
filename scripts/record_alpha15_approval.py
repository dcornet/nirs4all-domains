"""Record the owner's explicit synthesis-only resource decision; no science."""
import json
from pathlib import Path
from nirs4all_domains.privacy import PrivateStore
from nirs4all_domains.storage import atomic_json


def main():
    cfg = json.loads(Path('.audit/alpha15/private-root.json').read_text())
    store = PrivateStore(cfg['root'], Path.cwd())
    approval = {'owner_approved': True, 'owner_statement': 'Valider ce plan hors pilote',
        'owner_decision_date': '2026-10-18', 'workspace_ceiling': 16021161665,
        'campaign_ceiling': 805306368, 'previous_campaign_reserved': 699792850,
        'new_reservation_envelope': 67108864, 'real_supervised_pilot_authorized': False,
        'new_PCA_HDBSCAN_B60_authorized': False, 'source_document_download_upper_bytes': 8388608,
        'scope': 'Existing-evidence synthesis, targeted source closure and confidential reporting.'}
    path = Path('.audit/alpha15/budget-approval.json')
    if path.exists():
        assert json.loads(path.read_text()) == approval
    else:
        atomic_json(path, approval)
    destination = Path(cfg['report_root'])/'owner-resource-approval.json'
    atomic_json(destination, {'approval': approval, 'authentication': store.authenticate(approval)})
    print('ALPHA15_SYNTHESIS_RESOURCE_APPROVAL_RECORDED; REAL_PILOT_NOT_AUTHORIZED')


if __name__ == '__main__':
    try: main()
    except Exception:
        print('ALPHA15_APPROVAL_RECORD_REFUSED'); raise SystemExit(2)
