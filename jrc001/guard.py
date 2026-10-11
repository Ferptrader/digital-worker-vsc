"""JRC001 startup boundary guard."""
import json
from pathlib import Path
def verify_contract(c):
    if not isinstance(c,dict): raise RuntimeError("INVALID_CONTRACT")
    if (c.get("change_id"),c.get("state"))!=("JRC-001","CANDIDATE_HOLD_NOT_QUALIFIED"): raise RuntimeError("INVALID_STATE")
    if c.get("baseline",{}).get("loaded_at_runtime") is not False: raise RuntimeError("BASELINE_CLAIM")
    if c.get("component",{}).get("authoritative") is not False: raise RuntimeError("AUTHORITY_CLAIM")
    a=c.get("authority",{})
    if not isinstance(a,dict) or set(a)!={"gxp_approval","gxp_release","gxp_signature","production_write","production_delete","shared_learning"} or any(v is not False for v in a.values()): raise RuntimeError("AUTHORITY_ESCALATION")
    if c.get("interfaces",{}).get("customer_data_allowed") is not False or c.get("interfaces",{}).get("request_body_allowed") is not False: raise RuntimeError("UNSAFE_INTERFACE")
    if c.get("risks")!={"IDEMP-01":"OPEN_CRITICAL","IA-02":"OPEN_CRITICAL"}: raise RuntimeError("FALSE_RISK_PASS")
    if any(c.get("acceptance",{}).get(k)!="HOLD" for k in ("runtime_identity","idempotency","recovery","independent_validation")): raise RuntimeError("FALSE_PASS")
    return True
def verify_file():
    return verify_contract(json.loads(Path(__file__).with_name("integration_contract.json").read_text()))
