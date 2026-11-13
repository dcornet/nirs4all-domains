"""The independent analytical oracle must not inherit platform-relative tolerance."""
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[2] / "scripts/check_browser_parity.py"
spec = importlib.util.spec_from_file_location("browser_parity_checker", path)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class BrowserParityToleranceTests(unittest.TestCase):
    def test_agreeing_backends_do_not_substitute_for_an_analytical_expectation(self):
        checker.near(1 + 5e-10, 1, "platform")
        with self.assertRaises(AssertionError):
            checker.analytical_near(1 + 5e-10, 1, "independent-expectation")

    def test_analytical_tolerance_has_no_relative_escape_at_large_scale(self):
        checker.near(1e8 + 1e-4, 1e8, "platform")
        with self.assertRaises(AssertionError):
            checker.analytical_near(1e8 + 1e-4, 1e8, "independent-expectation")

    def test_analytical_finite_values_inside_the_frozen_bound_pass(self):
        checker.analytical_near(1 + 5e-11, 1, "inside-bound")
        for value in (float("nan"), float("inf"), -float("inf")):
            with self.subTest(value=value), self.assertRaises(AssertionError):
                checker.analytical_near(value, value, "nonfinite")


if __name__ == "__main__":
    unittest.main()
