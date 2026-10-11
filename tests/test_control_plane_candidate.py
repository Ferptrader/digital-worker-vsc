import tempfile
import unittest
import time
from pathlib import Path
from control_plane.dispatcher import ControlPlane
from tools.jarvis_auth_gateway_candidate import sign_request
from tools.sqlite_replay_candidate import SQLiteReplayGuard

class ControlPlaneTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.doc=self.root/"sample.txt"
        self.doc.write_text("Synthetic requirement",encoding="utf-8")
        self.key=b"test-only-not-production-key"
        self.cp=ControlPlane(keys={"test":self.key},allowed_root=str(self.root),
                replay_guard=SQLiteReplayGuard(str(self.root/"nonce.sqlite")))
    def tearDown(self): self.temp.cleanup()
    def env(self,nonce):
        payload={"operation":"extract_document","document_path":str(self.doc),"analysis_type":"risk"}
        stamp=int(time.time())
        return {"identity":"test","timestamp":stamp,"nonce":nonce,"payload":payload,
                "signature":sign_request(self.key,"test",stamp,nonce,payload)}
    def test_extract_never_approves(self):
        r=self.cp.dispatch(self.env("abcdefghijklmnop1234"),correlation_id="test-correlation-123")
        self.assertEqual(r["status"],"EXTRACTED_UNVERIFIED")
        self.assertEqual(r["gxp_release"],"NOT_GRANTED")
        self.assertFalse(r["execution_authorized"])
        self.assertEqual(len(r["response_sha256"]),64)
    def test_replay_rejected(self):
        e=self.env("abcdefghijklmnop1235")
        self.cp.dispatch(e,correlation_id="test-correlation-123")
        r=self.cp.dispatch(e,correlation_id="test-correlation-123")
        self.assertEqual(r["reason"],"REPLAY_REJECTED")
        self.assertFalse(r["execution_authorized"])
    def test_bad_correlation(self):
        r=self.cp.dispatch(self.env("abcdefghijklmnop1236"),correlation_id="x")
        self.assertEqual(r["reason"],"INVALID_CORRELATION")
    def test_invalid_signature(self):
        e=self.env("abcdefghijklmnop1237");e["signature"]="0"*64
        self.assertEqual(self.cp.dispatch(e,correlation_id="test-correlation-123")["reason"],"AUTHORIZATION_FAILED")
if __name__=="__main__":unittest.main()
