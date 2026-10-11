import unittest
from tools.jarvis_auth_gateway_candidate import MemoryReplayGuard

class ReplayKeyHardeningTests(unittest.TestCase):
    def test_delimiter_collision_does_not_block_distinct_identity(self):
        g=MemoryReplayGuard()
        nonce="1234567890123456"
        self.assertTrue(g.reserve("a:b",nonce,1000))
        self.assertTrue(g.reserve("a","b:"+nonce,1000))
    def test_same_identity_nonce_is_rejected(self):
        g=MemoryReplayGuard()
        self.assertTrue(g.reserve("client-a","1234567890123456",1000))
        self.assertFalse(g.reserve("client-a","1234567890123456",1001))
    def test_separate_identities_same_nonce_are_distinct(self):
        g=MemoryReplayGuard()
        self.assertTrue(g.reserve("client-a","1234567890123456",1000))
        self.assertTrue(g.reserve("client-b","1234567890123456",1000))
if __name__=="__main__":unittest.main()
