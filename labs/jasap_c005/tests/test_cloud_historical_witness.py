"""C005 hardening — historical S3 WORM evidence must gate missing DynamoDB rows.

AWS clients are synthetic. Tests demonstrate fail-closed code, NOT IAM/WORM in AWS.
"""
import unittest
from trust_anchor.cloud_adapter import CloudLedger
from test_cloud_adapter import FakeDDB, FakeS3


class HistoricalWitnessTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeDDB()
        self.s3 = FakeS3()
        self.ledger = CloudLedger(self.db, self.s3, "lab-table", "lab-witness",
                                  expected_bucket_owner="222222222222")
        self.args = ("lab-client", "tenant-one", "extract_document",
                     "lab-request-000000000001", "a"*64, 1792093200)

    def status(self):
        return self.ledger.status(self.args[1], self.args[2], self.args[3],
                                  identity=self.args[0])

    def test_01_missing_reservation_no_witness_not_found(self):
        self.assertEqual(self.status()["decision"], "NOT_FOUND")

    def test_02_db_deleted_worm_retained_status_holds(self):
        self.assertEqual(self.ledger.reserve(*self.args)["decision"], "WITNESSED")
        self.db.records.clear()
        result = self.status()
        self.assertEqual(result["decision"], "HOLD")
        self.assertEqual(result["reason"], "ORPHAN_WITNESS_REQUIRES_RECONCILIATION")

    def test_03_witness_history_access_denied_holds(self):
        self.s3.fail_versions = True
        self.assertEqual(self.status()["reason"], "WITNESS_HISTORY_UNAVAILABLE")

    def test_04_delete_marker_without_visible_current_item_holds(self):
        pk = self.ledger._pk(self.args[1], self.args[2], self.args[3])
        self.s3.hidden_current.add(f"witness/v1/{pk}.json")
        self.assertEqual(self.status()["decision"], "HOLD")

    def test_05_incomplete_listing_holds(self):
        original = self.s3.list_object_versions
        self.s3.list_object_versions = lambda **kw: {"Versions": [], "IsTruncated": True}
        self.assertEqual(self.status()["reason"], "WITNESS_HISTORY_INCOMPLETE")
        self.s3.list_object_versions = original

    def test_06_missing_truncated_flag_holds(self):
        self.s3.list_object_versions = lambda **kw: {"Versions": []}
        self.assertEqual(self.status()["reason"], "WITNESS_HISTORY_INCOMPLETE")

    def test_07_wrong_s3_owner_cannot_reserve(self):
        rogue = CloudLedger(self.db, self.s3, "lab-table", "lab-witness",
                            expected_bucket_owner="333333333333")
        result = rogue.reserve(*self.args)
        self.assertEqual(result["decision"], "HOLD")

    def test_08_wrong_s3_owner_cannot_conclude_not_found(self):
        rogue = CloudLedger(self.db, self.s3, "lab-table", "lab-witness",
                            expected_bucket_owner="333333333333")
        self.assertEqual(rogue.status(self.args[1], self.args[2], self.args[3],
                                      identity=self.args[0])["decision"], "HOLD")

    def test_09_owner_id_is_mandatory(self):
        with self.assertRaises(ValueError):
            CloudLedger(self.db, self.s3, "table", "bucket", expected_bucket_owner="")
        with self.assertRaises(ValueError):
            CloudLedger(self.db, self.s3, "table", "bucket", expected_bucket_owner="lab")

    def test_10_witness_verified_against_expected_owner(self):
        self.assertEqual(self.ledger.reserve(*self.args)["decision"], "WITNESSED")
        self.s3.owner = "333333333333"
        self.assertEqual(self.status()["decision"], "HOLD")

    def test_11_other_prefix_cannot_be_mistaken_for_orphan(self):
        pk = self.ledger._pk(self.args[1], self.args[2], self.args[3])
        self.s3.hidden_current.add(f"witness/v1/{pk}extra.json")
        self.assertEqual(self.status()["decision"], "NOT_FOUND")


if __name__ == '__main__':
    unittest.main()
