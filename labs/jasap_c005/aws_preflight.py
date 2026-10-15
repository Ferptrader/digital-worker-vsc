"""Read-only AWS account and resource readiness gate. Never provisions or mutates resources.

This preflight does not certify administrative independence or GxP suitability.
Requires actual AWS credentials with read permissions; missing credentials = FAIL.
"""
from __future__ import annotations
import argparse
import json
import re
from datetime import datetime, timezone


def inspect(session, *, table: str, bucket: str, anchor_account: str, witness_account: str):
    """Explicitly require two distinct expected AWS account IDs; do not infer or fabricate identity.

    Caller needs to be an anchor role in anchor account. S3 BucketOwner is verified
    using ExpectedBucketOwner on calls where supported, without any mutation.
    """
    result = {"decision": "HOLD", "assurance": "READ_ONLY_PREFLIGHT", "checks": {},
              "checked_at": datetime.now(timezone.utc).isoformat()}
    checks = result["checks"]
    if not (re.fullmatch(r"\d{12}", anchor_account) and
            re.fullmatch(r"\d{12}", witness_account) and
            anchor_account != witness_account):
        checks["separate_account_ids"] = "FAIL"
        return result
    checks["separate_account_ids"] = "PASS_CLAIMED_IDS_ONLY"
    try:
        sts = session.client("sts")
        caller = sts.get_caller_identity()
        result["caller_account"] = str(caller.get("Account", ""))
        result["caller_arn"] = str(caller.get("Arn", ""))
        checks["sts_anchor_identity"] = "PASS" if caller.get("Account") == anchor_account else "FAIL"
        ddb = session.client("dynamodb")
        desc = ddb.describe_table(TableName=table)["Table"]
        checks["ddb_account"] = "PASS" if f":{anchor_account}:table/" in desc.get("TableArn", "") else "FAIL"
        checks["ddb_active"] = "PASS" if desc.get("TableStatus") == "ACTIVE" else "FAIL"
        checks["ddb_pitr"] = "UNKNOWN"  # requires describe_continuous_backups; checked below
        backups = ddb.describe_continuous_backups(TableName=table)
        pitr = backups["ContinuousBackupsDescription"]["PointInTimeRecoveryDescription"]["PointInTimeRecoveryStatus"]
        checks["ddb_pitr"] = "PASS" if pitr == "ENABLED" else "FAIL"
        checks["ddb_deletion_protection"] = "PASS" if desc.get("DeletionProtectionEnabled") is True else "FAIL"
        s3 = session.client("s3")
        owner = {"Bucket": bucket, "ExpectedBucketOwner": witness_account}
        vers = s3.get_bucket_versioning(**owner)
        checks["witness_versioning"] = "PASS" if vers.get("Status") == "Enabled" else "FAIL"
        lock = s3.get_object_lock_configuration(**owner)
        configuration = lock.get("ObjectLockConfiguration", {})
        checks["witness_object_lock"] = "PASS" if configuration.get("ObjectLockEnabled") == "Enabled" else "FAIL"
        pab = s3.get_public_access_block(**owner)["PublicAccessBlockConfiguration"]
        checks["witness_public_access_block"] = "PASS" if all(pab.get(k) is True for k in
           ("BlockPublicAcls", "IgnorePublicAcls", "BlockPublicPolicy", "RestrictPublicBuckets")) else "FAIL"
        # Object Lock, versioning and PAB do NOT prove independent IAM or tamper-proof policies.
    except Exception as exc:
        # No client secrets or stack traces. Error type only in evidence.
        checks["aws_read_access"] = "FAIL_" + type(exc).__name__
        return result
    if all(value == "PASS" for key, value in checks.items() if key != "separate_account_ids"):
        result["decision"] = "INFRASTRUCTURE_PRESENT_NOT_QUALIFIED"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("table", "bucket", "region", "anchor-account", "witness-account"):
        parser.add_argument("--" + key, required=True)
    args = parser.parse_args()
    try:
        import boto3
        session = boto3.Session(region_name=args.region)
        verdict = inspect(session, table=args.table, bucket=args.bucket,
                          anchor_account=args.anchor_account, witness_account=args.witness_account)
    except Exception as exc:
        verdict = {"decision": "HOLD", "checks": {"aws_session": "FAIL_" + type(exc).__name__}}
    print(json.dumps(verdict, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if verdict["decision"] == "INFRASTRUCTURE_PRESENT_NOT_QUALIFIED" else 2

if __name__ == "__main__":
    raise SystemExit(main())
