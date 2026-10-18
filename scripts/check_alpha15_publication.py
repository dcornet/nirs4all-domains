"""Reuse the existing exact-byte publication review for finite alpha.15 sources."""
import check_alpha14_publication as review
private_taints = review.private_taints

review.BASELINE = '7ecb6d978c20c2ab7195d1b288e52d66a7656748'
review.ROSTER = 'docs/audit/alpha15-public-source-roster.json'
review.REVIEW_FILE = 'alpha15/public-source-review.json'
review.NEW = {
    'configs/bank/storage-policy-alpha15.json', review.ROSTER,
    *('bridges/python/nirs4all_domains/'+n for n in ['cohort.py', 'synthesis.py', 'confrontation.py', 'cross-dataset-synthesis.v1.schema.json']),
    'schemas/cross-dataset-synthesis.v1.schema.json',
    *('scripts/'+n+'.py' for n in ['alpha15_common', 'prepare_alpha15_audit', 'record_alpha15_approval',
        'run_alpha15_synthesis', 'run_alpha15_source_closure', 'finalize_alpha15_local',
        'generate_synthesis_schemas', 'check_alpha15_results', 'check_alpha15_publication',
        'validate_alpha15', 'collect_alpha15_validation', 'record_alpha15_ci', 'finalize_alpha15_delivery']),
    *('tests/integration/'+n+'.py' for n in ['test_synthesis', 'test_confrontation']),
    *('docs/'+n+'.md' for n in ['ALPHA15_RESOURCE_PLAN', 'ALPHA15_EXECUTION_NOTES',
        'ALPHA15_SCIENTIFIC_SYNTHESIS_PROTOCOL', 'ALPHA15_CROSS_DATASET_ANALYSIS',
        'ALPHA15_SOURCE_CLOSURE', 'ALPHA15_SUPERVISED_ADMISSION', 'ALPHA15_FALSIFICATION_PILOT',
        'ALPHA15_DISCLOSURE_REVIEW', 'ALPHA15_RELEASE_REPORT']),
    *('docs/audit/'+n+'.json' for n in ['alpha15-frozen-output-hashes', 'alpha15-portable-preservation',
        'alpha15-validation', 'alpha15-storage', 'github-ci-alpha15'])}
review.CHANGED |= {'scripts/check_alpha14_publication.py'}

if __name__ == '__main__': review.main()
