"""Real-source retained-label adversary; preserve and disclose the initial audit."""
import copy
import json
from pathlib import Path
from nirs4all_domains.storage import atomic_json, digest, fingerprint
from run_alpha11_litter import ROOT,PUBLIC,original,assemble


def main():
    axis,rows=original('intact_spec.csv');other,ground=original('ground_spec.csv');assert axis==other
    expected=assemble(axis,rows,ground)
    stored=json.loads((ROOT/'litter/task-v2.json').read_text())
    assert expected[0]==stored
    changed_a,changed_b=copy.deepcopy(rows),copy.deepcopy(ground)
    retained=set(expected[2]['retained_groups']);mutations=0
    for key,row in changed_a.items():
        if row['plot'] in retained:
            row['Nmass']='FORBIDDEN_RETAINED_REFERENCE';mutations+=1
            if key in changed_b:changed_b[key]['Nmass']='DIFFERENT_FORBIDDEN_REFERENCE'
    changed=assemble(axis,changed_a,changed_b)
    if changed!=expected:raise ValueError('RETAINED_SOURCE_REFERENCE_INFLUENCED_SANITIZED_TASK')
    result={'protocol':'domains.alpha11.source_isolation.v0.1','original_audit_ref':'litter-original-audit.json',
        'original_source_audit_numeric_retained_access':True,
        'correction':'The initial paired integrity audit compared retained Nmass values and incorrectly marked its source-audit access flag false. Model training/selection/scoring always received only development Y. The corrected adapter compares development values and retained identity keys only.',
        'retained_numeric_mutations':mutations,'sanitized_task_exact':True,'transfer_development_exact':True,
        'task_sha256':digest(ROOT/'litter/task-v2.json'),'mean_task_sha256':digest(ROOT/'litter/mean-task-v2.json'),
        'preserved_evaluation_id':json.loads((PUBLIC/'litter-evaluation.json').read_text())['evaluation_id'],
        'qualification_scope':'Final evidence uses the isolated adapter and identical already-executed numerical inputs/folds; no score-based change or new fit required.',
        'test_target_accessed_in_corrected_adapter':False}
    atomic_json(PUBLIC/'source-isolation.json',result);print(json.dumps({k:result[k] for k in ['retained_numeric_mutations','sanitized_task_exact','transfer_development_exact']}))


if __name__=='__main__':main()
