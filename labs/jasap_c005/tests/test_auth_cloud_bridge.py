"""C002 Ed25519 authenticated envelope + C003 fake-cloud ledger E2E, no AWS traffic."""
import base64
import hashlib
import time
import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from trust_anchor.core import Anchor, request_envelope, verify_response
from trust_anchor.cloud_adapter import CloudLedger
from test_cloud_adapter import FakeDDB, FakeS3


def pub(key):
    return base64.b64encode(key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw)).decode()

class SignedEnvelopeCloud(unittest.TestCase):
    def setUp(self):
        self.client_key=Ed25519PrivateKey.generate()
        self.anchor_key=Ed25519PrivateKey.generate()
        self.ddb=FakeDDB();self.s3=FakeS3()
        ledger=CloudLedger(self.ddb,self.s3,"synthetic-table","synthetic-witness-bucket",expected_bucket_owner="222222222222")
        principals={"synthetic-client":{"public_key":pub(self.client_key),"tenant":"tenant-one",
                                         "actions":["reserve","status"],"operations":["extract_document"]}}
        self.anchor=Anchor(ledger,principals,self.anchor_key)
        self.payload={"action":"reserve","tenant":"tenant-one", "operation":"extract_document",
                      "request_id":"test-request-signed-000001", "digest":"a"*64}

    def send(self,payload,key=None):
        req=request_envelope("synthetic-client",key or self.client_key,payload)
        return verify_response(self.anchor.respond(req),self.anchor_key.public_key())

    def test_signed_authenticated_reservation(self):
        r=self.send(self.payload)
        self.assertEqual(r["decision"],"WITNESSED")
        self.assertFalse(r["execution_authorized"])
        self.assertEqual(r["gxp_release"],"NOT_GRANTED")
    def test_authenticated_duplicate(self):
        self.send(self.payload)
        self.assertEqual(self.send(self.payload)["decision"],"DUPLICATE")
    def test_untrusted_identity_cannot_reserve(self):
        r=self.send(self.payload,Ed25519PrivateKey.generate())
        self.assertEqual(r["decision"],"DENIED")
        self.assertEqual(r["reason"],"AUTHENTICATION_FAILED")
    def test_cross_tenant_denied(self):
        p={**self.payload,"tenant":"tenant-other"}
        self.assertEqual(self.send(p)["reason"],"AUTHORIZATION_FAILED")
    def test_external_execution_rejected(self):
        p={**self.payload,"operation":"execute_workflow"}
        self.assertEqual(self.send(p)["reason"],"OPERATION_NOT_ALLOWED")
    def test_status_has_no_grant(self):
        self.send(self.payload)
        p={**self.payload,"action":"status"}
        r=self.send(p)
        self.assertEqual(r["decision"],"FOUND")
        self.assertFalse(r["execution_authorized"])
    def test_witness_storage_outage_holds(self):
        self.s3.fail_write=True
        r=self.send(self.payload)
        self.assertEqual(r["decision"],"HOLD")
        self.assertFalse(r["execution_authorized"])

if __name__=="__main__": unittest.main()
