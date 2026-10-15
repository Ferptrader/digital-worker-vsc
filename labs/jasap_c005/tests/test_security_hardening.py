"""C004 adversarial tests; synthetic clients only, no cloud requests."""
import base64
import hashlib
import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from trust_anchor.core import Anchor, request_envelope, verify_response
from trust_anchor.cloud_adapter import CloudLedger
from test_cloud_adapter import FakeDDB, FakeS3

def pub(k):
    return base64.b64encode(k.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,format=serialization.PublicFormat.Raw)).decode()

class SecurityHardening(unittest.TestCase):
    def setUp(self):
        self.client_a=Ed25519PrivateKey.generate()
        self.client_b=Ed25519PrivateKey.generate()
        self.anchor_key=Ed25519PrivateKey.generate()
        self.db,self.s3=FakeDDB(),FakeS3()
        self.ledger=CloudLedger(self.db,self.s3,"reservation-test","witness-test",expected_bucket_owner="222222222222")
        principals={"client-a":{"public_key":pub(self.client_a),"tenant":"same-tenant","actions":["reserve","status"],"operations":["extract_document"]},
                    "client-b":{"public_key":pub(self.client_b),"tenant":"same-tenant","actions":["reserve","status"],"operations":["extract_document"]}}
        self.anchor=Anchor(self.ledger,principals,self.anchor_key)
        self.payload={"action":"reserve","tenant":"same-tenant","operation":"extract_document",
                      "request_id":"synthetic-strong-0000001","digest":"a"*64}
    def send(self,name,key,payload):
        return verify_response(self.anchor.respond(request_envelope(name,key,payload)),self.anchor_key.public_key())
    def test_signed_operation_accepts_valid_owner(self):
        self.assertEqual(self.send("client-a",self.client_a,self.payload)["decision"],"WITNESSED")
    def test_other_client_cannot_read_owners_status(self):
        self.send("client-a",self.client_a,self.payload)
        response=self.send("client-b",self.client_b,{**self.payload,"action":"status"})
        self.assertEqual(response["decision"],"DENIED")
        self.assertEqual(response["reason"],"IDENTITY_MISMATCH")
    def test_other_client_cannot_duplicate_owners_reservation(self):
        self.send("client-a",self.client_a,self.payload)
        response=self.send("client-b",self.client_b,self.payload)
        self.assertEqual(response["decision"],"DENIED")
    def test_other_client_cannot_obtain_existing_digest(self):
        self.send("client-a",self.client_a,self.payload)
        response=self.send("client-b",self.client_b,{**self.payload,"digest":"b"*64})
        self.assertEqual(response["decision"],"DENIED")
    def test_invalid_signer_rejected(self):
        response=self.send("client-a",self.client_b,self.payload)
        self.assertEqual(response["reason"],"AUTHENTICATION_FAILED")
    def test_nonlisted_operation_denied(self):
        response=self.send("client-a",self.client_a,{**self.payload,"operation":"execute_gxp"})
        self.assertEqual(response["reason"],"OPERATION_NOT_ALLOWED")
    def test_deleted_db_cannot_be_reauthorized_while_witness_exists(self):
        self.assertEqual(self.send("client-a",self.client_a,self.payload)["decision"],"WITNESSED")
        self.db.records.clear()
        self.assertEqual(self.send("client-a",self.client_a,self.payload)["decision"],"HOLD")
    def test_witness_corrupted_fails_closed(self):
        self.send("client-a",self.client_a,self.payload)
        self.s3.objects[next(iter(self.s3.objects))]["body"]=b"attack"
        self.assertEqual(self.send("client-a",self.client_a,{**self.payload,"action":"status"})["decision"],"HOLD")
    def test_missing_witness_after_reservation_holds(self):
        self.s3.fail_write=True
        self.assertEqual(self.send("client-a",self.client_a,self.payload)["decision"],"HOLD")
        self.assertEqual(self.send("client-a",self.client_a,self.payload)["decision"],"HOLD")
    def test_unauthenticated_status_is_denied(self):
        self.assertEqual(self.ledger.status("same-tenant","extract_document","synthetic-strong-0000001")["decision"], "DENIED")
    def test_no_external_execution_granted(self):
        result=self.send("client-a",self.client_a,self.payload)
        self.assertFalse(result["execution_authorized"])
        self.assertEqual(result["gxp_approval"],"NOT_GRANTED")

if __name__=="__main__":unittest.main()
