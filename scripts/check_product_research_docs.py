"""Documentation/continuity checks only; no data access, fitting or migration."""
import ast
import json
from pathlib import Path
import re
import subprocess


def read(path):
    def invalid(value):raise ValueError('NONFINITE_JSON')
    return json.loads(Path(path).read_text(encoding='utf-8'),parse_constant=invalid)


def git(*args):return subprocess.check_output(['git',*args],text=True).strip()


def main():
    manifest=read('docs/research-continuity.json');base=manifest['baseline_commit']
    assert manifest['mode']=='references_only_no_migration'
    for key in ['creation_authorized','repository_created_by_this_assignment','raw_data_copied',
                'private_evidence_moved','archives_duplicated','new_research_results_published','new_global_results_schema']:
        assert manifest[key] is False,key
    assert len({r['path'] for r in manifest['records']})==len(manifest['records'])
    preserved=0
    for record in manifest['records']:
        path=record['path'];assert Path(path).is_file()
        assert git('rev-parse',base+':'+path)==record['git_blob_id'],path
        assert record['immutable_url']==manifest['source_repository']+'/blob/'+base+'/'+path
        assert record['disposition']=='retain_and_reference'
        if record['preserve_current_bytes']:
            assert git('hash-object','--path='+path,path)==record['git_blob_id'],path
            preserved+=1
        else:
            assert record['current_path_policy']=='evolving_index_with_pinned_snapshot'
            assert path in ['docs/ROADMAP.md','docs/RELEASE_HISTORY.md'] or path.startswith('docs/campaign/')
    files=['README.md','docs/ROADMAP.md','docs/PRODUCT_RESEARCH_BOUNDARY.md','docs/VALIDATION_INTENTS.md',
           'docs/STRUCTURAL_GENERALIZATION_RESEARCH_PROGRAM.md','docs/RESEARCH_INTEROPERABILITY_AND_TRANSITION.md',
           'docs/MULTISCALE_AND_AUGMENTATION_NOTES.md','docs/ARCHITECTURE.md','docs/METHOD_REUSE_MATRIX.md','docs/SCIENTIFIC_PROTOCOLS.md']
    for name in files:
        path=Path(name)
        for link in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if '://' not in link and not link.startswith('#'):
                assert (path.parent/link.split('#')[0]).exists(),(name,link)
    status=read('docs/campaign/status.json');text=Path('README.md').read_text(encoding='utf-8')
    assert f"| Complete raw/SNV source profiles | {status['computed_source_views']} |" in text
    assert f"| Complete primary quantitative reference tasks | {status['completed_primary_quantitative_tasks']} |" in text
    for name in ['README.md','docs/ROADMAP.md']:
        content=Path(name).read_text(encoding='utf-8')
        for n in range(1,6):assert re.search(r'^\| D'+str(n)+r'\b',content,re.M)
    # Exercise only the milestone loop; never regenerate archived figures/matrices.
    tree=ast.parse(Path('scripts/render_alpha18_science.py').read_text(encoding='utf-8'))
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    loop=next(n for n in function.body if isinstance(n,ast.For) and any(
        isinstance(v,ast.If) and isinstance(v.test,ast.Call) and isinstance(v.test.func,ast.Attribute)
        and v.test.func.attr=='startswith' for v in n.body))
    namespace={'text':text,'s':status,'lines':[]}
    exec(compile(ast.Module(body=[loop],type_ignores=[]),'<documentation-milestones>','exec'),namespace)
    updated='\n'.join(namespace['lines'])
    for old in text.splitlines():
        if old.startswith(('| D1 ','| D3 ')):
            prefix='|'+old.split('|')[1]+'|'
            new=next(line for line in updated.splitlines() if line.startswith(prefix))
            assert new.split('|')[:-2]==old.split('|')[:-2]
    print(json.dumps({'continuity_references':len(manifest['records']),'preserved_current_research_records':preserved,
        'documentation_links':'valid','status_counts':'current','D1_D5_renderer':'preserves_product_objectives',
        'new_global_results_schema':False,'model_fits':0}))


if __name__=='__main__':main()
