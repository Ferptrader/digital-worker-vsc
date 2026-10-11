import hashlib
import tempfile
import unittest
from pathlib import Path
from tools.jarvis_auth_gateway_candidate import MemoryReplayGuard, process_authenticated, sign_request

class Gateway(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.doc=self.root/"urs.txt"; self.doc.write_text("Synthetic test",encoding="utf-8")
        self.keys={"test-dispatcher":b"synthetic-only-key-value-never-production"}
        self.guard=MemoryReplayGuard()
        self.now=1000000
        self.payload={"operation":"extract_document","document_path":str(self.doc),"analysis_type":"risk"}
    def tearDown(self): self.tmp.cleanup()
    def env(self,payload=None, identity="test-dispatcher",ts=None,nonce="abcdefghijklmnop0001"):
        p=payload if payload is not None else self.payload
        t=ts if ts is not None else self.now
        return {"identity":identity,"timestamp":t,"nonce":nonce,"payload":p,
                "signature":sign_request(self.keys["test-dispatcher"],identity,t,nonce,p)}
    def run_env(self,e):
        return process_authenticated(e,keys=self.keys,allowed_root=str(self.root),guard=self.guard,clock=lambda:self.now)
    def test_authenticated_extraction(self):
        r=self.run_env(self.env()); self.assertEqual(r["status"],"EXTRACTED_UNVERIFIED");self.assertFalse(r["execution_authorized"])
    def test_tampered_payload(self):
        e=self.env(); e["payload"]={**self.payload,"analysis_type":"compliance"}
        self.assertEqual(self.run_env(e)["reason"],"AUTHORIZATION_FAILED")
    def test_replay(self):
        e=self.env(); self.run_env(e)
        self.assertEqual(self.run_env(e)["reason"],"REPLAY_REJECTED")
    def test_expired(self):
        self.assertEqual(self.run_env(self.env(ts=self.now-121))["reason"],"AUTHORIZATION_FAILED")
    def test_unknown_identity(self):
        self.assertEqual(self.run_env(self.env(identity="unknown"))["reason"],"AUTHORIZATION_FAILED")
    def test_unauthorized_action(self):
        r=self.run_env(self.env(payload={"operation":"execute_workflow"},nonce="abcdefghijklmnop0002"))
        self.assertEqual(r["reason"],"OPERATION_NOT_ALLOWED")
    def test_missing_field(self):
        e=self.env(); del e["signature"]
        self.assertEqual(self.run_env(e)["reason"],"AUTHORIZATION_FAILED")
    def test_wrong_signature(self):
        e=self.env(); e["signature"]="0"*64
        self.assertEqual(self.run_env(e)["reason"],"AUTHORIZATION_FAILED")
    def test_approval_claim_denied(self):
        p={**self.payload,"approve":True}
        self.assertEqual(self.run_env(self.env(payload=p,nonce="abcdefghijklmnop0003"))["reason"],"AUTHORITY_FIELDS_REJECTED")
    def test_durable_store_across_instances(self):
        from tools.sqlite_replay_candidate import SQLiteReplayGuard
        from tools.jarvis_auth_gateway_candidate import process_authenticated
        database=str(self.root/"replay.db")
        e=self.env()
        first=process_authenticated(e,keys=self.keys,allowed_root=str(self.root),
                    guard=SQLiteReplayGuard(database),clock=lambda:self.now)
        second=process_authenticated(e,keys=self.keys,allowed_root=str(self.root),
                    guard=SQLiteReplayGuard(database),clock=lambda:self.now)
        self.assertEqual(first["status"],"EXTRACTED_UNVERIFIED")
        self.assertEqual(second["reason"],"REPLAY_REJECTED")
    def test_store_exception_fails_closed(self):
        class Broken:
            def reserve(self,*args): raise OSError("simulated")
        from tools.jarvis_auth_gateway_candidate import process_authenticated
        r=process_authenticated(self.env(),keys=self.keys,allowed_root=str(self.root),
                guard=Broken(),clock=lambda:self.now)
        self.assertEqual(r["reason"],"REPLAY_STORE_UNAVAILABLE")
        self.assertFalse(r["execution_authorized"])
if __name__=="__main__":unittest.main()
