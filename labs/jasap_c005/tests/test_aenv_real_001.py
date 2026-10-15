"""AENV-REAL-001: adversarial checks against the real C005 cloud adapter.
Synthetic AWS clients only. No production services or data are modified.
"""
import unittest
from trust_anchor.cloud_adapter import CloudLedger
from test_cloud_adapter import FakeDDB, FakeS3


class WitnessPreflightTests(unittest.TestCase):
    def setUp(self):
        self.ddb = FakeDDB()
        self.s3 = FakeS3()
        self.ledger = CloudLedger(self.ddb, self.s3, "lab-table", "lab-bucket",
                                  expected_bucket_owner="222222222222")
        self.args = ("client-001", "tenant-001", "extract_document",
                     "request-0000000000001", "a" * 64, 1792093200)

    def test_new_reservation_succeeds_with_clean_history(self):
        self.assertEqual(self.ledger.reserve(*self.args)["decision"], "WITNESSED")

    def test_same_request_remains_duplicate(self):
        self.assertEqual(self.ledger.reserve(*self.args)["decision"], "WITNESSED")
        self.assertEqual(self.ledger.reserve(*self.args)["decision"], "DUPLICATE")

    def test_changed_payload_conflicts(self):
        self.ledger.reserve(*self.args)
        changed = (*self.args[:-2], "b" * 64, self.args[-1])
        self.assertEqual(self.ledger.reserve(*changed)["decision"], "CONFLICT")

    def test_deleted_database_with_retained_version_holds(self):
        self.ledger.reserve(*self.args)
        self.ddb.records.clear()
        self.assertEqual(self.ledger.reserve(*self.args)["decision"], "HOLD")

    def test_deleted_database_with_delete_marker_holds_before_write(self):
        pk = self.ledger._pk(self.args[1], self.args[2], self.args[3])
        self.s3.hidden_current.add(f"witness/v1/{pk}.json")
        self.assertEqual(self.ledger.reserve(*self.args)["decision"], "HOLD")
        self.assertEqual(len(self.ddb.records), 0)

    def test_incomplete_history_holds_before_write(self):
        self.s3.list_object_versions = lambda **kw: {"Versions": [], "IsTruncated": True}
        self.assertEqual(self.ledger.reserve(*self.args)["decision"], "HOLD")
        self.assertEqual(len(self.ddb.records), 0)

    def test_history_unavailable_holds_before_write(self):
        self.s3.fail_versions = True
        self.assertEqual(self.ledger.reserve(*self.args)["decision"], "HOLD")
        self.assertEqual(len(self.ddb.records), 0)

    def test_wrong_bucket_owner_holds(self):
        self.s3.owner = "333333333333"
        self.assertEqual(self.ledger.reserve(*self.args)["decision"], "HOLD")
        self.assertEqual(len(self.ddb.records), 0)


if __name__ == "__main__":
    unittest.main()
