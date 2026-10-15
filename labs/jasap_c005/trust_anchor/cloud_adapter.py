"""C003 AWS DynamoDB + independently administered WORM S3 witness adapter.

Candidate / not deployed / not qualified. Never authorize GxP execution.
S3 PutObject and DynamoDB conditional transitions are NOT a distributed transaction.
If evidence publication or finalization is ambiguous, always HOLD.
"""
from __future__ import annotations
import hashlib
import base64
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from botocore.exceptions import ClientError, BotoCoreError
from .core import canonical

HEX64 = re.compile(r"^[0-9a-f]{64}$")
SAFE_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:-]{2,127}$")


def av(s: str) -> dict:
    return {"S": s}


class CloudLedger:
    """Fail-closed reservation adapter, with NO external business side effects.

    DynamoDB: only role in separate trust account can transact.
    S3: Object Lock COMPLIANCE bucket controlled by independent audit account.
    Runtime/agent MUST have access to neither bucket nor DynamoDB.
    """
    def __init__(self, dynamodb: Any, s3: Any, table_name: str, bucket: str,
                 *, expected_bucket_owner: str, retention_days: int = 7):
        if not (isinstance(expected_bucket_owner, str) and re.fullmatch(r"[0-9]{12}", expected_bucket_owner)):
            raise ValueError("EXPECTED_BUCKET_OWNER_REQUIRED")
        if not table_name or not bucket or not 1 <= retention_days <= 3650:
            raise ValueError("INVALID_CONFIG")
        self.ddb, self.s3, self.table, self.bucket = dynamodb, s3, table_name, bucket
        self.retention_days = retention_days
        self.expected_bucket_owner = expected_bucket_owner

    @staticmethod
    def _pk(tenant: str, operation: str, request_id: str) -> str:
        return hashlib.sha256(canonical({"t": tenant, "op": operation, "id": request_id})).hexdigest()

    def _get(self, pk: str) -> dict | None:
        result = self.ddb.get_item(TableName=self.table, Key={"pk": av(pk)}, ConsistentRead=True)
        return result.get("Item")

    def _verify_witness(self, item: dict) -> bool:
        try:
            if item["state"]["S"] != "WITNESSED":
                return False
            key = item["witness_key"]["S"]
            version = item["witness_version"]["S"]
            expected_sha = item["witness_digest"]["S"]
            metadata = self.s3.head_object(Bucket=self.bucket, Key=key, VersionId=version,
                                           ExpectedBucketOwner=self.expected_bucket_owner)
            if metadata.get("ObjectLockMode") != "COMPLIANCE":
                return False
            end = metadata.get("ObjectLockRetainUntilDate")
            if end is None or end <= datetime.now(timezone.utc):
                return False
            remote = self.s3.get_object(Bucket=self.bucket, Key=key, VersionId=version,
                                        ExpectedBucketOwner=self.expected_bucket_owner)
            data = remote["Body"].read()
            witness = json.loads(data)
            if not isinstance(witness, dict):
                return False
            expected = {
                "contract": "JASAP-C003-RESERVATION-v1",
                "pk": item["pk"]["S"],
                "tenant": item["tenant"]["S"],
                "operation": item["operation"]["S"],
                "request_id": item["request_id"]["S"],
                "identity": item["identity"]["S"],
                "digest": item["digest"]["S"],
                "created_at": int(item["created_at"]["N"]),
            }
            return (hashlib.sha256(data).hexdigest() == expected_sha
                    and witness == expected
                    and item["pk"]["S"] == self._pk(
                        expected["tenant"], expected["operation"], expected["request_id"]))
        except (KeyError, ValueError, TypeError, json.JSONDecodeError, ClientError, BotoCoreError, OSError):
            return False

    def _verdict(self, item: dict | None, digest: str | None = None, identity: str | None = None) -> dict:
        if item is None:
            return {"decision": "HOLD", "reason": "MISSING_RESERVATION_AFTER_CONFLICT"}
        if identity is not None and item.get("identity", {}).get("S") != identity:
            return {"decision": "DENIED", "reason": "IDENTITY_MISMATCH"}
        if digest is not None and item.get("digest", {}).get("S") != digest:
            return {"decision": "CONFLICT", "reason": "IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_DIGEST"}
        if not self._verify_witness(item):
            return {"decision": "HOLD", "reason": "WITNESS_NOT_VERIFIED"}
        return {"decision": "DUPLICATE" if digest is not None else "FOUND",
                "witness_id": item["witness_version"]["S"],
                "witness_sha256": item["witness_digest"]["S"]}

    def reserve(self, identity: str, tenant: str, operation: str, request_id: str,
                digest: str, now: int) -> dict:
        if not all(isinstance(x, str) and SAFE_ID.fullmatch(x) for x in (identity, tenant, operation, request_id)):
            return {"decision": "DENIED", "reason": "INVALID_IDENTIFIER"}
        if not isinstance(digest, str) or not HEX64.fullmatch(digest) or type(now) is not int:
            return {"decision": "DENIED", "reason": "INVALID_DIGEST_OR_TIME"}
        pk = self._pk(tenant, operation, request_id)
        # Historical WORM evidence is a mandatory precondition even when the
        # DynamoDB reservation has been deleted.  A missing/unavailable or
        # incomplete S3 version listing must never become a fresh reservation.
        # NOTE: this is a fail-closed laboratory gate, not an atomic
        # cross-service transaction or proof against concurrent privileged
        # tampering of both stores. Production still requires reconciliation
        # and an independently enforced fencing/authorization boundary.
        # Existing reservations must retain ordinary idempotent semantics.
        # Historical reconciliation only applies if the authoritative row
        # really is absent; otherwise duplicates would incorrectly HOLD.
        try:
            existing = self._get(pk)
        except (ClientError, BotoCoreError, OSError):
            return {"decision": "HOLD", "reason": "RESERVATION_READ_UNAVAILABLE"}
        if existing is not None:
            return self._verdict(existing, digest, identity)
        historical = self._status_without_db_row(pk)
        if historical["decision"] != "NOT_FOUND":
            return historical
        key = f"witness/v1/{pk}.json"  # one immutable version per reservation
        item = {"pk": av(pk), "tenant": av(tenant), "operation": av(operation),
                "request_id": av(request_id), "identity": av(identity),
                "digest": av(digest), "state": av("PENDING_WITNESS"),
                "witness_key": av(key), "created_at": {"N": str(now)}}
        try:
            self.ddb.put_item(TableName=self.table, Item=item,
                              ConditionExpression="attribute_not_exists(pk)")
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
                try:
                    return self._verdict(self._get(pk), digest, identity)
                except (ClientError, BotoCoreError, OSError):
                    return {"decision": "HOLD", "reason": "READ_AFTER_CONFLICT_FAILED"}
            return {"decision": "HOLD", "reason": "RESERVATION_UNAVAILABLE"}
        except (BotoCoreError, OSError, Exception):  # no unknown write may be retried blindly
            return {"decision": "HOLD", "reason": "RESERVATION_OUTCOME_UNKNOWN"}

        witness = {"contract": "JASAP-C003-RESERVATION-v1", "pk": pk, "tenant": tenant,
                   "operation": operation, "request_id": request_id, "identity": identity,
                   "digest": digest, "created_at": now}
        evidence = canonical(witness)
        evidence_hash = hashlib.sha256(evidence).hexdigest()
        expires = datetime.now(timezone.utc) + timedelta(days=self.retention_days)
        try:
            put = self.s3.put_object(Bucket=self.bucket, Key=key, Body=evidence,
                     ExpectedBucketOwner=self.expected_bucket_owner,
                     ContentType="application/json", ServerSideEncryption="AES256",
                     ObjectLockMode="COMPLIANCE", ObjectLockRetainUntilDate=expires,
                     IfNoneMatch="*", ContentMD5=base64.b64encode(hashlib.md5(evidence).digest()).decode("ascii"))
            version = put.get("VersionId")
            if not isinstance(version, str) or not version:
                return {"decision": "HOLD", "reason": "WITNESS_VERSION_MISSING"}
            # Confirm version-specific retention before accepting it.
            h = self.s3.head_object(Bucket=self.bucket, Key=key, VersionId=version,
                                    ExpectedBucketOwner=self.expected_bucket_owner)
            if h.get("ObjectLockMode") != "COMPLIANCE" or h.get("ObjectLockRetainUntilDate") is None or h["ObjectLockRetainUntilDate"] <= datetime.now(timezone.utc):
                return {"decision": "HOLD", "reason": "WORM_RETENTION_NOT_PROVEN"}
            self.ddb.update_item(TableName=self.table, Key={"pk": av(pk)},
                UpdateExpression="SET #st = :w, witness_version = :v, witness_digest = :h",
                ConditionExpression="#st = :p AND digest = :d",
                ExpressionAttributeNames={"#st": "state"},
                ExpressionAttributeValues={":w": av("WITNESSED"), ":p": av("PENDING_WITNESS"),
                                           ":d": av(digest), ":v": av(version), ":h": av(evidence_hash)})
            # The same independent evidence must be readable and match recorded digest.
            current = self._get(pk)
            if current is None or not self._verify_witness(current):
                return {"decision": "HOLD", "reason": "READBACK_WITNESS_INVALID"}
            return {"decision": "WITNESSED", "witness_id": version,
                    "witness_sha256": evidence_hash}
        except (ClientError, BotoCoreError, OSError, ValueError, TypeError):
            return {"decision": "HOLD", "reason": "WITNESS_OR_FINALIZATION_FAILED"}

    def _status_without_db_row(self, pk: str) -> dict:
        """Do not equate deleted reservation with unused identifier.

        Inspect the exact S3 key's historical versions AND delete markers.
        An ambiguous/error/truncated listing is always HOLD. This cannot
        guarantee recovery against an administrator controlling both stores.
        """
        key = f"witness/v1/{pk}.json"
        try:
            result = self.s3.list_object_versions(
                Bucket=self.bucket, Prefix=key, MaxKeys=1000,
                ExpectedBucketOwner=self.expected_bucket_owner)
            if result.get("IsTruncated") is not False:
                return {"decision": "HOLD", "reason": "WITNESS_HISTORY_INCOMPLETE"}
            for record in result.get("Versions", []) + result.get("DeleteMarkers", []):
                if record.get("Key") == key:
                    return {"decision": "HOLD", "reason": "ORPHAN_WITNESS_REQUIRES_RECONCILIATION"}
            return {"decision": "NOT_FOUND"}
        except (ClientError, BotoCoreError, OSError, ValueError, KeyError, TypeError):
            return {"decision": "HOLD", "reason": "WITNESS_HISTORY_UNAVAILABLE"}

    def status(self, tenant: str, operation: str, request_id: str, identity: str | None = None) -> dict:
        if not isinstance(identity, str) or not SAFE_ID.fullmatch(identity):
            return {"decision": "DENIED", "reason": "IDENTITY_REQUIRED"}
        if not all(isinstance(x, str) and SAFE_ID.fullmatch(x) for x in (tenant, operation, request_id)):
            return {"decision": "DENIED", "reason": "INVALID_IDENTIFIER"}
        try:
            item = self._get(self._pk(tenant, operation, request_id))
            if item is None:
                return self._status_without_db_row(self._pk(tenant, operation, request_id))
            return self._verdict(item, identity=identity)
        except (ClientError, BotoCoreError, OSError):
            return {"decision": "HOLD", "reason": "STATUS_UNAVAILABLE"}
