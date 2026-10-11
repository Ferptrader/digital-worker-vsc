import tempfile
import unittest
from pathlib import Path
from tools.safe_document_core import analyze_document, analyze_json
import json

class Safety(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / 'scope'
        self.root.mkdir()
        self.doc = self.root / 'test.txt'
        self.doc.write_text('URS-001: verify audit trail.', encoding='utf-8')
    def tearDown(self): self.tmp.cleanup()
    def test_extraction_unverified(self):
        r = analyze_document(str(self.doc), 'requirements', str(self.root))
        self.assertEqual(r['status'], 'EXTRACTED_UNVERIFIED')
        self.assertEqual(r['gxp_compliance'], 'NOT_VERIFIED')
    def test_no_authority_for_all_types(self):
        for kind in ('requirements','risk','compliance','structure'):
            r=analyze_document(str(self.doc),kind,str(self.root))
            self.assertEqual(r['gxp_release'],'NOT_GRANTED')
            self.assertEqual(r['gxp_approval'],'NOT_GRANTED')
    def test_missing_file(self):
        self.assertEqual(analyze_document(str(self.root/'absent.txt'),'risk',str(self.root))['status'],'NOT_VERIFIED')
    def test_escape(self):
        p=Path(self.tmp.name)/'outside.txt';p.write_text('PASS')
        self.assertEqual(analyze_document(str(p),'compliance',str(self.root))['reason'],'PATH_OUTSIDE_SCOPE')
    def test_zero_byte(self):
        p=self.root/'empty.txt';p.touch()
        self.assertEqual(analyze_document(str(p),'compliance',str(self.root))['reason'],'EMPTY_DOCUMENT')
    def test_unsupported(self):
        p=self.root/'binary.exe';p.write_bytes(b'abc')
        self.assertEqual(analyze_document(str(p),'structure',str(self.root))['reason'],'UNSUPPORTED_DOCUMENT')
    def test_unsupported_analysis(self):
        self.assertEqual(analyze_document(str(self.doc),'APPROVE',str(self.root))['reason'],'INVALID_ANALYSIS_TYPE')
    def test_hash(self):
        import hashlib
        r=analyze_document(str(self.doc),'risk',str(self.root))
        self.assertEqual(r['evidence']['sha256'],hashlib.sha256(self.doc.read_bytes()).hexdigest())
    def test_json_no_false_pass(self):
        r=json.loads(analyze_json(str(self.doc),'compliance',str(self.root)))
        self.assertEqual(r['gxp_compliance'],'NOT_VERIFIED')
        self.assertEqual(r['gxp_release'],'NOT_GRANTED')
    def test_bad_pdf(self):
        p=self.root/'bad.pdf';p.write_bytes(b'not a pdf')
        self.assertEqual(analyze_document(str(p),'compliance',str(self.root))['status'],'NOT_VERIFIED')

if __name__=='__main__': unittest.main()
