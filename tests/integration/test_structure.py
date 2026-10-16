import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import jsonschema

ROOT=Path(__file__).resolve().parents[2]


class StructureTests(unittest.TestCase):
    def test_cli_structure_replays_schema_and_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cfg=json.loads((ROOT/'configs/pilots/structure-v1.json').read_text());cfg['replicates']=20
            config=root/'config.json';config.write_text(json.dumps(cfg))
            command=[os.environ['N4DOMAINS_BIN'],'structure',str(ROOT/'tests/fixtures/structure/separated.json'),'--config',str(config)]
            for name in ['first','second']:
                subprocess.run([*command,'--out',str(root/name)],check=True,capture_output=True)
                subprocess.run([os.sys.executable,str(ROOT/'scripts/check_structure_report.py'),str(root/name/'report.json')],check=True,capture_output=True)
            first=(root/'first/report.json').read_bytes();self.assertEqual(first,(root/'second/report.json').read_bytes())
            r=json.loads(first);self.assertEqual(r['classification'],'robust_structure');self.assertEqual(r['population']['n_physical_samples'],72)
            failed=subprocess.run([*command,'--out',str(root/'first')],capture_output=True)
            self.assertNotEqual(failed.returncode,0);self.assertEqual(first,(root/'first/report.json').read_bytes())

    def test_structure_missing_provider_and_invalid_config_are_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);environment={k:v for k,v in os.environ.items() if k!='N4DOMAINS_METHODS_LIBRARY'}
            command=[os.environ['N4DOMAINS_BIN'],'structure',str(ROOT/'tests/fixtures/structure/separated.json')]
            subprocess.run([*command,'--config',str(ROOT/'configs/pilots/structure-v1.json'),'--out',str(root/'missing')],env=environment,check=True,capture_output=True)
            report=json.loads((root/'missing/report.json').read_text());self.assertEqual(report['status'],'unavailable');self.assertFalse(report['settings'])
            cfg=json.loads((ROOT/'configs/pilots/structure-v1.json').read_text());cfg['replicates']=10000;bad=root/'bad.json';bad.write_text(json.dumps(cfg))
            result=subprocess.run([*command,'--config',str(bad),'--out',str(root/'invalid')],capture_output=True)
            self.assertNotEqual(result.returncode,0);self.assertFalse((root/'invalid').exists())

    def test_structural_control_inputs_and_configuration_match_schemas(self):
        schema=json.loads((ROOT/'schemas/task.v1.schema.json').read_text())
        for path in (ROOT/'tests/fixtures/structure').glob('*.json'):
            jsonschema.validate(json.loads(path.read_text()),schema)
        jsonschema.validate(json.loads((ROOT/'configs/pilots/structure-v1.json').read_text()),json.loads((ROOT/'schemas/structure-config.v1.schema.json').read_text()))
