"""JAEA v0.1: isolated, deterministic DRY-RUN policy gate.

No network, filesystem writes, subprocesses, credentials, or production actions.
Not connected to the authoritative JARVIS runtime.
"""
from dataclasses import dataclass
from hashlib import sha256
import json

FORBIDDEN = frozenset({"approve", "release", "sign", "deploy", "delete", "write_production", "export_shared"})
ALLOWED = frozenset({"analyze", "draft", "simulate", "test_synthetic", "review"})

@dataclass(frozen=True)
class Request:
    run_id: str
    tenant: str
    project: str
    action: str
    environment: str
    synthetic: bool
    human_authorized: bool = False

def evaluate(req: Request) -> dict:
    """Produce a deterministic decision; never dispatch the requested action."""
    fields = [req.run_id, req.tenant, req.project, req.action, req.environment]
    if any(not isinstance(v, str) or not v.strip() for v in fields):
        verdict, reason = "HOLD", "missing_or_invalid_scope"
    elif req.action in FORBIDDEN:
        verdict, reason = "DENY", "authority_bound_action"
    elif req.action not in ALLOWED:
        verdict, reason = "HOLD", "unknown_action"
    elif req.environment != "sandbox" or req.synthetic is not True:
        verdict, reason = "HOLD", "isolation_unverified"
    else:
        verdict, reason = "DRY_RUN_ONLY", "preflight_pass_no_execution"
    record = {"run_id": req.run_id, "tenant": req.tenant,
              "project": req.project, "action": req.action,
              "environment": req.environment, "synthetic": req.synthetic,
              "decision": verdict, "reason": reason, "dispatched": False}
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":"))
    record["sha256"] = sha256(canonical.encode("utf-8")).hexdigest()
    return record
