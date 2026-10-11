"""Synthetic Render preview: startup integration verification, no secret disclosure."""
import json
import os
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from api.probe import handler

def _get(url, token=None):
    headers={"Authorization":"Bearer "+token} if token else {}
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=30) as res:
            return res.status,json.loads(res.read(16000))
    except urllib.error.HTTPError as e:
        return e.code,json.loads(e.read(16000))

def main():
    port=int(os.environ.get("PORT","10000"))
    token=os.environ.get("JARVIS_PREVIEW_BEARER_TOKEN","")
    if len(token)<32:
        raise RuntimeError("Preview bearer token not configured")
    server=ThreadingHTTPServer(("0.0.0.0",port),handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    url="http://127.0.0.1:"+str(port)
    health,hb=_get(url+"/api/health")
    denied,db=_get(url+"/api/probe")
    accepted,ab=_get(url+"/api/probe",token)
    checks={"health":health==200 and hb.get("status")=="UP",
            "anonymous_denied":denied==401 and db.get("status")=="UNAUTHORIZED",
            "authenticated_success":accepted==200 and ab.get("status")=="PASS",
            "sha256_present":isinstance(ab.get("document_sha256"),str) and len(ab["document_sha256"])==64,
            "authority_ungranted":ab.get("gxp_authority") is False and ab.get("jarvis_authoritative_connected") is False}
    print("JARVIS_STARTUP_AUTH_RECEIPT="+json.dumps({"checks":checks,"scope":"SYNTHETIC_ONLY","overall":"PASS" if all(checks.values()) else "FAIL"},sort_keys=True),flush=True)
    if not all(checks.values()):
        raise RuntimeError("Startup authentication validation failed")
    print("JARVIS synthetic preview serving port "+str(port),flush=True)
    threading.Event().wait()

if __name__=="__main__":
    main()
