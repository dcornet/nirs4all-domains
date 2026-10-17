"""Generate additive bank-v1 contracts; existing scientific schemas are untouched."""
import json
from pathlib import Path

from nirs4all_domains.registry import TASK_FIELDS, EXECUTION_FIELDS, PURPOSES


def obj(properties, required=None):
    return {"type":"object", "properties":properties, "required":list(properties) if required is None else required, "additionalProperties":False}


def main():
    string = {"type":"string", "minLength":1}
    digest = {"type":"string", "pattern":"^[0-9a-f]{64}$"}
    integer = {"type":"integer", "minimum":0}
    relative = {"type":"string", "pattern":r"^(?!/)(?!.*(?:^|/)\.\.(?:/|$))[^\\:]+$"}
    version = {"const":1}
    task = obj({"schema_version":version, "task_id":digest, **{k:string for k in TASK_FIELDS}})
    execution = obj({k:{} for k in EXECUTION_FIELDS})
    for k in ("input_sha256", "source_content_sha256", "split_folds_sha256", "controller_sha256"):
        execution["properties"][k] = digest
    state = {"oneOf":[obj({"status":{"enum":["computed", "exploratory"]}, "reason":{"type":"null"}, "value":{"not":{"type":"null"}}}),
                          obj({"status":{"enum":["inconclusive", "insufficient_information", "not_identifiable", "unavailable", "ineligible", "failed"]}, "reason":string, "value":{"type":"null"}})]}
    artifact = obj({"path":relative, "sha256":digest, "bytes":integer,
                    "retention":{"enum":["essential_evidence", "replay_checkpoint", "debug_archive"]}})
    storage = obj({"schema_version":version, "protocol_version":{"const":"domains.storage.v0.1"},
                   "execution_id":digest, "artifacts":{"type":"array", "items":artifact},
                   "cache_dependencies":{"type":"array", "items":obj({"content_sha256":digest, "bytes":integer, "provider":string,
                       "access":{"enum":["public", "requires_authorization"]}, "local_locator_key":string})},
                   "replay_grade":{"enum":["metadata_only", "reconstructed_from_cache", "requires_authorized_origin"]},
                   "measured_bytes":integer, "optional_archives":{"type":"array", "items":{"type":"object"}},
                   "limitations":{"type":"array", "items":string}})
    evidence = obj({"schema_version":version, "protocol_version":{"const":"domains.bank.v0.1"}, "evidence_id":digest,
                    "task_id":digest, "execution_id":digest, "task":task,
                    "contract":obj({"task":task, "execution":execution}),
                    "domain":{"enum":["real", "synthetic"]},
                    "status":{"enum":["computed", "exploratory", "inconclusive", "insufficient_information", "not_identifiable", "unavailable", "ineligible", "failed"]},
                    "reason":{"type":["string", "null"]},
                    "qualifications":{"type":"object", "additionalProperties":state},
                    "purposes":{"type":"array", "minItems":1, "uniqueItems":True, "items":{"enum":list(PURPOSES)}},
                    "scientific":{"type":"object"}, "limitations":{"type":"array", "minItems":1, "items":string}})
    evidence["allOf"] = [{"if":{"properties":{"status":{"enum":["computed", "exploratory"]}}},
                          "then":{"properties":{"reason":{"type":"null"}}},
                          "else":{"properties":{"reason":string}}}]
    suite = obj({"schema_version":version, "protocol_version":{"const":"domains.bank.v0.1"}, "suite_id":digest,
                 "purpose":{"enum":list(PURPOSES)}, "selection_basis":string,
                 "metric_contract":{"type":"object"}, "tasks":{"type":"array", "items":obj({"task_id":digest, "evidence_id":digest, "evidence_sha256":digest, "split_protocol":string})}})
    sidecar = obj({"schema_version":version, "integration_protocol":{"const":"domains.datasets_sidecar.v0.1"},
                   "dataset_id":string, "content_version":string, "task_id":digest, "qualification_protocol":string,
                   "evidence_sha256":digest, "evidence_ref":relative,
                   "purposes":{"type":"array", "items":{"enum":list(PURPOSES)}}})
    permission = obj({"status":{"enum":["allowed", "denied", "unknown"]}, "evidence":{"type":"array", "items":string}})
    fields = ("dataset_id", "catalog_revision", "content_version", "source_hashes", "scientific_reference", "source_id",
              "target", "identities", "dependencies", "factors", "representation", "split", "independent_units",
              "missing_fields", "budget", "review_evidence")
    admission = obj({"schema_version":version, "protocol_version":{"const":"domains.admission.v0.1"}, "admission_id":digest,
                     "specification":obj({**{k:{} for k in fields}, "permissions":obj({k:permission for k in
                         ("access", "local_analysis", "publish_statistics", "redistribute_raw")})}),
                     "status":{"enum":["admitted", "pending"]}, "reasons":{"type":"array", "items":string}, "selection_basis":string})
    admission["allOf"] = [{"if":{"properties":{"status":{"const":"admitted"}}}, "then":{"properties":{"reasons":{"maxItems":0}}},
                           "else":{"properties":{"reasons":{"minItems":1}}}}]
    failed_design = obj({"status":{"const":"failed"}, "reason":string, "value":{"type":"null"},
                         "failed_fold_id":string, "completed_folds":{"type":"array"}, "partial_oof_count":integer})
    design_state = {"anyOf":[state, failed_design]}
    comparison = obj({"protocol_version":{"const":"domains.multifamily.v0.1"}, "task_id":digest, "parent_task_id":digest,
                      "evaluation_id":digest, "specification":{"type":"object"}, "designs":{"type":"object", "minProperties":1, "additionalProperties":design_state},
                      "wall_seconds":{"type":"number", "minimum":0}, "memory":{"type":"object"}, "expected_fit_upper":integer,
                      "source_fingerprints":{"type":"object"}, "test_target_accessed":{"const":False}})
    adaptive = {"type":"object", "required":["schema_version","protocol_version","record_id","dataset_id","source_id","identity_evidence","levels","universal_shortcut_score"],
        "properties":{"schema_version":version,"protocol_version":{"const":"domains.adaptive_structure.v0.1"},"record_id":digest,
            "dataset_id":string,"source_id":string,"identity_evidence":{"enum":["verified_physical_identity","declared_but_unverified_identity","observation_identity_only","identity_unavailable"]},
            "levels":obj({k:state for k in ("X0","X1","XY","XYM","MODEL")}),"universal_shortcut_score":{"type":"null"}},"additionalProperties":True}
    repeated = {"type":"object", "required":["evaluation_id","models","test_target_accessed"],
        "properties":{"evaluation_id":digest,"test_target_accessed":{"const":False},"models":{"type":"object","minProperties":1,
            "additionalProperties":obj({"designs":{"type":"array","minItems":3,"maxItems":3,"items":design_state},"refit_variation":state})}},"additionalProperties":True}
    for name, schema in (("benchmark-task",task), ("qualification-evidence",evidence), ("storage-manifest",storage), ("benchmark-suite",suite), ("datasets-sidecar",sidecar), ("task-admission",admission), ("multifamily-result",comparison), ("adaptive-coverage",adaptive), ("repeated-design-result",repeated)):
        schema = {"$schema":"https://json-schema.org/draft/2020-12/schema", "$id":f"https://dcornet.github.io/nirs4all-domains/schemas/{name}.v1.schema.json", **schema}
        data = json.dumps(schema, indent=2, sort_keys=True)+"\n"
        for root in (Path("schemas"), Path("bridges/python/nirs4all_domains")):
            (root/f"{name}.v1.schema.json").write_text(data, encoding="utf-8")


if __name__ == "__main__":
    main()
