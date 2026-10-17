"""Validate public frozen alpha.9 contracts without acquiring source data."""
import json
from pathlib import Path

from nirs4all_domains.admission import verify_admission
from nirs4all_domains.bank import read, schema_check
from nirs4all_domains.registry import verify_evidence, verify_storage, reject_heavy_payload
from nirs4all_domains.storage import fingerprint


def main():
    root=Path("docs/benchmarks/alpha9")
    storage=read(root/"storage.json");schema_check(storage,"storage-manifest");verify_storage(storage,root)
    admission=read(root/"perten-admission.json");schema_check(admission,"task-admission");verify_admission(admission)
    evidence=read(root/"perten-evidence.json");schema_check(evidence,"qualification-evidence");verify_evidence(evidence)
    old=read("docs/benchmarks/alpha8/ecosis-evidence.json");verify_evidence(old)
    records={r["task_id"]:r for r in (old,evidence)}
    for file in root.glob("*suite.json"):
        suite=read(file);schema_check(suite,"benchmark-suite")
        assert suite["suite_id"]==fingerprint({k:v for k,v in suite.items() if k!="suite_id"})
        for task in suite["tasks"]:
            assert task["evidence_sha256"]==fingerprint(records[task["task_id"]])
        if suite["purpose"]=="candidate_low_structural_dependence":assert not suite["tasks"]
    assert evidence["domain"]=="real" and admission["status"]=="admitted"
    assert evidence["scientific"]["deep"]["n_samples"]==359
    assert evidence["scientific"]["deep"]["n_components"]==17
    assert all(f["effective_attempts"]==0 for f in evidence["scientific"]["deep"]["interventions"])
    assert len(read(root/"perten-family-comparison.json")["designs"])==3
    def inspect(value):
        if isinstance(value,dict):
            if "test_target_accessed" in value:assert value["test_target_accessed"] is False
            for child in value.values():inspect(child)
        elif isinstance(value,list):
            for child in value:inspect(child)
    for file in root.glob("*.json"):
        value=json.loads(file.read_text(),parse_constant=lambda s:(_ for _ in ()).throw(ValueError(s)))
        reject_heavy_payload(value);inspect(value)
    print("alpha.9: admission, finite compact evidence, suites, artifact digests and retained-target invariants verified")


if __name__=="__main__":main()
