import tempfile
import unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from tools.sqlite_replay_candidate import SQLiteReplayGuard

class SQLiteReplay(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=str(Path(self.tmp.name)/"replay.sqlite")
    def tearDown(self): self.tmp.cleanup()
    def test_reserve_and_duplicate(self):
        g=SQLiteReplayGuard(self.path)
        self.assertTrue(g.reserve("a","n",100))
        self.assertFalse(g.reserve("a","n",101))
    def test_restart_retains(self):
        self.assertTrue(SQLiteReplayGuard(self.path).reserve("a","n",1))
        self.assertFalse(SQLiteReplayGuard(self.path).reserve("a","n",2))
    def test_distinct_principals(self):
        g=SQLiteReplayGuard(self.path)
        self.assertTrue(g.reserve("a","n",1))
        self.assertTrue(g.reserve("b","n",1))
    def test_concurrent_only_one(self):
        g=SQLiteReplayGuard(self.path)
        with ThreadPoolExecutor(max_workers=8) as pool:
            results=list(pool.map(lambda _:g.reserve("a","same",1),range(8)))
        self.assertEqual(sum(results),1)
    def test_invalid_identity(self):
        self.assertFalse(SQLiteReplayGuard(self.path).reserve("","n",1))
    def test_separate_instances(self):
        a=SQLiteReplayGuard(self.path)
        b=SQLiteReplayGuard(self.path)
        self.assertTrue(a.reserve("u","nonce",1))
        self.assertFalse(b.reserve("u","nonce",1))
if __name__=="__main__":unittest.main()
