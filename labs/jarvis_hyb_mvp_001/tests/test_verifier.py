import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from jarvis_hyb.verifier import run, validate_csv

BASE=Path(__file__).resolve().parents[1]
FIXTURE=BASE/'fixtures'

class VerifierTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.source=self.root/'input'
        shutil.copytree(FIXTURE,self.source)

    def update_json(self,fn):
        path=self.source/'sim_ems_v0.4.json'
        v=json.loads(path.read_text(encoding='utf-8'))
        fn(v)
        path.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        self.rehash('requirements_json')

    def rehash(self,key):
        manifest_path=self.source/'manifest.json'
        manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
        entry=manifest['declared_inputs'][key]
        entry['sha256']=hashlib.sha256((self.source/entry['file']).read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    def update_csv(self,fn):
        p=self.source/'sim_ems_20_v0.4.csv'
        with p.open(encoding='utf-8-sig',newline='') as f:
            rd=csv.DictReader(f,delimiter=';')
            fields=rd.fieldnames
            rows=list(rd)
        fn(rows)
        with p.open('w',encoding='utf-8-sig',newline='') as f:
            wr=csv.DictWriter(f,fieldnames=fields,delimiter=';')
            wr.writeheader();wr.writerows(rows)
        self.rehash('readings_csv')

    def ids(self,result):
        return {f['id'] for f in result['findings']}

    def test_01_clean_fixture_is_structural_pass_only(self):
        r=run(self.source)
        self.assertEqual(r['documentary_structural_status'],'PASS')
        self.assertEqual(r['counts']['findings'],0)
        self.assertEqual(r['counts']['traces'],16)
        self.assertEqual(r['execution'],{'oq_planned':16,'oq_executed':0,'harness_tests_planned':22,'harness_tests_executed':0})

    def test_02_never_grants_gxp(self):
        r=run(self.source)
        self.assertFalse(r['gxp_release_authorized'])
        self.assertEqual(r['harness_authoritative_gate'],'HOLD')
        self.assertEqual(r['quality_gates']['G4'],'HOLD')
        self.assertEqual(r['quality_gates']['G5'],'HOLD')

    def test_03_byte_tamper_without_rehash_hold(self):
        p=self.source/'sim_ems_v0.4.json'
        p.write_bytes(p.read_bytes()+b' ')
        r=run(self.source)
        self.assertEqual(r['documentary_structural_status'],'HOLD')
        self.assertIn('INT-001',self.ids(r))

    def test_04_invalid_manifest_version_hold(self):
        p=self.source/'manifest.json'
        m=json.loads(p.read_text(encoding='utf-8'))
        m['fixture_revision']='v9.9'
        p.write_text(json.dumps(m),encoding='utf-8')
        self.assertIn('INT-001',self.ids(run(self.source)))

    def test_05_unknown_risk_ref_fail(self):
        self.update_json(lambda d:d['URS'][0].__setitem__(4,'RSK-999'))
        self.assertIn('RTM-001',self.ids(run(self.source)))

    def test_06_duplicate_oq_fail(self):
        self.update_json(lambda d:d['OQ'][1].__setitem__(0,'OQ-001'))
        self.assertIn('DAT-DUP',self.ids(run(self.source)))

    def test_07_urs_risk_mismatch_fail(self):
        self.update_json(lambda d:d['OQ'][0].__setitem__(2,'RSK-002'))
        self.assertIn('RTM-011',self.ids(run(self.source)))

    def test_08_incomplete_expected_result_fail(self):
        self.update_json(lambda d:d['OQ'][3].__setitem__(6,''))
        self.assertIn('RTM-012',self.ids(run(self.source)))

    def test_09_missing_oq_link_fail(self):
        self.update_json(lambda d:d['OQ'].pop(0))
        r=run(self.source)
        self.assertIn('RTM-014',self.ids(r))
        self.assertEqual(r['documentary_structural_status'],'FAIL')

    def test_10_control_list_not_equal_rtm_fail(self):
        self.update_json(lambda d:d['RISKS'][3].__setitem__(6,'OQ-004'))
        self.assertIn('RTM-007',self.ids(run(self.source)))

    def test_11_duplicated_event_fail(self):
        self.update_csv(lambda rows:rows[1].__setitem__('id_evento',rows[0]['id_evento']))
        self.assertIn('CSV-005',self.ids(run(self.source)))

    def test_12_naive_timestamp_fail(self):
        self.update_csv(lambda rows:rows[0].__setitem__('timestamp_iso8601','2026-10-18T08:00:00'))
        self.assertIn('CSV-009',self.ids(run(self.source)))

    def test_13_nonnumeric_value_fail(self):
        self.update_csv(lambda rows:rows[0].__setitem__('valor_c','NaN'))
        self.assertIn('CSV-008',self.ids(run(self.source)))

    def test_14_missing_one_reading_fail(self):
        self.update_csv(lambda rows:rows.pop())
        self.assertIn('CSV-002',self.ids(run(self.source)))

    def test_15_compare_equivalent_synthetic_file_pass_not_oq(self):
        r=run(self.source,candidate_csv=self.source/'sim_ems_20_v0.4.csv')
        self.assertEqual(r['comparisons']['export']['status'],'PASS')
        self.assertEqual(r['execution']['oq_executed'],0)
        self.assertEqual(r['quality_gates']['G4'],'HOLD')

    def test_16_compare_tampered_export_fail(self):
        p=self.root/'modified.csv'
        shutil.copyfile(self.source/'sim_ems_20_v0.4.csv',p)
        with p.open(encoding='utf-8-sig',newline='') as f:
            rd=csv.DictReader(f,delimiter=';'); fields=rd.fieldnames; rows=list(rd)
        rows[5]['valor_c']='6.2'
        with p.open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fields,delimiter=';');w.writeheader();w.writerows(rows)
        r=run(self.source,candidate_csv=p)
        self.assertEqual(r['comparisons']['export']['status'],'FAIL')
        self.assertIn('CMP-DIFF',self.ids(r))

    def test_17_symlink_manifest_blocks(self):
        # Windows may prohibit creation of symbolic links (WinError 1314).
        # Verify the security guard deterministically even without elevation.
        p=self.source/'manifest.json'
        other=self.root/'external.json'
        shutil.move(p,other)
        try:
            p.symlink_to(other)
        except OSError as exc:
            if not (isinstance(exc, PermissionError) or getattr(exc, 'winerror', None)==1314):
                raise
            # Restore a regular fixture file, then simulate the filesystem
            # returning is_symlink=True for this precise manifest path.
            shutil.copyfile(other,p)
            is_symlink_original=Path.is_symlink
            def is_symlink_injected(path):
                return path == p or is_symlink_original(path)
            with patch.object(Path,'is_symlink',is_symlink_injected):
                result=run(self.source)
        else:
            result=run(self.source)
        self.assertEqual(result['documentary_structural_status'],'HOLD')
        self.assertIn('INT-001',self.ids(result))

    def test_18_cli_creates_reports_and_returns_zero_on_clean_structure(self):
        out=self.root/'out'
        cp=subprocess.run([sys.executable,'-m','jarvis_hyb','verify','--fixture-dir',str(self.source),'--output-dir',str(out)],cwd=BASE,capture_output=True,text=True)
        self.assertEqual(cp.returncode,0,cp.stderr)
        self.assertTrue((out/'verification.json').is_file())
        self.assertIn('G0/G4/G5: HOLD',(out/'summary.txt').read_text(encoding='utf-8'))
        self.assertTrue((out/'SHA256SUMS.txt').is_file())

    def test_19_cli_rejects_overwrite(self):
        out=self.root/'out';out.mkdir()
        cp=subprocess.run([sys.executable,'-m','jarvis_hyb','verify','--fixture-dir',str(self.source),'--output-dir',str(out)],cwd=BASE,capture_output=True,text=True)
        self.assertNotEqual(cp.returncode,0)
        self.assertIn('OUTPUT_DIR_EXISTS',cp.stderr)

    def test_20_cli_nonzero_on_bad_links(self):
        self.update_json(lambda d:d['URS'][0].__setitem__(4,'RSK-999'))
        out=self.root/'bad'
        cp=subprocess.run([sys.executable,'-m','jarvis_hyb','verify','--fixture-dir',str(self.source),'--output-dir',str(out)],cwd=BASE,capture_output=True,text=True)
        self.assertEqual(cp.returncode,1,cp.stderr)
        r=json.loads((out/'verification.json').read_text(encoding='utf-8'))
        self.assertEqual(r['documentary_structural_status'],'FAIL')


if __name__=='__main__':
    unittest.main()
