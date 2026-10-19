"""Bind the explicit target-semantic correction for not-yet-started workers."""
from alpha18_common import Context
from nirs4all_domains.storage import digest

c=Context();original=c.load('reference-operational-freeze.json')
assert digest('.audit/alpha18-reference-controller-first.py')==original['controllers']['scripts/run_alpha18_campaign.py']
c.save('reference-semantics-continuation.json',{
    'original_controller_sha256':digest('.audit/alpha18-reference-controller-first.py'),
    'current_controller_sha256':digest('scripts/run_alpha18_campaign.py'),
    'semantics_id':c.load('target-semantics-v2.json')['semantics_id'],
    'completed_artifacts_changed':False,'selection_uses_model_scores':False,
    'ongoing_worker_may_finish_original_task_list':True,
    'scope':'Future workers skip additional metadata-defined identifiers/categories. Existing model scores are retained as diagnostic executions, outside the primary quantitative-endpoint synthesis.'})
print('SEMANTIC_CONTINUATION_RECORDED_WITH_ORIGINAL_SOURCE_PRESERVED')
