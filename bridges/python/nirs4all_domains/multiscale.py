"""Selected-branch persistence/support sidecars over existing Methods evidence.

No fitting, hierarchy reconstruction, biological inference or numerical kernel.
Public Methods owns clustering and descriptive distribution summaries.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import json
import math
from pathlib import Path

from .predictive import native_summary
from .storage import fingerprint

PROTOCOL = 'domains.selected_branch_persistence.v1'
QUALIFIED_PROVIDER = '1.3.6'


def state(value=None, reason=None, status='unavailable'):
    return {'status': 'computed' if reason is None else status,
            'reason': reason, 'value': value if reason is None else None}


def _extract(report, index):
    if isinstance(index, bool) or not isinstance(index, int) or index < 0:
        raise ValueError('NONNEGATIVE_SETTING_INDEX_REQUIRED')
    protocol = report.get('protocol_version')
    if protocol == 'domains.hierarchy_profile.v1':
        if index != 0:
            raise ValueError('SETTING_INDEX_OUT_OF_RANGE')
        return {'setting': {'status': 'computed', 'reason': None},
                'native': report['hdbscan'], 'parameters': report['parameters'],
                'n': report['n_observations'], 'ids': None,
                'representation': {'name': report['representation'],
                    'partition': 'full source descriptive fit', 'pca': report['pca']},
                'support_unit': 'observation', 'pointer': '/hdbscan',
                'stability_pointer': None, 'noise_fraction': None}
    if protocol == 'domains.structure.v0.1':
        settings = report['settings']
        if index >= len(settings):
            raise ValueError('SETTING_INDEX_OUT_OF_RANGE')
        setting = settings[index]
        fit = setting.get('reference')
        population = report.get('population') or {}
        return {'setting': setting, 'native': fit.get('hdbscan') if fit else None,
                'parameters': setting['parameters'], 'n': len(fit['observation_ids']) if fit else None,
                'ids': fit['observation_ids'] if fit else None,
                'representation': {'name': population.get('selected_representation', 'unknown'),
                    'partition': population.get('partition', 'unknown'),
                    'pca': fit.get('pca') if fit else None},
                'support_unit': 'fitted representation row (technical mean)',
                'pointer': f'/settings/{index}/reference/hdbscan',
                'stability_pointer': f'/settings/{index}/stability',
                'noise_fraction': fit.get('noise_fraction') if fit else None}
    if protocol == 'domains.unsupervised.v0.1':
        settings = report['cluster_settings']
        if index >= len(settings):
            raise ValueError('SETTING_INDEX_OUT_OF_RANGE')
        setting = settings[index]
        compact = setting.get('value') or {}
        evidence = compact.get('hierarchy_evidence') or {}
        transport = evidence.get('value') if evidence.get('status') == 'computed' else None
        if transport and transport.get('protocol_version') != 'domains.hdbscan_transport.v1':
            raise ValueError('UNSUPPORTED_HIERARCHY_TRANSPORT')
        # These are frozen in this exact existing protocol, not guessed from labels.
        parameters = {'min_cluster_size': compact.get('min_cluster_size'),
                      'min_samples': compact.get('min_samples'),
                      'selection_method': 'eom', 'allow_single_cluster': False}
        if transport and transport['parameters'] != parameters:
            raise ValueError('INCONSISTENT_FROZEN_CONFIGURATION')
        if transport and any(transport['hdbscan'].get(k) != compact.get(k) for k in ('labels', 'n_clusters')):
            raise ValueError('INCONSISTENT_NATIVE_COMPACT_MEMBERSHIP')
        return {'setting': setting, 'native': transport['hdbscan'] if transport else compact,
                'parameters': parameters, 'n': report.get('n_observations'), 'ids': None,
                'representation': {'name': report.get('representation', 'unknown'),
                    'partition': 'full source descriptive fit', 'pca': report.get('pca')},
                'support_unit': 'observation',
                'pointer': f'/cluster_settings/{index}/value/hierarchy_evidence/value/hdbscan'
                    if transport else f'/cluster_settings/{index}/value',
                'stability_pointer': None, 'noise_fraction': compact.get('noise_fraction')}
    raise ValueError('UNSUPPORTED_STRUCTURE_REPORT_PROTOCOL')


def _integer(value, minimum=0):
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def _summary(values):
    if not values:
        return state(reason='NO_SELECTED_CLUSTERS', status='not_applicable')
    try:
        value = native_summary(values)
        if any(v is not None and not math.isfinite(v) for v in value.values()):
            raise ValueError('NONFINITE_SUMMARY')
        return state(value)
    except (ImportError, OSError, RuntimeError, ValueError):
        return state(reason='NATIVE_METHODS_SUMMARY_UNAVAILABLE')


def _hierarchy(native, count, counts):
    nodes = native.get('hierarchy')
    if nodes is None:
        return {}, state(reason='ORIGINAL_HIERARCHY_NOT_RETAINED'), 'unknown'
    if not isinstance(nodes, list) or not nodes:
        raise ValueError('INVALID_NATIVE_HIERARCHY')
    if any(not isinstance(node, dict) or not
           {'parent', 'size', 'label', 'lambda_birth', 'lambda_death', 'stability'} <= node.keys()
           for node in nodes):
        return {}, state(reason='ORIGINAL_HIERARCHY_FIELDS_NOT_RETAINED'), 'unknown'
    selected = {}
    for index, node in enumerate(nodes):
        parent, size, label = node['parent'], node['size'], node['label']
        if (not isinstance(parent, int) or isinstance(parent, bool)
                or (index == 0 and parent != -1)
                or (index > 0 and not 0 <= parent < index)
                or not _integer(size, 1) or not isinstance(label, int) or isinstance(label, bool)
                or label < -1 or label >= count):
            raise ValueError('INVALID_NATIVE_HIERARCHY')
        if label >= 0:
            if label in selected or size < counts[label]:
                raise ValueError('INCONSISTENT_SELECTED_NODE_SUPPORT')
            selected[label] = index
    if set(selected) != set(range(count)):
        raise ValueError('INCONSISTENT_SELECTED_NODE_LABELS')
    diagnostics = native.get('nonfinite_diagnostics', [])
    infinite = any(d['field'] == 'hierarchy.lambda_death'
                   and d['native_value'] == 'positive_infinity' for d in diagnostics)
    convention = ('global_infinite_lambda_fallback_one' if infinite else
                  'global_zero_lambda_fallback_one' if all(n['lambda_death'] == 0 for n in nodes)
                  else 'finite_or_unknown_global_lambda')
    return selected, state({'n_nodes': len(nodes)}), convention


def _partition(extracted, provider):
    native = extracted['native']
    if extracted['setting']['status'] != 'computed' or not native:
        return state(reason=extracted['setting'].get('reason') or 'NATIVE_FIT_UNAVAILABLE'), None
    labels, n, k = native.get('labels'), extracted['n'], native.get('n_clusters')
    if labels is None or n is None or k is None:
        return state(reason='COMPACT_HISTORY_LACKS_LABELLED_POPULATION'), None
    if (not _integer(n, 1) or not _integer(k) or not isinstance(labels, list)
            or len(labels) != n or any(not isinstance(v, int) or isinstance(v, bool)
                                      or v < -1 or v >= k for v in labels)
            or native.get('noise_label', -1) != -1 or native.get('native_status', 0) != 0):
        raise ValueError('INCONSISTENT_NATIVE_MEMBERSHIP_COUNTS')
    ids = extracted['ids']
    if ids is not None and (len(ids) != n or len(set(ids)) != n or any(not v for v in ids)):
        raise ValueError('INCONSISTENT_FITTED_ROW_IDENTITIES')
    counts = Counter(labels)
    if set(counts) - {-1} != set(range(k)):
        raise ValueError('EMPTY_OR_UNDECLARED_SELECTED_CLUSTER')
    noise = counts[-1] / n
    if extracted['noise_fraction'] is not None and abs(extracted['noise_fraction'] - noise) > 1e-12:
        raise ValueError('INCONSISTENT_NATIVE_NOISE_FRACTION')
    strengths = native.get('membership_strengths')
    if strengths is not None and (len(strengths) != n or any(
            not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v)
            or not 0 <= v <= 1 or (label == -1 and v != 0)
            for v, label in zip(strengths, labels, strict=True))):
        raise ValueError('INCONSISTENT_NATIVE_MEMBERSHIP_STRENGTHS')
    selected, hierarchy, convention = _hierarchy(native, k, counts)
    if hierarchy['status'] == 'computed' and native['hierarchy'][0]['size'] != n:
        raise ValueError('INCONSISTENT_NATIVE_ROOT_SIZE')
    persistence = native.get('cluster_persistence')
    if persistence is not None and (not isinstance(persistence, list) or len(persistence) != k):
        raise ValueError('INCONSISTENT_NATIVE_PERSISTENCE_COUNT')
    qualified = (str(provider.get('version', '')).split('+')[0] == QUALIFIED_PROVIDER
                 and provider.get('abi') == '2.19.0')
    rows = []
    for label in range(k):
        value = persistence[label] if persistence is not None else None
        reason = ('PERSISTENCE_NOT_RETAINED' if persistence is None else
                  'PROVIDER_PERSISTENCE_SEMANTICS_NOT_QUALIFIED' if not qualified else
                  'NONFINITE_OR_UNDEFINED_NATIVE_PERSISTENCE' if value is None else None)
        if reason is None and (isinstance(value, bool) or not isinstance(value, (int, float))
                               or not math.isfinite(value) or value < 0):
            reason = 'INVALID_NATIVE_PERSISTENCE'
        rows.append({'label': label, 'n_observations': counts[label],
                     'fraction_of_fitted_population': counts[label] / n,
                     'persistence': state(value, reason),
                     'hierarchy_node_index': state(selected[label]) if label in selected else
                        state(reason='ORIGINAL_HIERARCHY_NOT_RETAINED'),
                     'independent_unit_support': state(reason='NO_VERIFIED_INDEPENDENT_UNIT_SUPPORT')})
    persistence_summary = (_summary([r['persistence']['value'] for r in rows])
                           if all(r['persistence']['status'] == 'computed' for r in rows)
                           else state(reason='INCOMPLETE_SELECTED_CLUSTER_PERSISTENCE'))
    result = {'n_observations': n, 'support_unit': extracted['support_unit'],
              'n_selected_clusters': k, 'n_noise': counts[-1], 'noise_fraction': noise,
              'clusters': rows, 'persistence_distribution': persistence_summary,
              'observation_support_distribution': _summary([counts[i] for i in range(k)]),
              'distribution_weighting': 'one vote per selected cluster; no noise-cluster vote',
              'persistence_convention': convention,
              'discrete_structure': 'no_selected_clusters' if k == 0 else
                  'single_selected_cluster' if k == 1 else 'multiple_selected_clusters'}
    return state(result), hierarchy


def _summary_provider():
    try:
        from importlib.metadata import version
        from n4m._ffi import library_path
        from .storage import digest
        return state({'name': 'Methods summary ABI', 'version': version('nirs4all-methods'),
                      'binary_sha256': digest(Path(library_path()))})
    except (ImportError, OSError, RuntimeError):
        return state(reason='NATIVE_METHODS_SUMMARY_UNAVAILABLE')


def describe(report, *, setting_index=0):
    """Describe one frozen setting without mutating or refitting its source.

    Accept a hierarchy profile, a full structure report or an X-profile (including compact
    historical profiles). Independent-unit and resampling inference are outside
    this within-fit descriptor, even if a source has separate stability evidence.
    """
    # Also rejects non-JSON/nonfinite input before native calls or serialization.
    source_hash = fingerprint(report)
    extracted = _extract(report, setting_index)
    provider = {k: deepcopy(v) for k, v in (report.get('provider') or {}).items()
                if k in ('name', 'version', 'abi', 'binary_sha256')}
    evidence, hierarchy = _partition(extracted, provider)
    pca = extracted['representation']['pca']
    if pca:
        extracted['representation']['pca'] = {k: deepcopy(v) for k, v in pca.items()
            if k in ('backend', 'fit_partition', 'n_components', 'retained_variance_fraction',
                     'state_sha256', 'fit_x_sha256', 'preprocessing', 'solver')}
        if 'eigenvalues' in pca:
            extracted['representation']['pca']['n_components'] = len(pca['eigenvalues'])
    interpretation = 'The fitted population cannot be described from the retained evidence.'
    if evidence['status'] == 'computed':
        value = evidence['value']
        k = value['n_selected_clusters']
        interpretation = (
            'No discrete clusters selected under this configuration; all observations are noise. '
            'This does not establish continuity or low shortcut susceptibility.' if k == 0 else
            'One branch selected under this configuration; multiple distinct populations are not established.' if k == 1 else
            f'{k} density branches selected under this configuration; investigate sample organization without assigning experimental meaning.')
    result = {'schema_version': 1, 'protocol_version': PROTOCOL,
              'source': {'content_sha256': source_hash, 'protocol_version': report['protocol_version'],
                         'setting_index': setting_index, 'native_pointer': extracted['pointer']},
              'configuration': extracted['parameters'], 'representation': extracted['representation'],
              'provider': provider, 'summary_provider': _summary_provider(), 'selected_structure': evidence,
              'hierarchy': (state({'pointer': extracted['pointer'] + '/hierarchy',
                                  **hierarchy['value']}) if hierarchy and hierarchy['status'] == 'computed'
                            else hierarchy or state(reason='NATIVE_FIT_UNAVAILABLE')),
              'resampling_stability': state(reason='NOT_ASSESSED_BY_WITHIN_FIT_PERSISTENCE'),
              'separate_resampling_evidence_pointer': extracted['stability_pointer'],
              'finding': {'observation': interpretation, 'confidence': 'descriptive_within_fit',
                          'consequence': 'Useful for investigating organization within this fitted X population.',
                          'action': 'Inspect support, original hierarchy and acquisition metadata; assess resampling robustness separately.'},
              'limitations': [
                  'Persistence is normalized within-fit excess of mass, not a resampling statistic, probability or significance test.',
                  'Zero/infinite-density provider conventions can yield persistence 1 without strong empirical support.',
                  'Observation support is not effective independent sample size; repetitions may share specimens or references.',
                  'X-derived clusters are not genotypes, treatments, blocks or specimens; crossed factors need separate corroboration.',
                  'No biological validity, harmful shortcut reliance, supervised performance or validation split is established.',
                  'Euclidean Methods fit, row-order/tie sensitive; do not rank databases or representations by persistence.',
                  'Full-tree size at birth may differ from assigned support; a missing tree cannot be reconstructed from counts.',
                  'Resampling evidence, when separately referenced, retains its own design, denominator and limitations.']}
    validate_descriptor(result)
    return result


def validate_descriptor(value):
    from jsonschema import Draft202012Validator
    fingerprint(value)
    schema = json.loads(Path(__file__).with_name('selected-branch-persistence.v1.schema.json').read_text(encoding='utf-8'))
    Draft202012Validator(schema).validate(value)


def markdown(descriptor):
    validate_descriptor(descriptor)
    out = ['## Selected-branch persistence and support', '', descriptor['finding']['observation'], '',
           f"Representation: {descriptor['representation']['name']}; configuration: "
           + json.dumps(descriptor['configuration'], sort_keys=True) + '.', '']
    state_value = descriptor['selected_structure']
    if state_value['status'] == 'computed':
        value = state_value['value']
        out += [f"Fitted rows: {value['n_observations']} ({value['support_unit']}); noise: "
                f"{value['n_noise']} ({value['noise_fraction']:.3f}).", '',
                '| Label | Assigned rows | Fraction of all fitted rows | Within-fit persistence |',
                '|---|---:|---:|---:|']
        for row in value['clusters']:
            persistence = row['persistence']
            text = f"{persistence['value']:.6g}" if persistence['status'] == 'computed' else persistence['reason']
            out.append(f"| {row['label']} | {row['n_observations']} | {row['fraction_of_fitted_population']:.3f} | {text} |")
        out += ['', 'Distribution weighting: ' + value['distribution_weighting'] + '.',
                'Persistence convention: ' + value['persistence_convention'] + '.', '']
    else:
        out += [state_value['reason'], '']
    out += ['Resampling robustness: not assessed by this within-fit descriptor.', '',
            *['- ' + text for text in descriptor['limitations']], '']
    return '\n'.join(out)


def main(arguments=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('--setting-index', type=int, default=0)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(arguments)
    source = args.report.resolve()
    targets = (args.out.resolve(), args.out.with_suffix('.md').resolve())
    if (source in targets or len(set(targets)) != 2
            or any(target.exists() and target.samefile(source) for target in targets)
            or (all(t.exists() for t in targets) and targets[0].samefile(targets[1]))):
        raise ValueError('SIDECAR_MUST_NOT_OVERWRITE_SOURCE_OR_MARKDOWN')
    report = json.loads(source.read_text(encoding='utf-8'))
    descriptor = describe(report, setting_index=args.setting_index)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(descriptor, sort_keys=True, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    args.out.with_suffix('.md').write_text(markdown(descriptor), encoding='utf-8')


if __name__ == '__main__':
    main()
