"""Adversarial replay and recovery characterization, synthetic runner only."""
import concurrent.futures
import json
import shutil
import tempfile
from pathlib import Path
from tools.sqlite_replay_candidate import SQLiteReplayGuard

def run():
    checks={}
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        db=root/"state.sqlite"
        assert SQLiteReplayGuard(str(db)).reserve("client","nonce-1",1)
        assert not SQLiteReplayGuard(str(db)).reserve("client","nonce-1",2)
        checks["restart_denies_replay"]=True
        db.unlink()
        assert SQLiteReplayGuard(str(db)).reserve("client","nonce-1",3)
        checks["deletion_allows_replay"]=True
        db2=root/"rollback.sqlite"
        SQLiteReplayGuard(str(db2))
        snapshot=root/"old.snapshot"
        shutil.copy2(db2,snapshot)
        assert SQLiteReplayGuard(str(db2)).reserve("client","nonce-rollback",4)
        db2.unlink()
        shutil.copy2(snapshot,db2)
        assert SQLiteReplayGuard(str(db2)).reserve("client","nonce-rollback",5)
        checks["rollback_allows_replay"]=True
        concurrent_db=root/"concurrent.sqlite"
        SQLiteReplayGuard(str(concurrent_db))
        def attempt(i):
            return SQLiteReplayGuard(str(concurrent)).reserve("client","same-nonce",100+i)
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
            results=list(executor.map(attempt,range(24)))
        assert results.count(True)==1 and results.count(False)==23,results
        checks["concurrent_one_winner"]=True
        assert not hasattr(SQLiteReplayGuard(str(concurrent)),"reconcile_external_effect")
        checks["no_external_effect_reconciliation"]=True
    result={"status":"ADVERSARIAL_CHARACTERIZATION_PASS","checks":checks,
            "critical_risks":{"IDEMP-01":"OPEN_CRITICAL","IA-02":"OPEN_CRITICAL"},
            "external_effects":"UNKNOWN","gxp_release":"NOT_GRANTED",
            "disposition":"HOLD_NOT_QUALIFIED",
            "note":"PASS proves expected detection of vulnerabilities, not safe production operation"}
    Path("candidate_recovery_receipt.json").write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    print("JARVIS_RECOVERY_RECEIPT="+json.dumps(result,sort_keys=True))
if __name__=="__main__":
    run()
