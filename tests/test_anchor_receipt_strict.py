import unittest
from control_plane.independent_anchor_candidate import ExternalAnchorGuard, AnchorReceipt

class StrictReceiptRegression(unittest.TestCase):
    def test_boolean_accept(self):
        class Service:
            def reserve_once(self, identity, nonce, timestamp):
                return AnchorReceipt(True,identity,nonce,"w1","v1")
        self.assertTrue(ExternalAnchorGuard(Service()).reserve("client","nonce",1))
    def test_boolean_reject(self):
        class Service:
            def reserve_once(self, identity, nonce, timestamp):
                return AnchorReceipt(False,identity,nonce,"w2","v1")
        self.assertFalse(ExternalAnchorGuard(Service()).reserve("client","nonce",1))
    def test_string_decision_denied(self):
        class Service:
            def reserve_once(self, identity, nonce, timestamp):
                return AnchorReceipt("false",identity,nonce,"w3","v1")
        with self.assertRaises(RuntimeError):
            ExternalAnchorGuard(Service()).reserve("client","nonce",1)
    def test_numeric_decision_denied(self):
        class Service:
            def reserve_once(self, identity, nonce, timestamp):
                return AnchorReceipt(1,identity,nonce,"w4","v1")
        with self.assertRaises(RuntimeError):
            ExternalAnchorGuard(Service()).reserve("client","nonce",1)
    def test_invalid_witness_denied(self):
        class Service:
            def reserve_once(self, identity, nonce, timestamp):
                return AnchorReceipt(True,identity,nonce,123,"v1")
        with self.assertRaises(RuntimeError):
            ExternalAnchorGuard(Service()).reserve("client","nonce",1)
if __name__=="__main__":
    unittest.main()
