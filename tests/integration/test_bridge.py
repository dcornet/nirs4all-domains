import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from nirs4all_domains.dataset import task_from_dataset
from nirs4all_domains.batch import run_campaign

ROOT = Path(__file__).resolve().parents[2]


class Dataset:
    id = "fake-catalog"
    descriptor = SimpleNamespace(versions=SimpleNamespace(content="1.0.0"),
        sources=[SimpleNamespace(source_id="A", axis_unit="nm")])
    split_data = pd.DataFrame({"sample_id": ["b", "a"], "partition": ["held", "dev"]})

    def sources(self): return ["A", "B"]
    def x(self, source):
        if source != "A": raise AssertionError("Unselected source read")
        return np.array([[1., 2.], [3., 4.]])
    def wavelengths(self, source): return np.array([1100., 1200.])
    def sample_ids(self, source): return np.array(["a", "b"])
    def observation_ids(self, source): return np.array(["oa", "ob"])
    def split(self, name): return self.split_data
    def metadata(self): return pd.DataFrame({"sample_id": ["b", "a"], "site": ["B", "A"]})
    def y(self, target): return pd.DataFrame({"sample_id": ["b", "a"], "y": [999., 10.]})


class BridgeTests(unittest.TestCase):
    def config(self):
        return {"source_id": "A", "target_id": "y", "content_version": "1.0.0", "split_id": "original",
                "partition_labels": {"dev": "train", "held": "test"}, "sample_identity_confirmed": True,
                "signal_unit": "absorbance"}

    @patch("nirs4all_domains.dataset.version", return_value="0.3.11")
    def test_identity_joins_and_test_y_omitted(self, _):
        task = task_from_dataset(Dataset(), self.config())
        self.assertEqual(task["observations"][0]["y"], 10.)
        self.assertEqual(task["observations"][0]["metadata"]["site"], "A")
        self.assertNotIn("y", task["observations"][1])
        self.assertEqual(task["observations"][1]["partition"], "test")

    @patch("nirs4all_domains.dataset.version", return_value="0.3.11")
    def test_version_and_identity_assumption_required(self, _):
        config = self.config(); config["content_version"] = "2.0.0"
        with self.assertRaisesRegex(ValueError, "version mismatch"):
            task_from_dataset(Dataset(), config)
        config = self.config(); config["sample_identity_confirmed"] = False
        with self.assertRaisesRegex(ValueError, "Physical identities"):
            task_from_dataset(Dataset(), config)

    @patch("nirs4all_domains.dataset.version", return_value="0.3.11")
    def test_absent_ambiguous_or_unknown_split_rejected(self, _):
        for frame in [None, pd.DataFrame({"sample_id": ["a", "a"], "partition": ["dev", "held"]}),
                      pd.DataFrame({"sample_id": ["a", "b"], "partition": ["dev", "mystery"]})]:
            ds = Dataset(); ds.split_data = frame
            with self.assertRaises(ValueError): task_from_dataset(ds, self.config())

    @patch("nirs4all_domains.dataset.version", return_value="0.3.11")
    def test_post_evaluation_explicit(self, _):
        config = self.config(); config["audit_mode"] = "post_evaluation"
        task = task_from_dataset(Dataset(), config)
        self.assertEqual(task["observations"][1]["y"], 999.)

    @patch("nirs4all_domains.dataset.version", return_value="0.3.11")
    def test_explicit_exclusion_preserves_denominators_and_hides_target(self, _):
        ds = Dataset()
        ds.split_data = pd.DataFrame({"sample_id": ["a", "b"], "partition": ["dev", "validation"]})
        config = self.config()
        config["partition_labels"] = {"dev": "train", "validation": "exclude"}
        config["target_unit"] = "mg/tablet"
        task = task_from_dataset(ds, config)
        self.assertEqual(len(task["observations"]), 1)
        self.assertEqual(task["target_unit"], "mg/tablet")
        self.assertEqual(json.loads(task["provenance"]["native_partition_observation_counts"]), {"dev": 1, "validation": 1})
        self.assertEqual(json.loads(task["provenance"]["excluded_observation_ids"]), ["ob"])
        self.assertEqual(task["observations"][0]["y"], 10.)

    @patch("nirs4all_domains.dataset.version", return_value="0.3.11")
    def test_declared_missing_target_and_reserved_provenance_fail(self, _):
        ds = Dataset()
        ds.y = lambda _target: None
        with self.assertRaisesRegex(ValueError, "Requested target unavailable"):
            task_from_dataset(ds, self.config())
        config = self.config()
        config["provenance"] = {"datasets": "forged"}
        with self.assertRaisesRegex(ValueError, "Reserved provenance"):
            task_from_dataset(Dataset(), config)

    @patch("nirs4all_domains.dataset.version", return_value="0.3.11")
    def test_exclusion_requires_explicit_mapping_and_units(self, _):
        ds = Dataset()
        ds.split_data = pd.DataFrame({"sample_id": ["a", "b"], "partition": ["dev", "validation"]})
        with self.assertRaisesRegex(ValueError, "unknown partition"):
            task_from_dataset(ds, self.config())
        config = self.config()
        config["target_unit"] = " "
        with self.assertRaisesRegex(ValueError, "Target unit"):
            task_from_dataset(Dataset(), config)

    def test_batch_failure_is_retained_and_next_task_runs(self):
        binary = os.environ.get("N4DOMAINS_BIN")
        self.assertTrue(binary, "Set N4DOMAINS_BIN for integration tests")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task = json.loads((ROOT / "tests/fixtures/translation.json").read_text())
            (root / "task.json").write_text(json.dumps(task))
            (root / "campaign.yaml").write_text("schema_version: 1\ntasks:\n  - task_file: missing.json\n  - task_file: task.json\n")
            summary = run_campaign(root / "campaign.yaml", root / "out", binary, os.environ.get("N4DOMAINS_METHODS_LIBRARY"))
            self.assertEqual(summary["tasks"][0]["status"], "error")
            self.assertEqual(summary["tasks"][1]["status"], "partial")
            self.assertTrue((root / "out/task-001/report.md").exists())
            (root / "campaign.yaml").write_text("schema_version: 1\ntasks:\n  - task_file: missing.json\n  - task_file: missing-again.json\n")
            rerun = run_campaign(root / "campaign.yaml", root / "out", binary)
            self.assertEqual(rerun["tasks"][1]["status"], "error")
            self.assertFalse((root / "out/task-001/report.json").exists())

    def test_fixtures_conform_to_json_schema(self):
        import jsonschema
        schema = json.loads((ROOT / "schemas/task.v1.schema.json").read_text())
        for path in (ROOT / "tests/fixtures").glob("*.json"):
            jsonschema.validate(json.loads(path.read_text()), schema)

    def test_installed_datasets_public_getters_to_real_cli(self):
        """Actual Datasets 0.3.11 on synthetic canonical bytes, without network."""
        import nirs4all_datasets as datasets
        import yaml
        import subprocess
        binary = os.environ["N4DOMAINS_BIN"]
        original = json.loads((ROOT / "tests/fixtures/translation.json").read_text())
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data_dir = root / "datasets/synthetic_adapter/canonical"
            data_dir.mkdir(parents=True)
            catalog = root / "catalog/datasets"
            catalog.mkdir(parents=True)
            descriptor = {"schema_version": "2.0", "id": "synthetic_adapter", "name": "Synthetic adapter fixture",
                "description": "Controlled synthetic data, not a catalog benchmark", "tier": "public",
                "sources": [{"source_id": "A", "axis_unit": "nm"}],
                "variables": [{"name": "y", "role": "target", "type": "numeric"},
                              {"name": "site", "role": "metadata", "type": "categorical"}],
                "provenance": {"contributor": "synthetic test"}, "governance": {"license": "AGPL-3.0-or-later"}}
            (catalog / "synthetic_adapter.yaml").write_text(yaml.safe_dump(descriptor))
            spectra = []
            variables = []
            splits = []
            for row in original["observations"]:
                spectra.append({"observation_id": row["observation_id"], "sample_id": row["sample_id"],
                    **{str(axis): value for axis, value in zip(original["axis"], row["x"], strict=True)}})
                variables.append({"sample_id": row["sample_id"], "y": row["y"], "site": "synthetic-site"})
                splits.append({"sample_id": row["sample_id"], "partition": row["partition"]})
            pd.DataFrame(spectra).to_parquet(data_dir / "A.parquet", index=False)
            pd.DataFrame(variables[::-1]).to_parquet(data_dir / "variables.parquet", index=False)
            pd.DataFrame(splits[::-1]).to_parquet(data_dir / "split.parquet", index=False)
            manifest = {"id": "synthetic_adapter", "alignment_level": "observation",
                "sources": [{"source_id": "A", "path": "canonical/A.parquet", "axis_unit": "nm"}],
                "variables": {"path": "canonical/variables.parquet"},
                "splits": [{"name": "original", "path": "canonical/split.parquet"}]}
            (data_dir / "dataset.json").write_text(json.dumps(manifest))
            ds = datasets.get("synthetic_adapter", root=root)
            config = self.config()
            config.update(data_origin="synthetic", partition_labels={"train": "train", "test": "test"})
            task = task_from_dataset(ds, config)
            self.assertEqual(task["observations"][0]["y"], original["observations"][0]["y"])
            self.assertNotIn("y", task["observations"][-1])
            task_path = root / "task.json"
            task_path.write_text(json.dumps(task, allow_nan=False))
            result = subprocess.run([binary, "analyze", str(task_path), "--out", str(root / "report")], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((root / "report/report.json").read_text())
            self.assertEqual(report["data_origin"], "synthetic")
            self.assertEqual(report["provenance"]["datasets"], "0.3.11")
            if os.environ.get("N4DOMAINS_METHODS_LIBRARY"):
                coverage = next(m for m in report["metrics"] if m["metric_id"] == "coverage.test_outside_fraction")
                self.assertEqual(coverage["value"], 1.)
            campaign = {"schema_version": 1, "tasks": [{**config, "dataset_id": "synthetic_adapter"}]}
            campaign_path = root / "campaign.yaml"
            campaign_path.write_text(yaml.safe_dump(campaign))
            summary = run_campaign(campaign_path, root / "batch", binary,
                                   os.environ.get("N4DOMAINS_METHODS_LIBRARY"), catalog_root=root)
            self.assertEqual(summary["tasks"][0]["status"], "partial")


if __name__ == "__main__": unittest.main()
