import pathlib
import unittest
import yaml

ROOT=pathlib.Path(__file__).resolve().parents[1]

class CandidateTemplateChecks(unittest.TestCase):
    def test_cloudformation_syntax_yaml(self):
        for name in ['anchor-account.cfn.yaml','witness-account.cfn.yaml']:
            doc=yaml.safe_load((ROOT/'infra'/name).read_text())
            self.assertIn('Resources',doc)
    def test_ddb_durable_and_delete_protection(self):
        res=yaml.safe_load((ROOT/'infra'/'anchor-account.cfn.yaml').read_text())['Resources']['ReservationTable']
        p=res['Properties']
        self.assertTrue(p['DeletionProtectionEnabled'])
        self.assertTrue(p['PointInTimeRecoverySpecification']['PointInTimeRecoveryEnabled'])
        self.assertEqual(res['DeletionPolicy'],'Retain')
    def test_s3_compliance_lock_enabled(self):
        res=yaml.safe_load((ROOT/'infra'/'witness-account.cfn.yaml').read_text())['Resources']['IndependentWitnessBucket']
        p=res['Properties']
        self.assertTrue(p['ObjectLockEnabled'])
        self.assertEqual(p['VersioningConfiguration']['Status'], 'Enabled')
        self.assertEqual(p['ObjectLockConfiguration']['Rule']['DefaultRetention']['Mode'],'COMPLIANCE')
        self.assertEqual(res['DeletionPolicy'],'Retain')
    def test_no_public_access(self):
        p=yaml.safe_load((ROOT/'infra'/'witness-account.cfn.yaml').read_text())['Resources']['IndependentWitnessBucket']['Properties']
        self.assertTrue(all(p['PublicAccessBlockConfiguration'].values()))
    def test_no_automated_external_executors(self):
        for name in ['anchor-account.cfn.yaml','witness-account.cfn.yaml']:
            for r in yaml.safe_load((ROOT/'infra'/name).read_text())['Resources'].values():
                self.assertNotIn(r['Type'], {'AWS::Lambda::Function','AWS::IAM::Role','AWS::ApiGateway::RestApi'})
