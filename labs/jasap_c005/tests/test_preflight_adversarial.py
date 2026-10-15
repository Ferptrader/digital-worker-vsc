"""Read-only AWS verification: negative cases against synthetic provider responses."""
import json
import unittest
from aws_preflight import inspect

ANCHOR = '123456789012'
WITNESS = '234567890123'

class SyntheticCloud:
    def __init__(self, lock='COMPLIANCE', delete_guard=True, can_list=True):
        self.lock = lock
        self.delete_guard = delete_guard
        self.can_list = can_list
    def client(self, name):
        if name == 'sts': return self
        if name == 'dynamodb': return self
        if name == 's3': return self
        raise KeyError(name)
    def get_caller_identity(self): return {'Account':ANCHOR,'Arn':f'arn:aws:iam::{ANCHOR}:role/LabAnchor'}
    def describe_table(self, **k):
        return {'Table':{'TableArn':f'arn:aws:dynamodb:us-east-1:{ANCHOR}:table/table',
                         'TableStatus':'ACTIVE','DeletionProtectionEnabled':True}}
    def describe_continuous_backups(self, **k):
        return {'ContinuousBackupsDescription': {'PointInTimeRecoveryDescription':{'PointInTimeRecoveryStatus':'ENABLED'}}}
    def get_bucket_versioning(self, **k): return {'Status':'Enabled'}
    def get_object_lock_configuration(self, **k):
        return {'ObjectLockConfiguration':{'ObjectLockEnabled':'Enabled',
               'Rule':{'DefaultRetention':{'Mode':self.lock,'Days':7}}}}
    def list_object_versions(self, **k):
        if not self.can_list: raise PermissionError('synthetic read denied')
        return {'IsTruncated': False, 'Versions': []}
    def get_bucket_policy(self, **k):
        guard={'Effect':'Deny','Principal':'*',
               'Action':['s3:DeleteObject','s3:DeleteObjectVersion'],
               'Resource':'arn:aws:s3:::bucket/*'}
        if not self.delete_guard: guard['Condition']={'StringEquals':{'aws:PrincipalTag/role':'test'}}
        return {'Policy':json.dumps({'Statement':[guard]})}
    def get_public_access_block(self, **k):
        return {'PublicAccessBlockConfiguration':{x:True for x in
             ('BlockPublicAcls','IgnorePublicAcls','BlockPublicPolicy','RestrictPublicBuckets')}}

def check(session):
    return inspect(session,table='table',bucket='bucket',anchor_account=ANCHOR,witness_account=WITNESS)

class AdversarialPreflight(unittest.TestCase):
    def test_01_complete_configuration_still_not_qualified(self):
        self.assertEqual(check(SyntheticCloud())['decision'],'INFRASTRUCTURE_PRESENT_NOT_QUALIFIED')
    def test_02_governance_default_rejected(self):
        v=check(SyntheticCloud(lock='GOVERNANCE'))
        self.assertEqual(v['decision'],'HOLD')
        self.assertEqual(v['checks']['witness_default_compliance'],'FAIL')
    def test_03_conditioned_policy_rejected(self):
        v=check(SyntheticCloud(delete_guard=False))
        self.assertEqual(v['decision'],'HOLD')
        self.assertEqual(v['checks']['witness_delete_policy'],'FAIL')
    def test_04_unavailable_history_rejected(self):
        v=check(SyntheticCloud(can_list=False))
        self.assertEqual(v['decision'],'HOLD')
        self.assertEqual(v['checks']['aws_read_access'],'FAIL_PermissionError')
    def test_05_botocore_models_expected_bucket_owner(self):
        from botocore.session import get_session
        model=get_session().get_service_model('s3')
        for name in ('PutObject','HeadObject','GetObject','ListObjectVersions'):
            self.assertIn('ExpectedBucketOwner', model.operation_model(name).input_shape.members)

if __name__ == '__main__': unittest.main()
