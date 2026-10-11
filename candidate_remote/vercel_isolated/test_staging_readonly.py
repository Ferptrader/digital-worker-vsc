"""Read-only authenticated deployment diagnostic. No secret exposure, no production writes."""
import json
import os
import urllib.error
import urllib.request

BASE = os.environ.get("JARVIS_STAGING_URL", "").rstrip("/")
if not BASE.startswith("https://") or ".vercel.app" not in BASE:
    raise SystemExit("STAGING_URL_REQUIRED")
if "jarvis-python-isolated-20261011" not in BASE:
    raise SystemExit("UNAPPROVED_HOST")
results = []
for path in ("/api/health", "/api/probe"):
    req = urllib.request.Request(BASE + path, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            status, body = response.status, response.read(2048).decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        status, body = exc.code, exc.read(2048).decode("utf-8", "replace")
    except Exception as exc:
        results.append({"path":path,"verdict":"NOT_VERIFIED","transport_error":type(exc).__name__})
        continue
    try:
        parsed = json.loads(body)
    except ValueError:
        parsed = None
    verdict = "NOT_VERIFIED"
    if path == "/api/health" and status == 200 and isinstance(parsed,dict) and parsed.get("scope") == "SYNTHETIC_ONLY":
        verdict = "HEALTH_ONLY_PASS"
    if path == "/api/probe" and status == 503 and isinstance(parsed,dict) and parsed.get("status") == "AUTH_NOT_CONFIGURED":
        verdict = "FAIL_CLOSED_EXPECTED"
    if path == "/api/probe" and status == 401 and isinstance(parsed,dict) and parsed.get("status") == "UNAUTHORIZED":
        verdict = "ANONYMOUS_DENIAL_PASS"
    results.append({"path":path,"status":status,"verdict":verdict})
print(json.dumps({"scope":"STAGING_READ_ONLY","results":results,"gxp_qualified":False,"runtime_authoritative":False},sort_keys=True))
