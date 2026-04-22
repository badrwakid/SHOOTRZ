from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional


class DurableJobStore:
    """SQLite-backed durable store for MVP analysis jobs."""

    def __init__(self, db_path: Path, retention_hours: int = 72):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.retention_seconds = retention_hours * 3600
        self._lock = Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS mvp_jobs (
                    job_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    updated_at REAL NOT NULL,
                    expires_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_mvp_jobs_expires_at ON mvp_jobs(expires_at)"
            )
            conn.commit()

    def upsert(self, job_id: str, payload: Dict[str, Any]) -> None:
        now = time.time()
        expires_at = now + self.retention_seconds
        status = str(payload.get("status", "unknown"))
        payload_json = json.dumps(payload, default=str)

        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO mvp_jobs(job_id, status, payload_json, updated_at, expires_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(job_id) DO UPDATE SET
                        status = excluded.status,
                        payload_json = excluded.payload_json,
                        updated_at = excluded.updated_at,
                        expires_at = excluded.expires_at
                    """,
                    (job_id, status, payload_json, now, expires_at),
                )
                conn.commit()

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload_json FROM mvp_jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
            if row is None:
                return None
            return json.loads(row["payload_json"])

    def cleanup_expired(self) -> int:
        now = time.time()
        with self._lock:
            with self._connect() as conn:
                cur = conn.execute(
                    "DELETE FROM mvp_jobs WHERE expires_at < ?",
                    (now,),
                )
                conn.commit()
                return int(cur.rowcount or 0)
