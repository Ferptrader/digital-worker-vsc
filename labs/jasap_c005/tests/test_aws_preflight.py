"""No network, fake clients only. Cloud access is never claimed by these tests."""
import unittest
from aws_preflight import inspect


class AWSPreflightTests(unittest.TestCase):
    def test_same_account_is_blocked(self):
        result = inspect(None, table='t', bucket='b', anchor_account='123456789012', witness_account='123456789012')
        self.assertEqual(result['decision'], 'HOLD')
        self.assertEqual(result['checks']['separate_account_ids'], 'FAIL')

    def test_invalid_id_blocks(self):
        result = inspect(None, table='t', bucket='b', anchor_account='abc', witness_account='123456789012')
        self.assertEqual(result['decision'], 'HOLD')

    def test_missing_account_does_not_pass(self):
        class Missing:
            def client(self, service):
                raise PermissionError('unavailable')
        result = inspect(Missing(), table='t', bucket='b', anchor_account='123456789012', witness_account='234567890123')
        self.assertEqual(result['decision'], 'HOLD')
        self.assertEqual(result['checks']['aws_read_access'], 'FAIL_PermissionError')

    def test_healthy_mock_remains_not_qualified(self):
        class STS:
            def get_caller_identity(self): return {'Account':'123456789012', 'Arn':'arn:aws:iam::123456789012:role/Anchor'}
        class DDB:
            def describe_table(self, **kw): return {'Table': {'TableArn':'arn:aws:dynamodb:us-east-1:123456789012:table/t', 'TableStatus':'ACTIVE', 'DeletionProtectionEnabled':True}}
            def describe_continuous_backups(self, **kw): return {'ContinuousBackupsDescription': {'PointInTimeRecoveryDescription': {'PointInTimeRecoveryStatus':'ENABLED'}}}
        class S3:
            def get_bucket_versioning(self, **kw):return {'Status':'Enabled'}
            def get_object_lock_configuration(self, **kw): return {'ObjectLockConfiguration': {'ObjectLockEnabled':'Enabled', 'Rule':{'DefaultRetention': {'Mode':'COMPLIANCE','Days':7}}}}
            def list_object_versions(self, **kw): return {'IsTruncated':False, 'Versions':[]}
            def get_bucket_policy(self, **kw):
                import json
                return {'Policy':json.dumps({'Statement':[{'Effect':'Deny','Principal':'*',
                     'Action':['s3:DeleteObject','s3:DeleteObjectVersion'],
                     'Resource':'arn:aws:s3:::b/*'}]})}
            def get_public_access_block(self, **kw):return {'PublicAccessBlockConfiguration':{x:True for x in ('BlockPublicAcls','IgnorePublicAcls','BlockPublicPolicy','RestrictPublicBuckets')}}
        class Session:
            def client(self,name):return {'sts':STS(), 'dynamodb':DDB(), 's3':S3()}[name]
        result = inspect(Session(), table='t', bucket='b', anchor_account='123456789012', witness_account='234567890123')
        self.assertEqual(result['decision'], 'INFRASTRUCTURE_PRESENT_NOT_QUALIFIED')
        self.assertEqual(result['checks']['witness_object_lock'],'PASS')

    def test_wrong_caller_is_fail(self):
        class STS:
            def get_caller_identity(self): return {'Account':'999999999999','Arn':'arn:...'}
        class Fail:
            def client(self,name):
                if name=='sts':return STS()
                raise PermissionError()
        result=inspect(Fail(),table='t',bucket='b',anchor_account='123456789012',witness_account='234567890123')
        self.assertEqual(result['decision'],'HOLD')
        self.assertEqual(result['checks']['sts_anchor_identity'],'FAIL')

if __name__=='__main__':unittest.main()
