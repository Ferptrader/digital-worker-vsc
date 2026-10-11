import json
import tempfile
import unittest
from pathlib import Path
from tools.jarvis_handoff_candidate import handle_jarvis_request, handle_jarvis_json

class Handoff(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.file = self.root / "requirements.txt"
        self.file.write_text("Synthetic URS test", encoding="utf-8")
    def tearDown(self): self.temp.cleanup()
    def request(self, **kw):
        return {"operation":"extract_document","document_path":str(self.file),"analysis_type":"requirements", **kw}
    def test_extract_is_unverified(self):
        r=handle_jarvis_request(self.request(),allowed_root=str(self.root))
        self.assertEqual(r["status"],"EXTRACTED_UNVERIFIED")
        self.assertFalse(r["execution_authorized"])
        self.assertEqual(r["gxp_release"],"NOT_GRANTED")
    def test_disallow_execution(self):
        r=handle_jarvis_request(self.request(operation="execute_workflow"),allowed_root=str(self.root))
        self.assertEqual(r["reason"],"OPERATION_NOT_ALLOWED")
    def test_reject_authority_claim(self):
        r=handle_jarvis_request(self.request(approve=True),allowed_root=str(self.root))
        self.assertEqual(r["reason"],"AUTHORITY_FIELDS_REJECTED")
    def test_reject_outside_scope(self):
        other=self.root.parent / "outside-document.txt"
        r=handle_jarvis_request(self.request(document_path=str(other)),allowed_root=str(self.root))
        self.assertEqual(r["status"],"NOT_VERIFIED")
    def test_malformed_json(self):
        r=json.loads(handle_jarvis_json("{",allowed_root=str(self.root)))
        self.assertEqual(r["status"],"NOT_VERIFIED")
    def test_null_payload(self):
        r=handle_jarvis_request(None,allowed_root=str(self.root))
        self.assertEqual(r["status"],"NOT_VERIFIED")
if __name__ == "__main__":unittest.main()
