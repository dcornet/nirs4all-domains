"""Read-only inventory; writes its report only after measuring all inputs.

No traversal of junctions/symlinks. Byte identity is not reuse authorization.
Machine paths and the file-level inventory must remain outside Git.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import time


def allocated(path, info):
    if os.name != "nt":
        return getattr(info, "st_blocks", (info.st_size + 511) // 512) * 512
    class StandardInfo(ctypes.Structure):
        _fields_ = [("allocation",ctypes.c_longlong),("end",ctypes.c_longlong),
                    ("links",ctypes.c_ulong),("delete_pending",ctypes.c_ubyte),("directory",ctypes.c_ubyte)]
    create = ctypes.windll.kernel32.CreateFileW
    create.argtypes = [ctypes.c_wchar_p,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_void_p,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_void_p]
    create.restype = ctypes.c_void_p
    handle = create(str(path),0x80,7,None,3,0,None)
    if handle == ctypes.c_void_p(-1).value:
        return None
    try:
        result = StandardInfo()
        fn = ctypes.windll.kernel32.GetFileInformationByHandleEx
        fn.argtypes = [ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p,ctypes.c_ulong]
        return result.allocation if fn(handle,1,ctypes.byref(result),ctypes.sizeof(result)) else None
    finally:
        close = ctypes.windll.kernel32.CloseHandle
        close.argtypes = [ctypes.c_void_p]
        close(handle)


def artifact_class(path):
    name = str(path).lower()
    if path.suffix in (".zip", ".gz", ".zst", ".whl"):
        return "archive"
    if path.suffix == ".parquet":
        return "canonical_parquet"
    if "task" in path.name and path.suffix == ".json":
        return "task_matrix"
    if path.suffix == ".csv":
        return "csv_intermediate_or_source"
    if "bootstrap" in name or "stability" in name:
        return "bootstrap_or_stability"
    if "permutation" in name or "intervention" in name:
        return "intervention"
    if path.suffix in (".n4me", ".bin") or "artifact" in name:
        return "model_artifact"
    if "checkpoint" in name:
        return "checkpoint"
    if path.suffix == ".json":
        return "report_or_metadata"
    return "other"


def scan(roots, hash_duplicates=True):
    """Globally deduplicate file identities, even for overlapping input roots.

    Logical path totals are reported separately from unique allocated totals.
    Does not open files for writing or change permissions/access-time policy.
    """
    start = time.monotonic()
    files, links, errors, directories = [], [], [], set()
    seen_paths, owners = set(), {}
    root_records = []
    for label, base in roots:
        base = Path(base).absolute()
        usage = shutil.disk_usage(base if base.exists() else base.anchor)
        filesystem = None
        if os.name == "nt":
            fs_name = ctypes.create_unicode_buffer(64)
            fn = ctypes.windll.kernel32.GetVolumeInformationW
            fn.argtypes = [ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_ulong,ctypes.c_void_p,
                           ctypes.c_void_p,ctypes.c_void_p,ctypes.c_wchar_p,ctypes.c_ulong]
            if fn(base.anchor,None,0,None,None,None,fs_name,64):
                filesystem = fs_name.value
        root_records.append(dict(label=label, path=str(base), exists=base.exists(),
                                 volume_total=usage.total, volume_free=usage.free, filesystem=filesystem))
        if not base.exists():
            continue
        pending = [base]
        while pending:
            folder = pending.pop()
            try:
                for entry in sorted(os.scandir(folder), key=lambda e: e.name):
                    path = Path(entry.path)
                    key = os.path.normcase(str(path.absolute()))
                    if key in seen_paths:
                        continue
                    seen_paths.add(key)
                    # DirEntry.stat() on Windows can report st_ino=0. Path.stat
                    # obtains the actual file identity needed for hardlinks.
                    info = path.stat(follow_symlinks=False)
                    if entry.is_symlink() or getattr(info, "st_file_attributes", 0) & 0x400:
                        links.append(dict(path=str(path), reason="reparse_point_not_followed"))
                    elif stat.S_ISDIR(info.st_mode):
                        directories.add(key)
                        pending.append(path)
                    elif stat.S_ISREG(info.st_mode):
                        identity = (info.st_dev, info.st_ino) if info.st_ino else (key,)
                        first = owners.setdefault(identity, str(path))
                        files.append(dict(root=label, path=str(path), relative=path.relative_to(base).as_posix(),
                                          bytes=info.st_size, allocated_bytes=allocated(path, info),
                                          mtime_ns=info.st_mtime_ns, hardlink_owner=first,
                                          unique=first == str(path), artifact_class=artifact_class(path)))
            except OSError as exc:
                errors.append(dict(path=str(folder), error=type(exc).__name__))
    totals = defaultdict(lambda: dict(bytes=0, unique_allocated_bytes=0, files=0, allocation_unknown_files=0))
    for item in files:
        rel = Path(item["relative"])
        keys = [item["root"], f"{item['root']}/{rel.parts[0]}" if len(rel.parts) > 1 else f"{item['root']}/<root files>"]
        keys += [f"{item['root']}/{Path(*rel.parts[:i]).as_posix()}" for i in range(2, len(rel.parts))]
        if item["root"] == "workspace" and rel.parts[0] == "results":
            keys.append("results-class/" + item["artifact_class"])
        keys.append("extension/" + (rel.suffix.lower() or "<none>"))
        for key in keys:
            target = totals[key]
            target["bytes"] += item["bytes"]
            target["files"] += 1
            if item["unique"]:
                target["unique_allocated_bytes"] += item["allocated_bytes"] or 0
                target["allocation_unknown_files"] += item["allocated_bytes"] is None
    duplicates = []
    if hash_duplicates:
        by_size = defaultdict(list)
        for item in files:
            # Scientific outputs only. Full inventory accounts for tools without
            # needlessly hashing several GB of compiler caches.
            if item["root"] == "workspace" and item["relative"].startswith("results/") and item["bytes"]:
                by_size[item["bytes"]].append(item)
        for size, group in by_size.items():
            if len(group) < 2:
                continue
            hashes = defaultdict(list)
            for item in group:
                h = hashlib.sha256()
                with open(item["path"], "rb") as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b""):
                        h.update(block)
                hashes[h.hexdigest()].append(item["path"])
            duplicates.extend(dict(sha256=h, bytes_each=size, paths=paths,
                                   possible_logical_savings=size * (len(paths)-1),
                                   reuse_authorized=False)
                              for h, paths in hashes.items() if len(paths) > 1)
    return dict(schema_version=1, measured_utc=datetime.now(timezone.utc).isoformat(),
                roots=root_records, files=files, links=links, errors=errors,
                totals=dict(sorted(totals.items())),
                largest_files=sorted(files, key=lambda x: -x["bytes"])[:30],
                duplicate_scientific_bytes=sorted(duplicates, key=lambda x: -x["possible_logical_savings"]),
                duration_seconds=time.monotonic()-start,
                limitations=["Directory/MFT overhead excluded; allocated bytes are file allocations.",
                             "Reparse points skipped; their destinations are not charged twice.",
                             "Hardlink identity counted once globally; logical path totals can overlap.",
                             "Classification from artifact paths; embedded JSON phases need separate inspection.",
                             "Read access can update OS access-time metadata; no content/mtime writes."])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--root", default=".", type=Path)
    args = parser.parse_args()
    roots = [("workspace", args.root)]
    if os.name == "nt":
        local = Path(os.environ["LOCALAPPDATA"])
        roots += [("datasets_default_cache", local / "nirs4all-datasets/cache"),
                  ("pip_cache", local / "pip/Cache")]
    else:
        roots += [("datasets_default_cache", Path.home() / ".cache/nirs4all-datasets"),
                  ("pip_cache", Path.home() / ".cache/pip")]
    report = scan(roots)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
    print(json.dumps(dict(roots=report["roots"],
                          top_level={k:v for k,v in report["totals"].items() if k.count("/") <= 1 and not k.startswith("extension/")},
                          duplicates_bytes=sum(x["possible_logical_savings"] for x in report["duplicate_scientific_bytes"]),
                          errors=report["errors"], seconds=report["duration_seconds"]), indent=2))


if __name__ == "__main__":
    main()
