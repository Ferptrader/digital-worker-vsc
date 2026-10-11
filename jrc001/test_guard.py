"""JRC-001 negative configuration cases, no external services."""
import copy,json
from pathlib import Path
from jrc001.guard import verify_contract
def main():
    source=json.loads(Path("jrc001/integration_contract.json").read_text())
    assert verify_contract(source)
    cases=[]
    def reject(label,mutator):
        c=copy.deepcopy(source);mutator(c)
        try: verify_contract(c)
        except (RuntimeError,ValueError): cases.append(label);return
        raise AssertionError("unsafe contract accepted: "+label)
    reject("false_baseline",lambda c:c["baseline"].update(loaded_at_runtime=True))
    reject("false_authority",lambda c:c["component"].update(authoritative=True))
    reject("gxp_grant",lambda c:c["authority"].update(gxp_release=True))
    reject("customer_data",lambda c:c["interfaces"].update(customer_data_allowed=True))
    reject("request_body",lambda c:c["interfaces"].update(request_body_allowed=True))
    reject("risk_understatement",lambda c:c["risks"].update({"IDEMP-01":"PASS"}))
    reject("false_pass",lambda c:c["acceptance"].update(runtime_identity="PASS"))
    reject("bad_state",lambda c:c.update(state="ACTIVE"))
    from candidate_remote import render_server
    import inspect
    startup=inspect.getsource(render_server.main)
    assert startup.index("verify_file()")<startup.index("ThreadingHTTPServer(")
    report={"status":"PASS","safe_contract_accepted":True,"unsafe_contracts_denied":cases,"startup_guard_before_listener":True,"scope":"SYNTHETIC_ONLY"}
    Path("jrc001_guard_receipt.json").write_text(json.dumps(report,sort_keys=True,indent=2))
    print("JRC001_GUARD_RECEIPT="+json.dumps(report,sort_keys=True))
if __name__=="__main__":main()
