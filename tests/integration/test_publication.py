"""Real staged-blob and archive adversaries with synthetic sensitive content."""
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
import zipfile

import jsonschema
from nirs4all_domains.disclosure import candidate,validate_public
from nirs4all_domains.privacy import PrivacyError
from nirs4all_domains.publication import audit_surfaces,git_surfaces,package_surfaces,public_record

CANARY=b'SYNTHETIC_SECRET_PRIVATE_SOURCE_708324'


class OutgoingSurfaceControls(unittest.TestCase):
    def test_real_index_blob_is_scanned_despite_clean_worktree(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            subprocess.run(['git','init','--quiet'],cwd=root,check=True,capture_output=True)
            path=root/'report.md';path.write_bytes(CANARY)
            subprocess.run(['git','add','report.md'],cwd=root,check=True,capture_output=True)
            path.write_bytes(b'clean worktree')
            roster={'report.md':public_record(CANARY,'reviewed_documentation')}
            with self.assertRaisesRegex(PrivacyError,'PRIVATE_CONTENT'):
                audit_surfaces(git_surfaces(root,staged=True),roster,sensitive_literals=[CANARY])

    def test_force_staged_private_root_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            subprocess.run(['git','init','--quiet'],cwd=root,check=True,capture_output=True)
            (root/'.audit').mkdir();(root/'.audit/private.json').write_bytes(CANARY)
            subprocess.run(['git','add','-f','.audit/private.json'],cwd=root,check=True,capture_output=True)
            with self.assertRaisesRegex(PrivacyError,'RESTRICTED_PATH'):list(git_surfaces(root,staged=True))

    def test_unknown_csv_figure_log_model_or_fixture_not_auto_approved(self):
        for path in ['report.csv','figure.svg','figure.png','ci/private.json','model.n4me','trace.txt']:
            with self.assertRaisesRegex(PrivacyError,'NOT_REVIEWED'):audit_surfaces([(path,CANARY)],{})

    def test_changed_bytes_fail_reviewed_provenance(self):
        with self.assertRaisesRegex(PrivacyError,'PUBLIC_PROVENANCE'):
            audit_surfaces([('reviewed.md',CANARY)],{'reviewed.md':public_record(b'public','reviewed_documentation')})

    def test_real_wheel_and_sdist_private_member_not_rostered(self):
        with tempfile.TemporaryDirectory() as folder:
            for name in ['synthetic.whl','synthetic.tar.gz']:
                path=Path(folder)/name
                if name.endswith('whl'):
                    with zipfile.ZipFile(path,'w') as archive:
                        archive.writestr('package/code.py',b'# synthetic public')
                        archive.writestr('private/source.csv',CANARY)
                else:
                    with tarfile.open(path,'w:gz') as archive:
                        for member,data in [('package/code.py',b'# synthetic public'),('private/source.csv',CANARY)]:
                            info=tarfile.TarInfo(member);info.size=len(data);archive.addfile(info,io.BytesIO(data))
                with self.assertRaisesRegex(PrivacyError,'NOT_REVIEWED'):
                    audit_surfaces(package_surfaces(path),{'package/code.py':public_record(b'# synthetic public','public_source')})

    def test_raw_bytes_in_rostered_package_member_still_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'synthetic.whl'
            with zipfile.ZipFile(path,'w') as archive:archive.writestr('package/config.json',CANARY)
            with self.assertRaisesRegex(PrivacyError,'PRIVATE_CONTENT'):
                audit_surfaces(package_surfaces(path),{'package/config.json':public_record(CANARY,'public_source')},sensitive_literals=[CANARY])

    def test_package_traversal_and_links_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'synthetic.tar'
            with tarfile.open(path,'w') as archive:
                info=tarfile.TarInfo('linked');info.type=tarfile.SYMTYPE;info.linkname='../secret';archive.addfile(info)
            with self.assertRaisesRegex(PrivacyError,'LINK_FORBIDDEN'):list(package_surfaces(path))
            path=Path(folder)/'synthetic.whl'
            with zipfile.ZipFile(path,'w') as archive:archive.writestr('../source.json',CANARY)
            with self.assertRaisesRegex(PrivacyError,'PATH_INVALID'):list(package_surfaces(path))

    def test_package_expansion_bound_checked_before_read(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'synthetic.whl'
            with zipfile.ZipFile(path,'w') as archive:archive.writestr('large',b'x'*100)
            with self.assertRaisesRegex(PrivacyError,'BYTE_BOUND'):list(package_surfaces(path,maximum_unpacked_bytes=10))

    def test_privacy_schemas_match_runtime_and_reject_unknown_fields(self):
        from test_privacy import admission
        for name,value in [('private-admission',admission()),('public-disclosure',candidate())]:
            schema=json.loads(Path('schemas',name+'.v1.schema.json').read_text())
            jsonschema.Draft202012Validator.check_schema(schema)
            jsonschema.validate(value,schema)
            self.assertEqual(Path('schemas',name+'.v1.schema.json').read_bytes(),Path('bridges/python/nirs4all_domains',name+'.v1.schema.json').read_bytes())
            value['unknown_private_field']=CANARY.decode()
            with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(value,schema)


if __name__=='__main__':unittest.main()
