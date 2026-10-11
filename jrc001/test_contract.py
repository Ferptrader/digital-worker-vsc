"""JRC-001 contract invariant test. Synthetic candidate; no production authority."""
import json
from pathlib import Path
from control_plane.dispatcher import ControlPlane

def main():
    contract=json.loads(Path("jrc001/integration_contract.json").read_text())
    assert contract["change_id"]=="JRC-001"
    assert contract["baseline"]["loaded_at_runtime"] is False
    assert contract["component"]["authoritative"] is False
    assert contract["component"]["id"]=="JARVIS_CP_C001_UNQUALIFIED"
    assert contract["risks"]=={"IDEMP-01":"OPEN_CRITICAL","IA-02":"OPEN_CRITICAL"}
    assert all(value is False for value in contract["authority"].values())
    assert all(value=="HOLD" for key,value in contract["acceptance"].items() if key in ("runtime_identity","idempotency","recovery","independent_validation"))
    assert hasattr(ControlPlane,"dispatch")
    receipt={"status":"PASS","scope":"STATIC_CONTRACT_ONLY","checks":7,"runtime_authoritative":False,"gxp_qualified":False,"idempotency_verified":False,"external_effect_recovery_verified":False}
    Path("jrc001_contract_receipt.json").write_text(json.dumps(receipt,sort_keys=True,indent=2))
    print("JRC001_CONTRACT_RECEIPT="+json.dumps(receipt,sort_keys=True))

if __name__=="__main__":
    main()
