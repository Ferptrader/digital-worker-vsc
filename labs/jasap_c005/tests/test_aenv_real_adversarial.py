"""AENV-REAL-001: adversarial acceptance gates for the actual C005 CloudLedger.

Uses version-aware synthetic AWS doubles. This is *not* a claim of deployed
AWS isolation, WORM effectiveness, or GxP qualification.
"""
import unittest
from trust_anchor.cloud_adapter import CloudLedger
from test_cloud_adapter import FakeDDB, FakeS3


class MarkerAwareFakeS3(FakeS3):
    """S3 versioning edge case: If-None-Match:* can accept a new put when
    the current version is a delete marker, while older locked versions exist.
    This double keeps the older witness in archive rather than deleting it.
    """
    def __init__(self):
        super().__init__()
        self.archived_immutable_versions = {}

    def put_object(self, **kwargs):
        key = kwargs["Key"]
        if key in self.hidden_current:
            old = self.objects.pop(key, None)
            if old is not None:
                self.archived_immutable_versions.setdefault(key, []).append(old)
            # The current delete marker is replaced by a new current version.
            self.hidden_current.discard(key)
        return super().put_object(**kwargs)

    def list_object_versions(self, **kwargs):
        page = super().list_object_versions(**kwargs)
        prefix = kwargs["Prefix"]
        for key, versions in self.archived_immutable_versions.items():
            if key.startswith(prefix):
                page["Versions"].extend(
                    {"Key": key, "VersionId": v["version"]} for v in versions
                )
        return page


class RealCloudLedgerAdversarialGates(unittest.TestCase):
    def setUp(self):
        self.ddb, self.s3 = FakeDDB(), MarkerAwareFakeS3()
        self.ledger = CloudLedger(self.ddb, self.s3, "lab-ddb", "lab-worm",
                                  expected_bucket_owner="222222222222")
        self.args = ("lab-client", "tenant-one", "extract_document",
                     "aenv-request-0000000001", "a" * 64, 1792093200)

    def test_a01_deleted_reservation_plus_current_delete_marker_holds(self):
        self.assertEqual(self.ledger.reserve(*self.args)["decision"], "WITNESSED")
        key = next(iter(self.s3.objects))
        original = bytes(self.s3.objects[key]["body"])
        self.ddb.records.clear()  # privileged deletion, adversarial simulation
        self.s3.hidden_current.add(key)  # current marker, historical WORM remains
        before = self.ledger.status(*self.args[1:4], identity=self.args[0])
        self.assertEqual(before["decision"], "HOLD")
        result = self.ledger.reserve(*self.args)
        self.assertEqual(result["decision"], "HOLD", result)
        self.assertEqual(result.get("reason"), "ORPHAN_WITNESS_REQUIRES_RECONCILIATION")
        self.assertEqual(bytes(self.s3.objects[key]["body"]), original)
        self.assertEqual(self.s3.archived_immutable_versions, {})

    def test_a02_unavailable_history_must_not_be_treated_as_empty(self):
        self.s3.fail_versions = True
        result = self.ledger.reserve(*self.args)
        self.assertEqual(result["decision"], "HOLD", result)
        self.assertEqual(result.get("reason"), "WITNESS_HISTORY_UNAVAILABLE")
        self.assertEqual(len(self.ddb.records), 0)
        self.assertEqual(len(self.s3.objects), 0)

    def test_a03_clean_history_allows_exactly_one_first_reservation(self):
        first = self.ledger.reserve(*self.args)
        self.assertEqual(first["decision"], "WITNESSED")
        duplicate = self.ledger.reserve(*self.args)
        self.assertEqual(duplicate["decision"], "DUPLICATE")
        self.assertEqual(len(self.s3.objects), 1)

    def test_a04_orphan_status_is_not_authorization(self):
        self.assertEqual(self.ledger.reserve(*self.args)["decision"], "WITNESSED")
        self.ddb.records.clear()
        decision = self.ledger.status(*self.args[1:4], identity=self.args[0])
        self.assertEqual(decision["decision"], "HOLD")
        self.assertNotIn("execution_authorized", decision)
        self.assertNotIn("gxp_approval", decision)


if __name__ == "__main__":
    unittest.main()
