import unittest
from pathlib import Path
import yaml

class GuardrailTemplate(unittest.TestCase):
    def test_explicit_s3_delete_denial(self):
        p=Path(__file__).resolve().parents[1]/"infra/witness-account.cfn.yaml"
        template=yaml.safe_load(p.read_text())
        policy=template["Resources"]["IndependentWitnessDenyDelete"]["Properties"]["PolicyDocument"]
        denials=[x for x in policy["Statement"] if x["Effect"]=="Deny"]
        self.assertTrue(any("s3:DeleteObject" in x["Action"] and "s3:DeleteObjectVersion" in x["Action"] for x in denials))
    def test_immutable_default(self):
        p=Path(__file__).resolve().parents[1]/"infra/witness-account.cfn.yaml"
        template=yaml.safe_load(p.read_text())
        assert template["Resources"]["IndependentWitnessBucket"]["Properties"]["ObjectLockConfiguration"]["Rule"]["DefaultRetention"]["Mode"]=="COMPLIANCE"
if __name__=="__main__":unittest.main()
