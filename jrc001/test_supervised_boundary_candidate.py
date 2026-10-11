"""JRC-001 supervised boundary negative regression tests. No external side effects."""
import copy
import json
from pathlib import Path
from jrc001.guard import verify_contract

BASE = json.loads(Path(__file__).with_name("integration_contract.json").read_text(encoding="utf-8"))

def verify():
    cases = []
    def reject(name, path, value):
        contract = copy.deepcopy(BASE)
        node = contract
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] = value
        try:
            verify_contract(contract)
        except (RuntimeError, TypeError, AttributeError, KeyError):
            cases.append({"case": name, "result": "PASS_BLOCKED"})
        else:
            raise AssertionError("FAIL_OPEN: " + name)

    assert verify_contract(BASE) is True
    cases.append({"case": "unaltered candidate contract", "result": "PASS_ACCEPTED_HOLD"})
    for name, path, value in [
        ("baseline loaded claim", ["baseline", "loaded_at_runtime"], True),
        ("authoritative claim", ["component", "authoritative"], True),
        ("GxP approval escalation", ["authority", "gxp_approval"], True),
        ("GxP release escalation", ["authority", "gxp_release"], True),
        ("GxP signature escalation", ["authority", "gxp_signature"], True),
        ("production write escalation", ["authority", "production_write"], True),
        ("production delete escalation", ["authority", "production_delete"], True),
        ("shared learning escalation", ["authority", "shared_learning"], True),
        ("request body enabled", ["interfaces", "request_body_allowed"], True),
        ("customer data enabled", ["interfaces", "customer_data_allowed"], True),
        ("idempotency false pass", ["acceptance", "idempotency"], "PASS"),
        ("recovery false pass", ["acceptance", "recovery"], "PASS"),
        ("runtime identity false pass", ["acceptance", "runtime_identity"], "PASS"),
        ("independent validation false pass", ["acceptance", "independent_validation"], "PASS"),
        ("critical risk downgraded", ["risks", "IDEMP-01"], "CLOSED"),
        ("incorrect candidate state", ["state"], "ACTIVE"),
    ]:
        reject(name, path, value)
    print(json.dumps({"scope": "ISOLATED_CANDIDATE", "total": len(cases), "passed": len(cases), "failed": 0, "cases": cases}, sort_keys=True))

if __name__ == "__main__":
    verify()
