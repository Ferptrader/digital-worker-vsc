"""AENV-REAL-001: extra adversarial race and reconciliation tests.
Only FakeDDB/FakeS3; these do not prove real AWS IAM/WORM behavior.
"""
import unittest
from trust_anchor.cloud_adapter import CloudLedger
from test_cloud_adapter import FakeDDB, FakeS3


class RaceAndRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.db, self.s3 = FakeDDB(), FakeS3()
        self.ledger = CloudLedger(self.db, self.s3, "lab-table", "lab-bucket",
                                  expected_bucket_owner="222222222222")
        self.args = ("client-001", "tenant-001", "extract_document",
                     "request-0000000000001", "a" * 64, 1792093200)

    def test_preflight_toctou_exposes_simulator_gap(self):
        # Inject privileged history mutation just after the preflight list.
        original = self.s3.list_object_versions
        pk = self.ledger._pk(self.args[1], self.args[2], self.args[3])
        key = f"witness/v1/{pk}.json"
        def race(**kwargs):
            result = original(**kwargs)
            self.s3.hidden_current.add(key)
            return result
        self.s3.list_object_versions = race
        # The FakeS3 put is not a faithful S3 delete-marker emulator.
        # Assert only that the simulator can expose this missing semantic.
        self.assertEqual(self.ledger.reserve(*self.args)["decision"], "WITNESSED")
        # This is an EXPECTED GAP, not a passing security assertion.
        self.assertIn(key, self.s3.hidden_current)
        self.assertEqual(len(self.db.records), 1)

    def test_failed_witness_write_does_not_retry_blindly(self):
        self.s3.fail_write = True
        self.assertEqual(self.ledger.reserve(*self.args)["decision"], "HOLD")
        self.s3.fail_write = False
        self.assertEqual(self.ledger.reserve(*self.args)["decision"], "HOLD")

    def test_unavailable_history_blocks_clean_reservation(self):
        self.s3.fail_versions = True
        self.assertEqual(self.ledger.reserve(*self.args)["decision"], "HOLD")
        self.assertEqual(len(self.db.records), 0)


if __name__ == "__main__":
    unittest.main()
