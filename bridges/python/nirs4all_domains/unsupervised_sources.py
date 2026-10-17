"""Source identity evidence, not a numerical or inferred biological grouping."""
from .dependence import state


def relation(a,b):
    """Only explicit namespaces and verified keys establish physical overlap."""
    namespace=a.get('physical_namespace')
    if namespace and namespace==b.get('physical_namespace') and a.get('original_keys_verified') and b.get('original_keys_verified'):
        shared=set(a.get('original_keys',())) & set(b.get('original_keys',()))
        return state({'source_relationship':'shared_verified_physical_namespace',
            'n_shared_physical_keys':len(shared),
            'physical_overlap':'verified_shared_objects' if shared else 'no_shared_verified_keys_in_declared_namespace',
            'biological_independence':state(reason='PHYSICAL_KEYS_DO_NOT_ESTABLISH_BIOLOGICAL_INDEPENDENCE')})
    if a.get('original_package_id') and a.get('original_package_id')==b.get('original_package_id'):
        return state({'source_relationship':'same_original_source_package',
            'physical_overlap':state(reason='ORIGINAL_PAIRED_PHYSICAL_KEYS_NOT_VERIFIED'),
            'biological_independence':state(reason='SHARED_SOURCE_PACKAGE_DOES_NOT_ESTABLISH_INDEPENDENCE')})
    citations=set(a.get('cited_study_references',())) & set(b.get('cited_study_references',()))
    if citations:
        return state({'source_relationship':'shared_cited_reference','references':sorted(citations),
            'physical_overlap':state(reason='SHARED_REFERENCE_IS_NOT_PAIRED_SPECIMEN_EVIDENCE'),
            'biological_independence':state(reason='STUDY_DEPENDENCIES_UNRESOLVED')},status='exploratory')
    return state(reason='CROSS_SOURCE_PHYSICAL_OVERLAP_NOT_IDENTIFIABLE',status='not_identifiable')
