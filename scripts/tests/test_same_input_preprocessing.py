"""Adversarial identity binding for the diagnostic; no provider or numeric substitute."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import diagnose_same_input_preprocessing as diagnostic


class SameInputBinding(unittest.TestCase):
    def setUp(self):
        self.request = {"protocol_version": "domains.f43_same_input_requests.v1", "synthetic_only": True,
                        "provider_version": diagnostic.parity.VERSION, "requests": [
                            {"id": "fixed", "operation": "pca", "request": {"matrix": [[1.0]]},
                             "f64_fields": {"matrix": [[struct.pack(">d", 1.0).hex()]]}}]}
        self.raw = json.dumps(self.request).encode()
        self.wasm = {"protocol_version": "domains.f43_same_input_wasm.v1", "provider_version": diagnostic.parity.VERSION,
                     "input_sha256": hashlib.sha256(self.raw).hexdigest(), "new_real_scientific_fits": 0,
                     "results": [{"id": "fixed", "operation": "pca", "input_f64_le_sha256":
                                  {"matrix": hashlib.sha256(struct.pack("<d", 1.0)).hexdigest()}}]}
        self.native = copy.deepcopy(self.wasm)
        self.native["protocol_version"] = "domains.f43_same_input_native.v1"

    def test_exact_bound_inputs_are_accepted(self):
        diagnostic.verify_phase(self.wasm, self.native, self.raw)

    def test_matching_backend_lies_do_not_replace_expected_input_hash(self):
        for artifact in (self.wasm, self.native):
            artifact["results"][0]["input_f64_le_sha256"]["matrix"] = "0" * 64
        with self.assertRaisesRegex(AssertionError, "EXACT_IEEE_INPUT_REQUIRED"):
            diagnostic.verify_phase(self.wasm, self.native, self.raw)

    def test_changed_request_bytes_are_refused(self):
        with self.assertRaisesRegex(AssertionError, "EXACT_REQUEST_FILE_REQUIRED"):
            diagnostic.verify_phase(self.wasm, self.native, self.raw + b" ")

    def test_changed_operation_is_refused(self):
        self.native["results"][0]["operation"] = "factor_descriptive"
        with self.assertRaisesRegex(AssertionError, "EXACT_IEEE_INPUT_REQUIRED"):
            diagnostic.verify_phase(self.wasm, self.native, self.raw)

    def test_duplicate_or_replaced_identity_is_refused(self):
        self.native["results"][0]["id"] = "different population"
        with self.assertRaisesRegex(AssertionError, "REQUEST_ORDER_CHANGED"):
            diagnostic.verify_phase(self.wasm, self.native, self.raw)

    def test_unqualified_owner_or_real_fit_is_refused(self):
        self.native["provider_version"] = "newer-is-not-qualified"
        with self.assertRaisesRegex(AssertionError, "PINNED_OWNER_REQUIRED"):
            diagnostic.verify_phase(self.wasm, self.native, self.raw)


if __name__ == "__main__":
    unittest.main()
