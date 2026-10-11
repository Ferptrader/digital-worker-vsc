"""SQLite-backed replay reservation candidate for single-host testing only.

Provides atomic duplicate rejection across processes sharing ONE SQLite file.
Not a remote trust anchor, not a multi-host idempotency guarantee, and not
proof of exactly-once side effects or GxP qualification.
"""
from __future__ import annotations
import sqlite3
from pathlib import Path

class SQLiteReplayGuard:
    def __init__(self, database_path: str):
        self.database_path = str(Path(database_path))
        if self.database_path == ":memory:":
            raise ValueError("PERSISTENT_DATABASE_REQUIRED")
        self._initialize()

    def _connect(self):
        db=sqlite3.connect(self.database_path, timeout=10, isolation_level=None)
        db.execute("PRAGMA busy_timeout=10000")
        db.execute("PRAGMA synchronous=FULL")
        return db

    def _initialize(self):
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS replay_reservations (identity TEXT NOT NULL, nonce TEXT NOT NULL, reserved_at INTEGER NOT NULL, PRIMARY KEY(identity,nonce))")

    def reserve(self, identity: str, nonce: str, now: int) -> bool:
        if not isinstance(identity,str) or not identity or not isinstance(nonce,str) or not nonce:
            return False
        # Do not purge by clock: retaining reservations denies reuse even after
        # restart. Rotation and retention must be governed externally.
        with self._connect() as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                db.execute("INSERT INTO replay_reservations(identity,nonce,reserved_at) VALUES(?,?,?)",(identity,nonce,now))
                db.execute("COMMIT")
                return True
            except sqlite3.IntegrityError:
                db.execute("ROLLBACK")
                return False
            except Exception:
                if db.in_transaction:
                    db.execute("ROLLBACK")
                raise
