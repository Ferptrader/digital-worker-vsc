import tempfile
import unittest
import time
from pathlib import Path
from control_plane.dispatcher import ControlPlane
from tools.jarvis_auth_gateway_candidate import sign_request
from tools.sqlite_replay_candidate import SQLiteReplayGuard

class EndToEndBoundary(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.root.joinpath("example.md").write_text("Synthetic URS audit trail",encoding="utf-8")
        self.key=b"synthetic-e2e-key-not-production"
        self.db=str(self.root/"reservations.sqlite")
    def tearDown(self): self.temp.cleanup()
    def request(self,nonce,payload=None):
        payload=payload or {"operation":"extract_document","document_path":str(self.root/"example.md"),"analysis_type":"compliance"}
        timestamp=int(time.time())
        return {"identity":"client-a","timestamp":timestamp,"nonce":nonce,"payload":payload,
                "signature":sign_request(self.key,"client-a",timestamp,nonce,payload)}
    def dispatcher(self,db=None):
        return ControlPlane(keys={"client-a":self.key},allowed_root=str(self.root),
                            replay_guard=SQLiteReplayGuard(db or self.db))
    def test_correlation_and_hash(self):
        r=self.dispatcher().dispatch(self.request("nonce-abcdefghijkl-0001"),correlation_id="e2e-corr-00001")
        self.assertEqual(r["correlation_id"],"e2e-corr-00001")
        self.assertEqual(len(r["response_sha256"]),64)
        self.assertEqual(r["gxp_compliance"],"NOT_VERIFIED")
        self.assertEqual(r["status"],"EXTRACTED_UNVERIFIED")
    def test_restart_replay(self):
        envelope=self.request("nonce-abcdefghijkl-0002")
        self.assertEqual(self.dispatcher().dispatch(envelope,correlation_id="e2e-corr-00002")["status"],"EXTRACTED_UNVERIFIED")
        self.assertEqual(self.dispatcher().dispatch(envelope,correlation_id="e2e-corr-00002")["reason"],"REPLAY_REJECTED")
    def test_two_clients_no_shared_identity(self):
        r=self.dispatcher().dispatch(self.request("nonce-abcdefghijkl-0003"),correlation_id="e2e-corr-00003")
        self.assertEqual(r["gxp_approval"],"NOT_GRANTED")
    def test_tamper_denied(self):
        e=self.request("nonce-abcdefghijkl-0004")
        e["payload"]["analysis_type"]="risk"
        self.assertEqual(self.dispatcher().dispatch(e,correlation_id="e2e-corr-00004")["reason"],"AUTHORIZATION_FAILED")
    def test_no_dispatch_of_execute(self):
        payload={"operation":"execute_workflow"}
        r=self.dispatcher().dispatch(self.request("nonce-abcdefghijkl-0005",payload),correlation_id="e2e-corr-00005")
        self.assertEqual(r["reason"],"OPERATION_NOT_ALLOWED")
        self.assertFalse(r["execution_authorized"])
    def test_database_failure_closed(self):
        class Store:
            def reserve(self,*args): raise OSError("simulated failure")
        cp=ControlPlane(keys={"client-a":self.key},allowed_root=str(self.root),replay_guard=Store())
        r=cp.dispatch(self.request("nonce-abcdefghijkl-0006"),correlation_id="e2e-corr-00006")
        self.assertEqual(r["reason"],"REPLAY_STORE_UNAVAILABLE")
        self.assertFalse(r["execution_authorized"])

if __name__=="__main__": unittest.main()
