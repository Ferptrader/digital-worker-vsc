"""Isolated JARVIS -> Control Plane -> Digital Worker smoke proof.
Synthetic input only. No production effects or GxP authorization.
"""
import hashlib
import json
import tempfile
import time
from pathlib import Path
from control_plane.dispatcher import ControlPlane
from tools.jarvis_auth_gateway_candidate import sign_request
from tools.sqlite_replay_candidate import SQLiteReplayGuard

def run_proof():
    with tempfile.TemporaryDirectory(prefix="jarvis-candidate-") as tmp:
        root = Path(tmp)
        document = root / "synthetic_urs.txt"
        document.write_text("URS-001 synthetic audit trail requirement", encoding="utf-8")
        key = b"synthetic-only-key-not-for-production"
        identity = "synthetic-client"
        payload = {"operation": "extract_document", "document_path": str(document), "analysis_type": "requirements"}
        ts = int(time.time())
        nonce = "synthetic-unique-nonce-0001"
        envelope = {"identity": identity, "timestamp": ts, "nonce": nonce, "payload": payload,
                    "signature": sign_request(key, identity, ts, nonce, payload)}
        db = root / "replay.sqlite"
        def dispatcher():
            return ControlPlane(keys={identity: key}, allowed_root=tmp, replay_guard=SQLiteReplayGuard(str(db)))
        result = dispatcher().dispatch(envelope, correlation_id="remote-proof-0001")
        repeated = dispatcher().dispatch(envelope, correlation_id="remote-proof-0002")
        tampered = dict(envelope)
        tampered["payload"] = dict(payload, analysis_type="risk")
        denied = dispatcher().dispatch(tampered, correlation_id="remote-proof-0003")
        assert result["status"] == "EXTRACTED_UNVERIFIED", result
        assert result["evidence"]["sha256"] == hashlib.sha256(document.read_bytes()).hexdigest()
        assert result["gxp_approval"] == result["gxp_release"] == "NOT_GRANTED"
        assert result["execution_authorized"] is False
        assert repeated["reason"] == "REPLAY_REJECTED", repeated
        assert denied["reason"] == "AUTHORIZATION_FAILED", denied
        assert len(result["response_sha256"]) == 64
        return {"result": "LOCAL_OR_RUNNER_SYNTHETIC_PASS", "authenticated_extraction": True,
                "duplicate_after_guard_restart": "REPLAY_REJECTED",
                "tampered_payload": "AUTHORIZATION_FAILED",
                "document_sha256": result["evidence"]["sha256"],
                "response_sha256": result["response_sha256"],
                "correlation_id": result["correlation_id"],
                "gxp_approval": result["gxp_approval"],
                "authoritative_jarvis_runtime": "NOT_CONNECTED",
                "independent_witness": "NOT_QUALIFIED",
                "disposition": "CANDIDATE_HOLD"}

if __name__ == "__main__":
    print("JARVIS_REMOTE_CANDIDATE_PROOF=" + json.dumps(run_proof(), sort_keys=True))
