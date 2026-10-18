"""Explicit original-file bindings; a matching basename is never a join."""
from pathlib import Path
import math
import re

from .original_keys import keyed_equivalence
from .storage import digest


def manifest_locator(row, dataset_id, allowed_roots):
    """Validate the declaration without reading original content.

    Generated conversion manifests are locator evidence, not proof of specimen
    independence, assay ownership, units or original-study provenance.
    """
    if row.get('dataset_id') != dataset_id:
        raise ValueError('MANIFEST_SOURCE_IDENTITY_CONTRADICTION')
    locator = row.get('local_path_if_any', '').strip()
    if not locator:
        raise ValueError('EXPLICIT_ORIGINAL_LOCAL_LOCATOR_REQUIRED')
    path = Path(locator)
    roots = [Path(root).resolve() for root in allowed_roots]
    if not path.is_absolute():
        matches = {root/path for root in roots if (root/path).is_file()}
        if len(matches) != 1:
            raise ValueError('UNAMBIGUOUS_DECLARED_RELATIVE_LOCATOR_REQUIRED')
        path = matches.pop()
    resolved = path.resolve()
    if not any(resolved.is_relative_to(root) for root in roots):
        raise ValueError('ORIGINAL_LOCATOR_OUTSIDE_ADMITTED_ROOT')
    if not resolved.is_file():
        raise ValueError('DECLARED_ORIGINAL_NOT_LOCALLY_AVAILABLE')
    if path.is_symlink() or any(q.is_symlink() or getattr(q.lstat(), 'st_file_attributes', 0) & 0x400
                                for q in (path, *path.parents) if q.exists()):
        raise ValueError('ORIGINAL_LOCATOR_FILESYSTEM_LINK')
    if resolved.name != row.get('file_name'):
        raise ValueError('MANIFEST_DECLARED_FILENAME_CONTRADICTION')
    expected = row.get('sha256_or_partial_hash', '').strip().lower()
    if expected.startswith('sha256:'):
        expected = expected[len('sha256:'):]
    if not re.fullmatch('[0-9a-f]{64}', expected):
        raise ValueError('DECLARED_FULL_ORIGINAL_CONTENT_HASH_REQUIRED')
    return resolved, expected


def manifest_file(row, dataset_id, allowed_roots):
    """Bind exact content only after source/locator/scope preflight."""
    resolved, expected = manifest_locator(row, dataset_id, allowed_roots)
    if digest(resolved) != expected:
        raise ValueError('MANIFEST_ORIGINAL_CONTENT_CONTRADICTION')
    return resolved


def required_keyed_equivalence(original, canonical, *, key, columns):
    """Both absent fields must not compare as a successful correspondence."""
    if not original or not canonical or not columns:
        raise ValueError('NONEMPTY_ORIGINAL_CORRESPONDENCE_REQUIRED')
    for rows in (original, canonical):
        for row in rows:
            def present(field):
                value = row.get(field)
                return field in row and value is not None and not (isinstance(value, str) and not value.strip()) and not (
                    isinstance(value, (int, float)) and not math.isfinite(value))
            if any(not present(field) for field in [key, *columns]):
                raise ValueError('COMPLETE_EXPLICIT_ORIGINAL_FIELDS_REQUIRED')
    return keyed_equivalence(original, canonical, key=key, columns=columns)
