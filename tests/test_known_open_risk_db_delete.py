"""Negative proof for an OPEN control gap. A passing demonstration is a SECURITY FAILURE,
not successful replay protection. Synthetic data only; no production resources.
"""
import tempfile
import unittest
from pathlib import Path
from tools.sqlite_replay_candidate import SQLiteReplayGuard

class KnownOpenRisk(unittest.TestCase):
    def test_deleted_sqlite_reservation_allows_reuse(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/"nonce.sqlite"
            guard=SQLiteReplayGuard(str(db))
            self.assertTrue(guard.reserve("synthetic-tenant","synthetic-nonce",1))
            self.assertFalse(guard.reserve("synthetic-tenant","synthetic-nonce",2))
            db.unlink()  # simulate privileged local database deletion; no production data
            recreated=SQLiteReplayGuard(str(db))
            bypass=recreated.reserve("synthetic-tenant","synthetic-nonce",3)
            # This MUST remain explicitly documented as an UNRESOLVED weakness.
            self.assertTrue(bypass, "Expected synthetic replay bypass is no longer reproducible: reassess control")
            print("SECURITY GAP REPRODUCED: deleting SQLite allows nonce reuse; IDEMP-01 remains OPEN/HOLD")

if __name__ == "__main__":
    unittest.main()
