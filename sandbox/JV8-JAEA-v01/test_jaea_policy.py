import unittest
from jaea_policy import Request, evaluate

BASE = dict(run_id="SYN-001", tenant="synthetic-tenant",
            project="synthetic-project", action="analyze",
            environment="sandbox", synthetic=True)

class TestJAEA(unittest.TestCase):
    def test_dry_run_only(self):
        result = evaluate(Request(**BASE))
        self.assertEqual(result["decision"], "DRY_RUN_ONLY")
        self.assertFalse(result["dispatched"])
    def test_forbidden_even_with_human_flag(self):
        for action in ("approve", "release", "sign", "deploy", "delete", "write_production", "export_shared"):
            result = evaluate(Request(**{**BASE, "action": action, "human_authorized": True}))
            self.assertEqual(result["decision"], "DENY")
    def test_unknown_action(self):
        self.assertEqual(evaluate(Request(**{**BASE, "action": "arbitrary"}))["decision"], "HOLD")
    def test_non_synthetic(self):
        self.assertEqual(evaluate(Request(**{**BASE, "synthetic": False}))["decision"], "HOLD")
    def test_production(self):
        self.assertEqual(evaluate(Request(**{**BASE, "environment": "production"}))["decision"], "HOLD")
    def test_missing_scope(self):
        self.assertEqual(evaluate(Request(**{**BASE, "tenant": ""}))["decision"], "HOLD")
    def test_deterministic(self):
        self.assertEqual(evaluate(Request(**BASE)), evaluate(Request(**BASE)))

if __name__ == "__main__":
    unittest.main()
