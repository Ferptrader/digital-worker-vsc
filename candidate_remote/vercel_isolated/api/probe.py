"""Synthetic-only Vercel proof: no GxP or production authority."""
from http.server import BaseHTTPRequestHandler
import hmac
import json
import os

class handler(BaseHTTPRequestHandler):
    def respond(self, code, payload):
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/api/health", "/api/health/"):
            return self.respond(200, {"status": "UP", "scope": "SYNTHETIC_ONLY",
                "jarvis_authoritative_connected": False, "gxp_authority": False})
        if self.path not in ("/api/probe", "/api/probe/"):
            return self.respond(404, {"status": "NOT_FOUND"})
        expected = os.environ.get("JARVIS_PREVIEW_BEARER_TOKEN", "")
        if len(expected) < 32:
            return self.respond(503, {"status": "AUTH_NOT_CONFIGURED",
                "jarvis_authoritative_connected": False})
        presented = self.headers.get("Authorization", "")
        if not hmac.compare_digest(presented, "Bearer " + expected):
            return self.respond(401, {"status": "UNAUTHORIZED"})
        return self.respond(200, {"status": "SYNTHETIC_AUTH_BOUNDARY_PASS",
            "execution_performed": False, "gxp_authority": False,
            "jarvis_authoritative_connected": False})
