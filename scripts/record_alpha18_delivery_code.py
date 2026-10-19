"""Bind explicit export trust at delivery; numerical evaluator AST is unchanged."""
import ast
from pathlib import Path
from alpha18_common import Context
from nirs4all_domains.storage import digest,fingerprint,atomic_json

c=Context();old=c.load('group-explicit-fold-code-continuation.json')
archive=Path('.audit/alpha18-full-bank-grouped-first.py');current=Path('bridges/python/nirs4all_domains/full_bank.py')
assert digest(archive)==old['current_core_sha256']
def methods(path):
    tree=ast.parse(path.read_text(encoding='utf-8'))
    return {n.name:fingerprint(ast.dump(n,include_attributes=False)) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['fit_predict','scores','reference_task','folds_for','target_values','matrix_request']}
assert methods(archive)==methods(current)
v={'alignment_protocol':'domains.same_export.v0.2','prior_grouped_core_sha256':digest(archive),
   'packaged_core_sha256':digest(current),'unchanged_numerical_transport_function_AST':methods(current),
   'qualification':'Six focused tests: explicit owner receipt, wrong-hash refusal, unattested count refusal, retained component purge, known marker, unsorted axes, singleton score and native explicit folds.',
   'scope':'Make the existing global owner trust explicit for future shared-adapter callers; no scientific rerun or altered prior output.',
   'plan_sha256':digest('docs/ALPHA18_DELIVERY_ADAPTER.md')}
c.save('delivery-adapter-code-continuation.json',v);atomic_json('docs/campaign/delivery-adapter-code-continuation.json',v)
print('CONTENT_BOUND_OWNER_EXPORT_RECEIPT_ENFORCED; NUMERICAL_TRANSPORT_AST_UNCHANGED')
