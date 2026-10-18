"""Outgoing Git/package surfaces: exact rosters plus taint, never regex alone."""
from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
import subprocess
import tarfile
import zipfile

from .disclosure import validate_outgoing
from .privacy import fail


def git_surfaces(root, *, staged=False):
    """Inspect actual index blobs when staged=True, not their worktree substitutes."""
    root=Path(root)
    names=subprocess.check_output(['git','ls-files','-z'],cwd=root).split(b'\x00')
    for name in filter(None,names):
        path=name.decode('utf-8')
        parts=PurePosixPath(path).parts
        if any(p in {'.audit','.venv','.tools','results','__pycache__','.env','keys','identities'} for p in parts):
            fail('OUTGOING_RESTRICTED_PATH')
        if staged:
            data=subprocess.check_output(['git','cat-file','blob',':'+path],cwd=root)
        else:
            local=root/path
            if local.is_symlink() or not local.is_file():
                fail('OUTGOING_GIT_SURFACE_UNAVAILABLE')
            data=local.read_bytes()
        yield path,data


def audit_surfaces(surfaces, roster, *, sensitive_literals=()):
    """Roster must be built independently from reviewed public provenance.

    New files, renamed files and changed bytes need a new exact reviewed entry.
    No report may authorize itself using a public visibility label.
    """
    allowed={}
    for record in roster.values():
        allowed.setdefault(record['kind'],set()).add(record['sha256'])
    count=0
    for path,data in surfaces:
        if path not in roster:
            fail('OUTGOING_SURFACE_NOT_REVIEWED')
        provenance=roster[path]
        validate_outgoing(path,data,provenance=provenance,sensitive_literals=sensitive_literals,
                          authorized_public_hashes=allowed)
        count+=1
    return {'status':'verified','outgoing_surfaces':count,'sensitive_values_printed':False}


def package_surfaces(path, *, maximum_unpacked_bytes=16*1024*1024):
    """No extraction. Deny traversal, links, duplicate names and oversized input."""
    total=0;seen=set()
    def check(name,size):
        nonlocal total
        parsed=PurePosixPath(name)
        if not name or parsed.is_absolute() or '..' in parsed.parts or '\\' in name or ':' in name or name in seen:
            fail('PACKAGE_MEMBER_PATH_INVALID')
        seen.add(name);total+=size
        if size<0 or total>maximum_unpacked_bytes:
            fail('PACKAGE_UNPACKED_BYTE_BOUND_EXCEEDED')
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            for member in archive.infolist():
                if member.is_dir():continue
                if (member.external_attr>>16)&0o170000==0o120000:
                    fail('PACKAGE_LINK_FORBIDDEN')
                check(member.filename,member.file_size)
                yield member.filename,archive.read(member)
    elif tarfile.is_tarfile(path):
        with tarfile.open(path,'r:*') as archive:
            for member in archive:
                if member.isdir():continue
                if not member.isfile():fail('PACKAGE_LINK_FORBIDDEN')
                check(member.name,member.size)
                yield member.name,archive.extractfile(member).read()
    else:
        fail('PACKAGE_FORMAT_NOT_ALLOWED')


def public_record(data, kind):
    return {'visibility':'public','sha256':hashlib.sha256(data).hexdigest(),'kind':kind}
