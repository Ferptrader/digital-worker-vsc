"""Independent anchor candidate — contracts and fail-closed adapter only.

No cloud resources or IAM are provisioned. An injected external anchor must
enforce atomic, durable conditional reservation independently of the worker.
A local SQLite implementation MUST NOT be treated as this interface's
production realization. The receipt alone is not an immutable witness.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class AnchorReceipt:
    accepted: bool
    identity: str
    nonce: str
    witness_id: str
    anchor_version: str

class IndependentAnchor(Protocol):
    def reserve_once(self, identity: str, nonce: str, timestamp: int) -> AnchorReceipt: ...

class ExternalAnchorGuard:
    """Adapt an independently administered anchor to existing reserve API.

    Always fail closed when the anchor is missing, unavailable, inconsistent,
    or returns a malformed receipt.
    """
    def __init__(self, anchor: IndependentAnchor | None):
        self.anchor = anchor

    def reserve(self, identity: str, nonce: str, now: int) -> bool:
        if self.anchor is None:
            raise RuntimeError("EXTERNAL_ANCHOR_UNAVAILABLE")
        receipt = self.anchor.reserve_once(identity, nonce, now)
        if not isinstance(receipt, AnchorReceipt):
            raise RuntimeError("INVALID_ANCHOR_RECEIPT")
        if receipt.identity != identity or receipt.nonce != nonce:
            raise RuntimeError("ANCHOR_RECEIPT_MISMATCH")
        if not receipt.anchor_version or not receipt.witness_id:
            raise RuntimeError("MISSING_ANCHOR_WITNESS")
        return receipt.accepted
