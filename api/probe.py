"""Synthetic candidate health/probe endpoint. No user-controlled document paths."""
from http.server import BaseHTTPRequestHandler
import json
import hashlib
import tempfile
import time
from pathlib import Path
from control_plane.dispatcher import ControlPlane
from tools.jarvis_auth_gateway_candidate import sign_request
from tools.sqlite_replay_candidate import SQLiteReplayGuard

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/api/probe", "/api/probe/"):
            self.send_response(404); self.end_headers(); return
        try:
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                doc = root / "synthetic.txt"
                doc.write_text("Synthetic VSC candidate probe", encoding="utf-8")
                key = b"local-synthetic-only-not-credential"
                payload = {"operation":"extract_document","document_path":str(doc),"analysis_type":"requirements"}
                ts = int(time.time())
                nonce = "synthetic-probe-"+str(time.time_ns())
                envelope = {"identity":"synthetic-probe","timestamp":ts,"nonce":nonce,"payload":payload,
                            "signature":sign_request(key,"synthetic-probe",ts,nonce,payload)}
                control = ControlPlane(keys={"synthetic-probe":key},allowed_root=td,
                                       replay_guard=SQLiteReplayGuard(str(root/"nonce.sqlite")))
                result = control.dispatch(envelope,correlation_id="probe-candidate-001")
                body = {"status":"PASS" if result["status"]=="EXTRACTED_UNVERIFIED" else "FAIL",
                        "scope":"SYNTHETIC_EPHEMERAL_ONLY", "jarvis_authoritative_connected":False,
                        "gxp_authority":False, "response_sha256":result.get("response_sha256"),
                        "document_sha256":result.get("evidence",{}).get("sha256")}
                code = 200 if body["status"]=="PASS" else 503
        except Exception as exc:
            code=503
            body={"status":"FAIL","reason":type(exc).__name__}
        data=json.dumps(body,sort_keys=True).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(data)))
        self.end_headers()
        self.wfile.write(data)
