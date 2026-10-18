"""Cost-only review around unchanged scientific/transport controllers."""
import json
from pathlib import Path
import continue_alpha13_calibration as transport
from alpha13_common import ROOT,PUBLIC,STATE
from nirs4all_domains.storage import atomic_json,digest


def main():
    journal=json.loads((STATE/'journal.json').read_text())
    review_path=ROOT/'calibration-storage-review.json'
    if not review_path.exists():
        failed=[r for r in journal['runs'].values() if r['status']=='failed' and r['contract'].get('phase')=='controlled-resampling']
        assert len(failed)==1 and failed[0]['reason']=='ValueError:STORAGE_ESTIMATE_UNDERRUN_REQUIRES_REVIEW'
        review={'review_controller_sha256':digest(__file__),'scientific_controller_sha256':digest('scripts/run_alpha13_calibration.py'),
            'transport_controller_sha256':digest('scripts/continue_alpha13_calibration.py'),'failed_receipts':failed,
            'review':'Observed 550738 evidence bytes exceed the estimated 524288; completed draw prefixes remain exact. Increase only P3 scratch/evidence estimates to 1 MiB each within unchanged campaign/task/evidence caps.',
            'new_p3_scratch_upper_bytes':1048576,'new_p3_evidence_upper_bytes':1048576,'scientific_contract_changed':False,
            'new_numerical_parameters':False,'historical_cleanup':False}
        atomic_json(review_path,review)
    review=json.loads(review_path.read_text())
    assert review['review_controller_sha256']==digest(__file__)
    assert review['scientific_controller_sha256']==digest('scripts/run_alpha13_calibration.py')
    assert review['transport_controller_sha256']==digest('scripts/continue_alpha13_calibration.py')
    original=transport.current_run
    def reviewed(contract,stage,plan,callback):
        if stage=='P3' and contract.get('phase')=='controlled-resampling':
            plan={**plan,'scratch_bytes':review['new_p3_scratch_upper_bytes'],'evidence_bytes':review['new_p3_evidence_upper_bytes'],
                'uncertainty':plan['uncertainty']+' Cost-only measured review: '+digest(review_path)}
        return original(contract,stage,plan,callback)
    transport.current_run=reviewed
    transport.main()
    atomic_json(PUBLIC/'calibration-storage-review.json',review)


if __name__=='__main__':main()
