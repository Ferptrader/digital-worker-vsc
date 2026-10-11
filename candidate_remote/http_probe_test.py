"""Exercise candidate HTTP handler on ephemeral loopback in GitHub Actions."""
import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from api.probe import handler

server=ThreadingHTTPServer(("127.0.0.1",0),handler)
thread=threading.Thread(target=server.serve_forever,daemon=True)
thread.start()
try:
    root=f"http://127.0.0.1:{server.server_port}"
    with urllib.request.urlopen(root+"/api/probe",timeout=15) as response:
        assert response.status==200
        assert response.headers.get("Cache-Control")=="no-store"
        result=json.load(response)
    assert result["status"]=="PASS",result
    assert result["scope"]=="SYNTHETIC_EPHEMERAL_ONLY"
    assert result["jarvis_authoritative_connected"] is False
    assert result["gxp_authority"] is False
    assert len(result["response_sha256"])==64
    assert len(result["document_sha256"])==64
    try:
        urllib.request.urlopen(root+"/invalid-route",timeout=15)
        raise AssertionError("unknown route must be 404")
    except urllib.error.HTTPError as e:
        assert e.code==404
    receipt={"http_status":200,"unknown_route_status":404,"endpoint":"/api/probe","result":result,
             "execution_environment":"GitHub Actions ephemeral loopback",
             "public_endpoint_available":False,"authoritative_jarvis_connected":False,
             "disposition":"CANDIDATE_HOLD_NOT_QUALIFIED"}
    Path("candidate_remote_http_receipt.json").write_text(json.dumps(receipt,sort_keys=True,indent=2),encoding="utf-8")
    print("JARVIS_HTTP_RECEIPT="+json.dumps(receipt,sort_keys=True))
finally:
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)
