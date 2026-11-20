"""Prospective provider identity boundary; numerical adversaries stay in v1/v2."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_preprocessing_parity_v3 as candidate


class CandidateBindingTests(unittest.TestCase):
    def test_candidate_binding_restores_historical_cohort_on_refusal(self):
        previous = candidate.rules.v1.VERSION
        with self.assertRaisesRegex(AssertionError, "PINNED_PROVIDER_AND_ABI_REQUIRED"):
            candidate.qualify(
                {"protocol_version": "domains.browser_preprocessing_sensitivity_wasm.v1",
                 "provider": {"version": previous}},
                {"protocol_version": "domains.browser_preprocessing_sensitivity_native.v1",
                 "provider_version": previous}, "unused")
        self.assertEqual(candidate.rules.v1.VERSION, previous)

    def test_different_candidate_abi_is_not_admitted(self):
        previous = candidate.rules.v1.VERSION
        with self.assertRaisesRegex(AssertionError, "PINNED_PROVIDER_AND_ABI_REQUIRED"):
            candidate.qualify(
                {"protocol_version": "domains.browser_preprocessing_sensitivity_wasm.v1",
                 "provider": {"version": "1.5.1+abi.2.20.0"}},
                {"protocol_version": "domains.browser_preprocessing_sensitivity_native.v1",
                 "provider_version": candidate.VERSION}, "unused")
        self.assertEqual(candidate.rules.v1.VERSION, previous)


if __name__ == "__main__":
    unittest.main()
