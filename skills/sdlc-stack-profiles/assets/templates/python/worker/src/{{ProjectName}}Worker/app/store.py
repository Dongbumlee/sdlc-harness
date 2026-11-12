"""The job store: one SQLite database holding jobs, effects, and the outbox.

SQLite is the pinned store for the template because it makes the
whole correctness story testable with no external services — the
transactions the guarantees rest on are real here. In production the
same schema and claim protocol map onto any transactional store;
the guarantees live in the protocol, not in SQLite.
"""

from __future__ import annotations

import json
import sqlite3
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL,
    payload TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    next_attempt_at REAL NOT NULL DEFAULT 0,
    claimed_by TEXT,
    claim_expires_at REAL,
    last_error TEXT,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS effects (
    idempotency_key TEXT PRIMARY KEY,
    job_id INTEGER NOT NULL,
    result TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS outbox (
    id INTEGER PRIMARY KEY,
    idempotency_key TEXT NOT NULL,
    event TEXT NOT NULL,
    payload TEXT NOT NULL,
    published_at REAL
);
"""


@dataclass(frozen=True)
class Job:
    id: int
    idempotency_key: str
    type: str
    payload: dict
    attempts: int


class JobStore:
    """All state transitions happen here, each in its own transaction."""

    def __init__(
        self, path: Path | str, clock: Callable[[], float] = time.time
    ) -> None:
        self._clock = clock
        self._conn = sqlite3.connect(path, isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(SCHEMA)

    def enqueue(self, type: str, payload: dict, idempotency_key: str) -> int:
        """Add a job, deduplicated by idempotency key.

        A producer retrying its own send gets the original job's id
        back; the key's UNIQUE constraint is what makes that safe.
        """
        cur = self._conn.execute(
            "INSERT OR IGNORE INTO jobs (idempotency_key, type, payload, created_at)"
            " VALUES (?, ?, ?, ?)",
            (idempotency_key, type, json.dumps(payload), self._clock()),
        )
        if cur.rowcount:
            return cur.lastrowid
        row = self._conn.execute(
            "SELECT id FROM jobs WHERE idempotency_key = ?", (idempotency_key,)
        ).fetchone()
        return row[0]

    def claim(self, worker_id: str, lease_seconds: float) -> Job | None:
        """Atomically claim the next due job under a lease.

        A job is due when it is pending and its scheduled time has
        come, or when it is claimed and its lease has expired — the
        second case is how a job whose worker crashed mid-flight
        returns to work.
        """
        now = self._clock()
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            row = self._conn.execute(
                "SELECT id, idempotency_key, type, payload, attempts FROM jobs"
                " WHERE (status = 'pending' AND next_attempt_at <= ?)"
                "    OR (status = 'claimed' AND claim_expires_at <= ?)"
                " ORDER BY id LIMIT 1",
                (now, now),
            ).fetchone()
            if row is None:
                self._conn.execute("COMMIT")
                return None
            self._conn.execute(
                "UPDATE jobs SET status = 'claimed', claimed_by = ?,"
                " claim_expires_at = ? WHERE id = ?",
                (worker_id, now + lease_seconds, row[0]),
            )
            self._conn.execute("COMMIT")
        except BaseException:
            self._conn.execute("ROLLBACK")
            raise
        return Job(
            id=row[0],
            idempotency_key=row[1],
            type=row[2],
            payload=json.loads(row[3]),
            attempts=row[4],
        )

    def complete(self, job: Job, result: str) -> bool:
        """Apply the effect and mark the job done, in one transaction.

        Returns True when the effect was applied. When the
        idempotency key already has an effect row, this delivery is
        a duplicate: the job is still marked done (acked), but the
        effect is NOT applied again and no second outbox event is
        written — that pair is the whole duplicate-delivery answer.
        """
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            cur = self._conn.execute(
                "INSERT OR IGNORE INTO effects"
                " (idempotency_key, job_id, result, created_at)"
                " VALUES (?, ?, ?, ?)",
                (job.idempotency_key, job.id, result, self._clock()),
            )
            applied = cur.rowcount == 1
            if applied:
                self._conn.execute(
                    "INSERT INTO outbox (idempotency_key, event, payload)"
                    " VALUES (?, 'job.completed', ?)",
                    (
                        job.idempotency_key,
                        json.dumps({"job_id": job.id, "result": result}),
                    ),
                )
            self._conn.execute(
                "UPDATE jobs SET status = 'done', claimed_by = NULL,"
                " claim_expires_at = NULL WHERE id = ?",
                (job.id,),
            )
            self._conn.execute("COMMIT")
        except BaseException:
            self._conn.execute("ROLLBACK")
            raise
        return applied

    def fail(
        self, job: Job, error: str, *, retryable: bool, next_attempt_at: float | None
    ) -> None:
        """Record a failure: schedule the retry, or dead-letter the job."""
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            if retryable and next_attempt_at is not None:
                self._conn.execute(
                    "UPDATE jobs SET status = 'pending', attempts = attempts + 1,"
                    " next_attempt_at = ?, last_error = ?, claimed_by = NULL,"
                    " claim_expires_at = NULL WHERE id = ?",
                    (next_attempt_at, error, job.id),
                )
            else:
                self._conn.execute(
                    "UPDATE jobs SET status = 'dead', attempts = attempts + 1,"
                    " last_error = ?, claimed_by = NULL, claim_expires_at = NULL"
                    " WHERE id = ?",
                    (error, job.id),
                )
            self._conn.execute("COMMIT")
        except BaseException:
            self._conn.execute("ROLLBACK")
            raise

    def dead_jobs(self) -> list[Job]:
        rows = self._conn.execute(
            "SELECT id, idempotency_key, type, payload, attempts FROM jobs"
            " WHERE status = 'dead' ORDER BY id"
        ).fetchall()
        return [
            Job(
                id=r[0],
                idempotency_key=r[1],
                type=r[2],
                payload=json.loads(r[3]),
                attempts=r[4],
            )
            for r in rows
        ]

    def replay(self, job_id: int) -> bool:
        """Return a dead job to pending with its attempt budget restored.

        The replay tool exists from day one — a dead-letter queue
        without one is a write-only graveyard.
        """
        cur = self._conn.execute(
            "UPDATE jobs SET status = 'pending', attempts = 0, next_attempt_at = 0,"
            " last_error = NULL WHERE id = ? AND status = 'dead'",
            (job_id,),
        )
        return cur.rowcount == 1

    def stats(self) -> dict[str, int]:
        """Queue depths per status. A dead depth above zero is the alarm.

        Wire the runner's check (or your scheduler's) to page on
        ``dead > 0`` — silently accumulating dead jobs is the failure
        mode this type exists to prevent.
        """
        counts = {"pending": 0, "claimed": 0, "done": 0, "dead": 0}
        for status, n in self._conn.execute(
            "SELECT status, COUNT(*) FROM jobs GROUP BY status"
        ):
            counts[status] = n
        counts["outbox_unpublished"] = self._conn.execute(
            "SELECT COUNT(*) FROM outbox WHERE published_at IS NULL"
        ).fetchone()[0]
        return counts

    def drain_outbox(self, publish: Callable[[str, dict], None]) -> int:
        """Publish unpublished outbox rows, marking each after it is accepted.

        Marking after acceptance keeps publishing at-least-once: a
        crash between publish and mark republishes, so consumers of
        the outbox must dedupe on the idempotency key like everyone
        else in this design.
        """
        rows = self._conn.execute(
            "SELECT id, idempotency_key, event, payload FROM outbox"
            " WHERE published_at IS NULL ORDER BY id"
        ).fetchall()
        published = 0
        for row_id, key, event, payload in rows:
            publish(event, {"idempotency_key": key, **json.loads(payload)})
            self._conn.execute(
                "UPDATE outbox SET published_at = ? WHERE id = ?",
                (self._clock(), row_id),
            )
            published += 1
        return published
