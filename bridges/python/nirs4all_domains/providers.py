"""Published provider versions qualified for new native fits.

Historical evidence keeps the provider versions it recorded; replaying it
requires the matching historical Domains commit and providers.
"""
from __future__ import annotations

import hashlib
from importlib.metadata import version
from pathlib import Path

QUALIFIED_NATIVE = {"dag-ml": "0.3.44", "nirs4all-methods": "1.3.13"}
QUALIFIED_NIRS4ALL = "1.4.14"


def native_qualified():
    return all(version(name) == expected for name, expected in QUALIFIED_NATIVE.items())


def frozen_transport_digest(path):
    """SHA-256 of a qualified native transport source as frozen in alpha.13.

    Preflight 0.1.6 turned ``ProviderError`` into a struct, so the frozen
    ``|e| e.0)`` accessor now reads ``|e| e.reason)``. Mapping only that token
    back proves that no other byte of the qualified source changed.
    """
    source = Path(path).read_bytes().replace(b"|e| e.reason)", b"|e| e.0)")
    return hashlib.sha256(source).hexdigest()
