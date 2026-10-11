import unittest
from control_plane.independent_anchor_candidate import ExternalAnchorGuard, AnchorReceipt

class AnchorContractTests(unittest.TestCase):
    def test_missing_anchor_fails_closed(self):
        with self.assertRaises(RuntimeError):
            ExternalAnchorGuard(None).reserve("u","n",1)
    def test_valid_receipt(self):
        class Anchor:
            def reserve_once(self,i,n,t):
                return AnchorReceipt(True,i,n,"witness-1","v1")
        self.assertTrue(ExternalAnchorGuard(Anchor()).reserve("u","n",1))
    def test_duplicate_receipt(self):
        class Anchor:
            def reserve_once(self,i,n,t):
                return AnchorReceipt(False,i,n,"witness-2","v1")
        self.assertFalse(ExternalAnchorGuard(Anchor()).reserve("u","n",1))
    def test_identity_mismatch_fails(self):
        class Anchor:
            def reserve_once(self,i,n,t):
                return AnchorReceipt(True,"forged",n,"w","v1")
        with self.assertRaises(RuntimeError):
            ExternalAnchorGuard(Anchor()).reserve("u","n",1)
    def test_missing_witness_fails(self):
        class Anchor:
            def reserve_once(self,i,n,t):
                return AnchorReceipt(True,i,n,"","v1")
        with self.assertRaises(RuntimeError):
            ExternalAnchorGuard(Anchor()).reserve("u","n",1)
    def test_service_outage_fails(self):
        class Anchor:
            def reserve_once(self,i,n,t):
                raise ConnectionError("simulated outage")
        with self.assertRaises(ConnectionError):
            ExternalAnchorGuard(Anchor()).reserve("u","n",1)
if __name__=="__main__":unittest.main()
