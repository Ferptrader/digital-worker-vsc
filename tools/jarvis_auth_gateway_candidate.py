"""Standalone authenticated request boundary. Candidate only; not a deployed JARVIS runtime.

HMAC authorizes a specific request signed by an out-of-band trusted caller.
Replay protection requires an explicitly supplied durable guard; it remains\nNOT QUALIFIED without independent storage integrity and multi-host validation. No GxP authority is delegated to document contents.
"""
from __future__ import annotations
import hashlib
import hmac
import json
import threading
import time
from typing import Any, Callable
from tools.jarvis_handoff_candidate import handle_jarvis_request

MAX_SKEW_SECONDS = 120

class MemoryReplayGuard:
    def __init__(self):
        self._lock = threading.Lock()
        self._seen: dict[tuple[str, str], int] = {}

    def reserve(self, identity: str, nonce: str, now: int) -> bool:
        with self._lock:
            self._seen = {k: v for k, v in self._seen.items() if v >= now - MAX_SKEW_SECONDS}
            key = (identity, nonce)
            if key in self._seen:
                return False
            self._seen[key] = now
            return True

def canonical_body(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True, allow_nan=False).encode("utf-8")

def sign_request(key: bytes, identity: str, timestamp: int, nonce: str, payload: dict[str, Any]) -> str:
    signing = canonical_body({"identity": identity, "timestamp": timestamp, "nonce": nonce, "payload": payload})
    return hmac.new(key, signing, hashlib.sha256).hexdigest()

def process_authenticated(envelope: dict[str, Any], *, keys: dict[str, bytes],
                          allowed_root: str, guard: Any,
                          clock: Callable[[], int] = lambda: int(time.time())) -> dict[str, Any]:
    denied = {"status":"NOT_VERIFIED","reason":"AUTHORIZATION_FAILED","execution_authorized":False,
              "gxp_compliance":"NOT_VERIFIED","gxp_approval":"NOT_GRANTED","gxp_release":"NOT_GRANTED"}
    if not isinstance(envelope, dict) or set(envelope) != {"identity", "timestamp", "nonce", "payload", "signature"}:
        return denied
    identity, ts, nonce, payload, signature = (envelope[k] for k in ("identity","timestamp","nonce","payload","signature"))
    if not isinstance(identity,str) or not identity or not isinstance(ts,int) or isinstance(ts,bool):
        return denied
    if not isinstance(nonce,str) or len(nonce) < 16 or len(nonce)>128 or not isinstance(signature,str) or len(signature)!=64:
        return denied
    if not isinstance(payload,dict) or identity not in keys or abs(clock()-ts)>MAX_SKEW_SECONDS:
        return denied
    try:
        expected=sign_request(keys[identity],identity,ts,nonce,payload)
    except (TypeError,ValueError):
        return denied
    if not hmac.compare_digest(expected,signature):
        return denied
    try:
        reserved = guard.reserve(identity, nonce, clock())
    except Exception:
        return {**denied, "reason":"REPLAY_STORE_UNAVAILABLE"}
    if not reserved:
        return {**denied,"reason":"REPLAY_REJECTED"}
    return handle_jarvis_request(payload,allowed_root=allowed_root)
