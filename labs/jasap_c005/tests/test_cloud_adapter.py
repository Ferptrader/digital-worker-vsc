"""C003 contract tests only: deterministic fake AWS clients, NO AWS calls."""
import copy
import hashlib
import io
import threading
import base64
import unittest
from datetime import datetime, timezone, timedelta
from botocore.exceptions import ClientError
from trust_anchor.cloud_adapter import CloudLedger


def failure(code):
    return ClientError({"Error": {"Code": code, "Message": "synthetic"}}, "MockAWS")


class FakeDDB:
    def __init__(self):
        self.records = {}
        self.lock = threading.Lock()
        self.unavailable = False
        self.fail_update = False
        self.fail_read = False
    def put_item(self, **kwargs):
        if self.unavailable: raise failure("ServiceUnavailable")
        key = kwargs["Item"]["pk"]["S"]
        with self.lock:
            if key in self.records: raise failure("ConditionalCheckFailedException")
            self.records[key] = copy.deepcopy(kwargs["Item"])
        return {}
    def get_item(self, **kwargs):
        if self.fail_read: raise failure("ServiceUnavailable")
        with self.lock:
            v=self.records.get(kwargs["Key"]["pk"]["S"])
            return {"Item": copy.deepcopy(v)} if v is not None else {}
    def update_item(self, **kwargs):
        if self.fail_update: raise failure("ServiceUnavailable")
        key=kwargs["Key"]["pk"]["S"]
        with self.lock:
            r=self.records[key]
            values=kwargs["ExpressionAttributeValues"]
            if r["state"] != values[":p"] or r["digest"] != values[":d"]:
                raise failure("ConditionalCheckFailedException")
            r["state"]=values[":w"]
            r["witness_version"]=values[":v"]
            r["witness_digest"]=values[":h"]
        return {}


class FakeS3:
    def __init__(self):
        self.objects={}
        self.lock=threading.Lock()
        self.fail_write=False
        self.fail_head=False
        self.fail_read=False
        self.invalid_retention=False
        self.owner="222222222222"
        self.fail_versions=False
        self.hidden_current=set()
    def _verify_owner(self, kwargs):
        if kwargs.get("ExpectedBucketOwner") != self.owner:
            raise failure("AccessDenied")
    def list_object_versions(self, **kwargs):
        self._verify_owner(kwargs)
        if self.fail_versions: raise failure("AccessDenied")
        prefix=kwargs["Prefix"]
        versions=[{"Key":k,"VersionId":v["version"]} for k,v in self.objects.items() if k.startswith(prefix)]
        markers=[{"Key":k,"VersionId":"marker-1"} for k in self.hidden_current if k.startswith(prefix)]
        return {"IsTruncated":False,"Versions":versions,"DeleteMarkers":markers}
    def put_object(self, **kwargs):
        self._verify_owner(kwargs)
        if self.fail_write: raise failure("AccessDenied")
        assert kwargs["ObjectLockMode"] == "COMPLIANCE"
        assert kwargs["IfNoneMatch"] == "*"
        assert base64.b64decode(kwargs["ContentMD5"]) == __import__("hashlib").md5(kwargs["Body"]).digest()
        key=kwargs["Key"]
        with self.lock:
            if key in self.objects: raise failure("PreconditionFailed")
            version="v1-mock-only"
            self.objects[key] = {"body":bytes(kwargs["Body"]),"version":version,
                                 "mode":kwargs["ObjectLockMode"],"until":kwargs["ObjectLockRetainUntilDate"]}
            return {"VersionId":version}
    def head_object(self, **kwargs):
        self._verify_owner(kwargs)
        if self.fail_head: raise failure("ServiceUnavailable")
        x=self.objects[kwargs["Key"]]
        if kwargs["VersionId"] != x["version"]:raise failure("NoSuchVersion")
        return {"ObjectLockMode": "GOVERNANCE" if self.invalid_retention else x["mode"],
                "ObjectLockRetainUntilDate":x["until"]}
    def get_object(self, **kwargs):
        self._verify_owner(kwargs)
        if self.fail_read: raise failure("AccessDenied")
        x=self.objects[kwargs["Key"]]
        if kwargs["VersionId"] != x["version"]:raise failure("NoSuchVersion")
        return {"Body":io.BytesIO(x["body"])}


