"""Guards around delegated local ingestion; no private data required in CI."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

spec = importlib.util.spec_from_file_location("local_pilot", Path(__file__).resolve().parents[2] / "scripts/run_local_pilot.py")
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)


class PreparationGuards(unittest.TestCase):
    def test_existing_pilot_reports_are_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            sentinel = root / "report.json"
            sentinel.write_text("preserve previous result")
            args = ["run_local_pilot.py", "--out", str(root)]
            for name in ("converter", "raw-zip", "descriptor", "binary", "methods-library"):
                args += [f"--{name}", "unused"]
            with patch("sys.argv", args), self.assertRaisesRegex(ValueError, "previous results are preserved"):
                pilot.main()
            self.assertEqual(sentinel.read_text(), "preserve previous result")

    def test_unreviewed_converter_is_never_executed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            converter = root / "converter.py"
            converter.write_text("raise AssertionError('must not execute')")
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                pilot.prepare(converter, "0" * 64, root / "missing.zip", root / "descriptor.yaml", root / "stage")
            self.assertFalse((root / "stage").exists())

    def test_existing_staging_tree_is_never_replaced(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            converter = root / "converter.py"
            converter.write_text("raise AssertionError('must not execute')")
            stage = root / "stage"
            stage.mkdir()
            sentinel = stage / "preserve.txt"
            sentinel.write_text("preserve")
            with self.assertRaisesRegex(ValueError, "new directory"):
                pilot.prepare(converter, pilot.digest(converter), root / "missing.zip", root / "descriptor.yaml", stage)
            self.assertEqual(sentinel.read_text(), "preserve")

    def test_archive_path_escape_is_rejected_before_converter_load(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            converter = root / "converter.py"
            converter.write_text("raise AssertionError('must not execute')")
            archive = root / "input.zip"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("../escape.txt", "bad")
            with self.assertRaisesRegex(ValueError, "escapes staging"):
                pilot.prepare(converter, pilot.digest(converter), archive, root / "descriptor.yaml", root / "stage")
            self.assertFalse((root / "escape.txt").exists())
