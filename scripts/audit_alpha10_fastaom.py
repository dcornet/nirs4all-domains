"""Record the exact optional entry-point deployment and distinct native facade."""
import importlib.metadata as metadata
import inspect
import json
from pathlib import Path

from nirs4all_domains.storage import atomic_json, digest, tree_bytes


def main():
    import nirs4all
    from nirs4all.operators.models import FastAOMPLSRidge, FastAOMConfig
    from n4m.model_selection import FastAOMPLSRegressor, FastAOMRidgeRegressor
    from n4m._ffi import lib
    from packaging.requirements import Requirement
    source = Path(nirs4all.__file__).parent
    root = Path(".audit/alpha10")
    original = json.loads((root/"nirs4all-source.json").read_text())
    checked = []
    for name, record in original["files"].items():
        if not name.startswith("nirs4all/") or not name.endswith(".py"): continue
        actual = source/Path(name).relative_to("nirs4all")
        if digest(actual) != record["sha256"]: raise ValueError("PUBLISHED_FASTAOM_SOURCE_DIFFERS")
        checked.append(name)
    requirements = metadata.requires("nirs4all")
    missing = []
    for text in requirements:
        req = Requirement(text)
        if req.marker and not req.marker.evaluate({"extra": ""}): continue
        try:
            installed = metadata.version(req.name)
            if req.specifier and installed not in req.specifier: missing.append({"requirement": text, "installed": installed})
        except metadata.PackageNotFoundError:
            missing.append({"requirement": text, "installed": None})
    result = {"protocol_version": "domains.alpha10.optional_provider_audit.v0.1",
        "repository": "https://github.com/GBeurier/nirs4all", "revision": original["revision"],
        "published_version": metadata.version("nirs4all"), "wheel_sha256": digest(root/"packages/nirs4all-1.4.10-py3-none-any.whl"),
        "public_import": "nirs4all.operators.models.FastAOMPLSRidge", "constructor_signature": str(inspect.signature(FastAOMPLSRidge)),
        "config_signature": str(inspect.signature(FastAOMConfig)), "implementation": "Python/NumPy/SciPy; sklearn estimator interface, upstream linear algebra",
        "source_files_matching_wheel": checked, "source_file_hashes": original["files"],
        "full_distribution_requirements": requirements, "requirements_absent_from_entrypoint_test_environment": missing,
        "deployment_scope": "Isolated no-deps wheel plus tested public-entry import closure; complete nirs4all application not installed or qualified. No monkeypatch or modified upstream source.",
        "added_entrypoint_dependencies": {p: metadata.version(p) for p in ("PyWavelets", "pybaselines", "polars", "polars-runtime-32")},
        "isolated_runtime_bytes": tree_bytes([root/"runtime"]),
        "serialization": "Own in-memory pickle protocol 5; source/version bound; timing metadata excluded; prediction replay qualified at atol=rtol=1e-9. No portable cross-version model format claimed.",
        "selection": "Fresh instance in every native group-safe inner/outer scope. cv_n_components disabled; singleton lambdas prevent row-LOOCV/GCV hyperparameter selection.",
        "randomness": "Explicit random_state=17; inspected low-rank implementation uses deterministic full thin SVD, then truncates. Seed is reserved/unused there.",
        "cost_bounds": {"features_tested": [32, 141], "depth": 1, "chains": 9, "bases": 2, "screened_pairs_per_fit": 18, "finalists": 8, "rank_cap": 32},
        "native_methods_facades": {"PLS": str(inspect.signature(FastAOMPLSRegressor)), "Ridge": str(inspect.signature(FastAOMRidgeRegressor)),
            "fit_symbol_available": hasattr(lib, "n4m_model_selection_aom_calibration_fit"),
            "predict_symbol_available": hasattr(lib, "n4m_model_selection_aom_calibration_predict"),
            "source": "Methods bindings/python/src/n4m/model_selection/aom_calibration.py; docs/methods/aom_calibration.md",
            "protocols": ["fast-pls-branch-cv-v1", "fast-ridge-branch-cv-v1"],
            "separate_semantics": "strict10 bank, explicit branch-CV and fold_ids; different from donor hard chain / sparse MKR",
            "local_scientific_execution": "not performed; source/binding/symbol evidence is availability, not qualification"},
        "TabPFN": "deferred; no model/weights/GPU acquisition or fit"}
    atomic_json("docs/audit/alpha10-fastaom-provider.json", result)
    print(json.dumps({"source_files_matching_wheel": len(checked), "entrypoint_import": "passed", "whole_package_missing_requirements": len(missing), "runtime_bytes": result["isolated_runtime_bytes"]}))


if __name__ == "__main__": main()