class CloudContract(unittest.TestCase):
    def setUp(self):
        self.ddb=FakeDDB();self.s3=FakeS3()
        self.ledger=CloudLedger(self.ddb,self.s3,"lab-reservation-table","separate-audit-account-bucket",expected_bucket_owner="222222222222")
        self.dig="a"*64;self.now=1792093200
        self.args=("lab-client","tenant-one","extract_document","synthetic-request-00000001",self.dig,self.now)
    def reserve(self): return self.ledger.reserve(*self.args)
    def test_01_first_reservation_witnessed(self):
        self.assertEqual(self.reserve()["decision"],"WITNESSED")
    def test_02_duplicate_no_new_witness(self):
        self.reserve();self.assertEqual(self.reserve()["decision"],"DUPLICATE");self.assertEqual(len(self.s3.objects),1)
    def test_03_conflicting_digest(self):
        self.reserve();r=self.ledger.reserve(*self.args[:-2],"b"*64,self.now)
        self.assertEqual(r["decision"],"CONFLICT")
    def test_04_other_tenant_distinct_reservation(self):
        self.reserve();r=self.ledger.reserve("lab-client","tenant-two",*self.args[2:])
        self.assertEqual(r["decision"],"WITNESSED");self.assertEqual(len(self.s3.objects),2)
    def test_05_database_failure_holds(self):
        self.ddb.unavailable=True;self.assertEqual(self.reserve()["decision"],"HOLD")
    def test_06_witness_failure_holds(self):
        self.s3.fail_write=True;self.assertEqual(self.reserve()["decision"],"HOLD")
        self.s3.fail_write=False;self.assertEqual(self.reserve()["decision"],"HOLD")
    def test_07_failure_after_s3_before_dynamo_finalization_holds(self):
        self.ddb.fail_update=True;self.assertEqual(self.reserve()["decision"],"HOLD")
        self.ddb.fail_update=False;self.assertEqual(self.reserve()["decision"],"HOLD")
    def test_08_missing_object_holds(self):
        self.reserve();self.s3.objects.clear();self.assertEqual(self.reserve()["decision"],"HOLD")
    def test_09_tampered_content_holds(self):
        self.reserve();key=next(iter(self.s3.objects));self.s3.objects[key]["body"]=b"evil";
        self.assertEqual(self.reserve()["decision"],"HOLD")
    def test_10_governance_not_accepted(self):
        self.s3.invalid_retention=True;self.assertEqual(self.reserve()["decision"],"HOLD")
    def test_11_expired_retention_holds(self):
        self.reserve();key=next(iter(self.s3.objects));self.s3.objects[key]["until"]=datetime.now(timezone.utc)-timedelta(seconds=1)
        self.assertEqual(self.reserve()["decision"],"HOLD")
    def test_12_s3_get_forbidden_holds(self):
        self.reserve();self.s3.fail_read=True;self.assertEqual(self.reserve()["decision"],"HOLD")
    def test_13_s3_head_forbidden_holds(self):
        self.reserve();self.s3.fail_head=True;self.assertEqual(self.reserve()["decision"],"HOLD")
    def test_14_status_found_only_verified(self):
        self.reserve();r=self.ledger.status(self.args[1],self.args[2],self.args[3], identity=self.args[0]);self.assertEqual(r["decision"],"FOUND")
    def test_15_status_not_found(self):
        self.assertEqual(self.ledger.status(self.args[1],self.args[2],self.args[3], identity=self.args[0])["decision"],"NOT_FOUND")
    def test_16_invalid_identity_denied(self):
        self.assertEqual(self.ledger.reserve("","tenant-one",*self.args[2:])["decision"],"DENIED")
    def test_17_invalid_digest_denied(self):
        self.assertEqual(self.ledger.reserve(*self.args[:-2],"hello",self.now)["decision"],"DENIED")
    def test_18_concurrent_single_witness(self):
        barrier=threading.Barrier(12);out=[];lock=threading.Lock()
        def run():
            barrier.wait();r=self.reserve()
            with lock:out.append(r["decision"])
        threads=[threading.Thread(target=run) for _ in range(12)]
        [t.start() for t in threads];[t.join(15) for t in threads]
        self.assertEqual(out.count("WITNESSED"),1)
        self.assertEqual(len(self.s3.objects),1)
        self.assertTrue(set(out).issubset({"WITNESSED","DUPLICATE","HOLD"}))
    def test_19_no_gxp_authority_in_response(self):
        result=self.reserve()
        self.assertNotIn("gxp_approval",result);self.assertNotIn("execution_authorized",result)
    def test_20_denied_if_status_database_down(self):
        self.ddb.fail_read=True
        self.assertEqual(self.ledger.status(self.args[1],self.args[2],self.args[3], identity=self.args[0])["decision"],"HOLD")
    def test_21_idempotency_key_fingerprint(self):
        self.assertNotEqual(self.ledger._pk("t1","op","id"),self.ledger._pk("t2","op","id"))
    def test_22_database_deleted_after_witness_does_not_reauthorize(self):
        self.assertEqual(self.reserve()["decision"], "WITNESSED")
        self.ddb.records.clear()  # privileged tamper simulation, not permitted in design
        self.assertEqual(self.reserve()["decision"], "HOLD")
        self.assertEqual(len(self.s3.objects), 1)
    def test_23_readback_fails_closed(self):
        self.ddb.fail_read=True;self.assertEqual(self.reserve()["decision"],"HOLD")

if __name__ == "__main__":unittest.main()
