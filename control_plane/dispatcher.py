"""JARVIS Control Plane C001: isolated, deny-by-default prototype.
No HTTP endpoint, no deployment, no production effects, no GxP approvals.
"""
from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass
from typing import Any
from tools.jarvis_auth_gateway_candidate import process_authenticated

@dataclass(frozen=True)
class ControlPlane:
    keys: dict[str, bytes]
    allowed_root: str
    replay_guard: Any

    def dispatch(self, envelope: dict[str, Any], *, correlation_id: str) -> dict[str, Any]:
        denied = {"status": "NOT_VERIFIED", "reason": "INVALID_CORRELATION",
                  "execution_authorized": False, "gxp_release": "NOT_GRANTED",
                  "gxp_approval": "NOT_GRANTED", "gxp_compliance": "NOT_VERIFIED"}
        if not isinstance(correlation_id, str) or not (8 <= len(correlation_id) <= 128):
            return denied
        # Correlation is caller-provided reference only, not proof of identity.
        response = process_authenticated(
            envelope, keys=self.keys, allowed_root=self.allowed_root, guard=self.replay_guard
        )
        # Ensure no underlying component may widen these hard invariants.
        response = dict(response)
        response["execution_authorized"] = False
        response["gxp_approval"] = "NOT_GRANTED"
        response["gxp_release"] = "NOT_GRANTED"
        response["gxp_compliance"] = "NOT_VERIFIED"
        response["correlation_id"] = correlation_id
        response["control_plane"] = "JARVIS_CP_C001_UNQUALIFIED"
        response["response_sha256"] = hashlib.sha256(json.dumps(
            {k:v for k,v in response.items() if k != "response_sha256"},
            sort_keys=True, ensure_ascii=False, default=str
        ).encode("utf-8")).hexdigest()
        return response
