"""JARVIS C002: fail-closed LAB-ONLY authentication and durable anchor.

This is a custom test protocol, NOT MCP/A2A, nor an independently governed
cloud trust service. Does not execute tools or grant GxP authorization.
"""
from __future__ import annotations
import base64
import hashlib
import json
import os
from pathlib import Path
from contextlib import closing
import sqlite3
import time
from typing import Any
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

MAX_CLOCK_SKEW = 120
GENESIS = "0" * 64
ALLOWED_ACTIONS = frozenset({"reserve", "status"})
ALLOWED_OPERATIONS = frozenset({"extract_document"})  # zero production side effects


def canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def encoded(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def decoded(data: str) -> bytes:
    return base64.b64decode(data, validate=True)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def request_envelope(identity: str, key: Ed25519PrivateKey, payload: dict, now: int | None = None) -> dict:
    """Caller-provided identity is non-authoritative until signature validates."""
    from secrets import token_hex
    body = {"protocol": "JASAP-ANCHOR-C002-LAB", "identity": identity,
            "timestamp": int(time.time()) if now is None else now,
            "nonce": token_hex(20), "payload": payload}
    return {**body, "signature": encoded(key.sign(canonical(body)))}


def verify_response(response: dict, anchor_public_key: Ed25519PublicKey) -> dict:
    body = response["body"]
    anchor_public_key.verify(decoded(response["signature"]), canonical(body))
    return body


class Denied(Exception):
    pass


class Ledger:
    """Single-node durable database, NOT immutable or admin-independent.

    Database is NEVER created implicitly during request processing. A deleted
    DB fails closed rather than recreating the nonce memory. Only provision()
    creates the DB; an operator restoring it must reconcile witnesses first.
    """
    def __init__(self, db_path: str, signing_key: Ed25519PrivateKey, seal_path: str | None = None):
        self.db_path = Path(db_path)
        self.seal_path = Path(seal_path) if seal_path is not None else Path(db_path + ".witness")
        self.key = signing_key
        self.public = signing_key.public_key()
        if not self.db_path.is_file() or not self.seal_path.is_file():
            raise Denied("ANCHOR_STORAGE_UNAVAILABLE")

    @classmethod
    def provision(cls, db_path: str, signing_key: Ed25519PrivateKey, seal_path: str | None = None) -> "Ledger":
        path = Path(db_path)
        seal = Path(seal_path) if seal_path else Path(db_path + ".witness")
        seal.parent.mkdir(parents=True, exist_ok=True)
        if seal.exists():
            raise Denied("REFUSE_REPROVISION_EXISTING_WITNESS")
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise Denied("REFUSE_REPROVISION_EXISTING_DATABASE")
        with closing(sqlite3.connect(str(path))) as db:
            db.execute("PRAGMA journal_mode=DELETE")
            db.execute("PRAGMA synchronous=FULL")
            db.execute("CREATE TABLE witness (seq INTEGER PRIMARY KEY, tenant TEXT NOT NULL, operation TEXT NOT NULL, request_id TEXT NOT NULL, digest TEXT NOT NULL, identity TEXT NOT NULL, previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL, signature TEXT NOT NULL, created_at INTEGER NOT NULL, UNIQUE(tenant,operation,request_id))")
            db.commit()
        obj = cls.__new__(cls)
        obj.db_path=path
        obj.seal_path=seal
        obj.key=signing_key
        obj.public=signing_key.public_key()
        obj._write_seal(0, GENESIS)
        return cls(str(path), signing_key, str(seal))

    def _connect(self):
        if not self.db_path.is_file() or not self.seal_path.is_file():
            raise Denied("ANCHOR_STORAGE_UNAVAILABLE")
        # URI mode=rw means a missing DB cannot silently regenerate reservations.
        db = sqlite3.connect(self.db_path.resolve().as_uri() + "?mode=rw", uri=True, timeout=5, isolation_level=None)
        db.execute("PRAGMA busy_timeout=5000")
        db.execute("PRAGMA synchronous=FULL")
        return db

    def _write_seal(self, seq: int, last_hash: str) -> None:
        """Independently located seal, not WORM nor independently administered.

        If DB commit succeeds but seal update fails, later operations HOLD until
        authorized recovery reconciles state. Do not use in production.
        """
        payload={"seq":seq,"last_hash":last_hash,"version":"C002"}
        seal={"payload":payload,"signature":encoded(self.key.sign(canonical(payload)))}
        temporary=self.seal_path.with_name(self.seal_path.name + ".new")
        with open(temporary,"xb") as handle:
            os.chmod(temporary,0o600)
            handle.write(canonical(seal))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary,self.seal_path)
        fd=os.open(self.seal_path.parent,os.O_RDONLY)
        try:os.fsync(fd)
        finally:os.close(fd)

    def _check_seal(self, seq: int, last_hash: str) -> None:
        try:
            seal=json.loads(self.seal_path.read_text())
            payload=seal["payload"]
            self.public.verify(decoded(seal["signature"]),canonical(payload))
            if payload != {"seq":seq,"last_hash":last_hash,"version":"C002"}:
                raise Denied("INDEPENDENT_SEAL_MISMATCH")
        except (ValueError,KeyError,TypeError,InvalidSignature,UnicodeError,OSError) as exc:
            raise Denied("INDEPENDENT_SEAL_INVALID") from exc

    def _validate(self, db: sqlite3.Connection) -> tuple[int, str]:
        try:
            if db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise Denied("STORAGE_CORRUPT")
            rows = db.execute("SELECT seq,tenant,operation,request_id,digest,identity,previous_hash,event_hash,signature,created_at FROM witness ORDER BY seq").fetchall()
        except sqlite3.DatabaseError as error:
            raise Denied("STORAGE_CORRUPT") from error
        previous = GENESIS
        for expected_seq, row in enumerate(rows, start=1):
            seq,tenant,operation,request_id,digest,identity,prior,event_hash,signature,created_at = row
            event = {"seq": seq, "tenant": tenant, "operation": operation,
                     "request_id": request_id, "digest": digest, "identity": identity,
                     "previous_hash": prior, "created_at": created_at}
            if seq != expected_seq or prior != previous or sha(canonical(event)) != event_hash:
                raise Denied("WITNESS_TAMPER_DETECTED")
            try:
                self.public.verify(decoded(signature), canonical({**event, "event_hash": event_hash}))
            except (ValueError, InvalidSignature):
                raise Denied("WITNESS_SIGNATURE_INVALID") from None
            previous = event_hash
        self._check_seal(len(rows),previous)
        return len(rows), previous

    def reserve(self, identity: str, tenant: str, operation: str, request_id: str, digest: str, now: int) -> dict:
        try:
            with closing(self._connect()) as db:
                db.execute("BEGIN IMMEDIATE")
                seq, previous = self._validate(db)
                existing = db.execute("SELECT seq,digest,event_hash FROM witness WHERE tenant=? AND operation=? AND request_id=?",(tenant,operation,request_id)).fetchone()
                if existing:
                    verdict = "DUPLICATE" if existing[1] == digest else "CONFLICT"
                    db.execute("ROLLBACK")
                    return {"decision": verdict, "sequence": existing[0], "witness_hash": existing[2]}
                event = {"seq": seq+1, "tenant": tenant, "operation": operation,
                         "request_id": request_id, "digest": digest, "identity": identity,
                         "previous_hash": previous, "created_at": now}
                event_hash = sha(canonical(event))
                signature = encoded(self.key.sign(canonical({**event, "event_hash": event_hash})))
                db.execute("INSERT INTO witness VALUES(?,?,?,?,?,?,?,?,?,?)",(seq+1,tenant,operation,request_id,digest,identity,previous,event_hash,signature,now))
                self._write_seal(seq+1,event_hash)
                db.execute("COMMIT")
                return {"decision":"RESERVED", "sequence":seq+1, "witness_hash":event_hash}
        except Denied:
            raise
        except (sqlite3.Error, OSError) as error:
            raise Denied("ANCHOR_STORAGE_UNAVAILABLE") from error

    def status(self, tenant: str, operation: str, request_id: str) -> dict:
        try:
            with closing(self._connect()) as db:
                self._validate(db)
                row=db.execute("SELECT seq,digest,event_hash FROM witness WHERE tenant=? AND operation=? AND request_id=?",(tenant,operation,request_id)).fetchone()
                return {"decision":"FOUND" if row else "NOT_FOUND", "sequence":row[0] if row else None,
                        "digest":row[1] if row else None,"witness_hash":row[2] if row else None}
        except Denied:
            raise
        except (sqlite3.Error,OSError) as error:
            raise Denied("ANCHOR_STORAGE_UNAVAILABLE") from error


