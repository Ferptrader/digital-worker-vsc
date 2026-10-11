"""Conservative JARVIS/Digital Worker VSC handoff boundary.

This module does NOT connect to a JARVIS runtime. A trusted caller must
provide a document path under an explicitly configured allowlisted root.
It emits unverified extraction evidence only; never approvals or executions.
"""
from __future__ import annotations
import json
from typing import Any
from tools.safe_document_core import analyze_document

ALLOWED_OPERATIONS = frozenset({"extract_document"})

def handle_jarvis_request(request: dict[str, Any], *, allowed_root: str) -> dict[str, Any]:
    """Fail-closed adapter for future authenticated JARVIS dispatcher."""
    base = {
        "integration": "JARVIS_DWVSC_CANDIDATE",
        "status": "NOT_VERIFIED",
        "gxp_compliance": "NOT_VERIFIED",
        "gxp_approval": "NOT_GRANTED",
        "gxp_release": "NOT_GRANTED",
        "execution_authorized": False,
        "reason": "INVALID_REQUEST",
        "evidence": None,
    }
    if not isinstance(request, dict):
        return base
    # Identity / permission must be enforced by an external trusted gateway;
    # the request content itself MUST NOT be treated as authority.
    if request.get("operation") not in ALLOWED_OPERATIONS:
        return {**base, "reason": "OPERATION_NOT_ALLOWED"}
    if any(k in request for k in ("approve", "release", "execute", "authority", "identity_override")):
        return {**base, "reason": "AUTHORITY_FIELDS_REJECTED"}
    path, kind = request.get("document_path"), request.get("analysis_type")
    if not isinstance(path, str) or not path or not isinstance(kind, str):
        return base
    result = analyze_document(path, kind, allowed_root)
    return {**base, **result, "integration": "JARVIS_DWVSC_CANDIDATE", "execution_authorized": False}

def handle_jarvis_json(payload: str, *, allowed_root: str) -> str:
    try:
        obj = json.loads(payload)
        result = handle_jarvis_request(obj, allowed_root=allowed_root)
    except (ValueError, TypeError):
        result = handle_jarvis_request({}, allowed_root=allowed_root)
    return json.dumps(result, ensure_ascii=False, sort_keys=True)