class Anchor:
    def __init__(self, ledger: Ledger, principals: dict[str, dict], signing_key: Ed25519PrivateKey, clock=time.time):
        self.ledger = ledger
        self.principals = principals
        self.key = signing_key
        self.clock = clock

    def _check(self, request: Any) -> tuple[str,dict,dict]:
        if not isinstance(request,dict) or set(request) != {"protocol","identity","timestamp","nonce","payload","signature"}:
            raise Denied("INVALID_ENVELOPE")
        protocol,identity,timestamp,nonce,payload,signature=(request[k] for k in ("protocol","identity","timestamp","nonce","payload","signature"))
        if protocol != "JASAP-ANCHOR-C002-LAB" or not isinstance(identity,str) or identity not in self.principals:
            raise Denied("AUTHENTICATION_FAILED")
        if type(timestamp) is not int or abs(int(self.clock())-timestamp) > MAX_CLOCK_SKEW:
            raise Denied("TIMESTAMP_INVALID")
        if not isinstance(nonce,str) or len(nonce) < 32 or len(nonce)>128 or not isinstance(payload,dict):
            raise Denied("INVALID_ENVELOPE")
        try:
            public = Ed25519PublicKey.from_public_bytes(decoded(self.principals[identity]["public_key"]))
            body = {k:request[k] for k in ("protocol","identity","timestamp","nonce","payload")}
            public.verify(decoded(signature), canonical(body))
        except (ValueError,InvalidSignature,TypeError,KeyError):
            raise Denied("AUTHENTICATION_FAILED") from None
        return identity,self.principals[identity],payload

    def respond(self, request: Any) -> dict:
        identity="NOT_AUTHENTICATED"
        result={"decision":"DENIED", "reason":"INVALID_REQUEST"}
        try:
            identity,principal,payload=self._check(request)
            if set(payload) != {"action","tenant","operation","request_id","digest"}:
                raise Denied("INVALID_PAYLOAD")
            action,tenant,operation,request_id,digest=(payload[k] for k in ("action","tenant","operation","request_id","digest"))
            if action not in ALLOWED_ACTIONS or operation not in ALLOWED_OPERATIONS:
                raise Denied("OPERATION_NOT_ALLOWED")
            if not all(isinstance(v,str) for v in (tenant,operation,request_id,digest)):
                raise Denied("INVALID_PAYLOAD")
            if tenant != principal["tenant"] or action not in principal["actions"] or operation not in principal["operations"]:
                raise Denied("AUTHORIZATION_FAILED")
            if len(request_id)<16 or len(request_id)>128 or len(digest)!=64 or any(c not in "0123456789abcdef" for c in digest):
                raise Denied("INVALID_PAYLOAD")
            if action == "reserve":
                result=self.ledger.reserve(identity,tenant,operation,request_id,digest,int(self.clock()))
            else:
                try:
                    result=self.ledger.status(tenant,operation,request_id,identity=identity)
                except TypeError:
                    # C002 local legacy ledger does not accept identity; deploy only cloud implementation.
                    result={"decision":"DENIED","reason":"LEDGER_IDENTITY_BINDING_REQUIRED"}
        except Denied as error:
            result={"decision":"DENIED", "reason":str(error)}
        except Exception:
            # Never return stack traces or private keys to untrusted clients.
            result={"decision":"DENIED", "reason":"INTERNAL_FAILURE"}
        body={"protocol":"JASAP-ANCHOR-C002-LAB", "identity":identity,
              **result, "execution_authorized":False,
              "gxp_approval":"NOT_GRANTED", "gxp_release":"NOT_GRANTED",
              "gxp_compliance":"NOT_VERIFIED"}
        return {"body":body,"signature":encoded(self.key.sign(canonical(body)))}
