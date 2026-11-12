//! The job store: one SQLite database holding jobs, effects, and
//! the outbox, through rusqlite's bundled engine — the shipped
//! binary is exactly the tested binary.
//!
//! SQLite is the pinned store for the template because it makes
//! the whole correctness story testable with no external services
//! — the transactions the guarantees rest on are real here. In
//! production the same schema and claim protocol map onto any
//! transactional store; the guarantees live in the protocol, not
//! in SQLite. All state transitions happen here, each in its own
//! transaction, mirroring the other stacks' worker stores
//! statement for statement. The connection sits behind a mutex so
//! the raw BEGIN IMMEDIATE / COMMIT / ROLLBACK statements are
//! serialized the way the protocol assumes.

use std::collections::BTreeMap;
use std::sync::Mutex;

use rusqlite::{Connection, params};
use serde_json::{Value, json};

const SCHEMA: &str = "
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
);";

/// A claimed or dead job as the worker loop sees it.
#[derive(Debug, Clone)]
pub struct Job {
    pub id: i64,
    pub idempotency_key: String,
    pub job_type: String,
    pub payload: Value,
    pub attempts: i64,
}

/// The job store.
pub struct JobStore {
    conn: Mutex<Connection>,
    clock: Box<dyn Fn() -> f64 + Send>,
}

impl JobStore {
    /// Open (or create) the store at `path`, stamping times from
    /// the real clock.
    pub fn open(path: &str) -> rusqlite::Result<Self> {
        Self::with_clock(path, Box::new(crate::now_seconds))
    }

    /// Open the store with an injected clock (tests pass a fake).
    pub fn with_clock(path: &str, clock: Box<dyn Fn() -> f64 + Send>) -> rusqlite::Result<Self> {
        let conn = Connection::open(path)?;
        conn.execute_batch("PRAGMA journal_mode=WAL")?;
        conn.execute_batch(SCHEMA)?;
        Ok(Self {
            conn: Mutex::new(conn),
            clock,
        })
    }

    fn now(&self) -> f64 {
        (self.clock)()
    }

    /// Run `f` inside one BEGIN IMMEDIATE transaction, committing
    /// on success and rolling back on error.
    fn tx<T>(&self, f: impl FnOnce(&Connection) -> rusqlite::Result<T>) -> rusqlite::Result<T> {
        let conn = self.conn.lock().expect("store mutex poisoned");
        conn.execute_batch("BEGIN IMMEDIATE")?;
        match f(&conn) {
            Ok(value) => {
                conn.execute_batch("COMMIT")?;
                Ok(value)
            }
            Err(error) => {
                let _ = conn.execute_batch("ROLLBACK");
                Err(error)
            }
        }
    }

    /// Add a job, deduplicated by idempotency key. A producer
    /// retrying its own send gets the original job's id back; the
    /// key's UNIQUE constraint is what makes that safe.
    pub fn enqueue(
        &self,
        job_type: &str,
        payload: &Value,
        idempotency_key: &str,
    ) -> rusqlite::Result<i64> {
        let conn = self.conn.lock().expect("store mutex poisoned");
        let changed = conn.execute(
            "INSERT OR IGNORE INTO jobs (idempotency_key, type, payload, created_at) VALUES (?1, ?2, ?3, ?4)",
            params![idempotency_key, job_type, payload.to_string(), self.now()],
        )?;
        if changed == 1 {
            return Ok(conn.last_insert_rowid());
        }
        conn.query_row(
            "SELECT id FROM jobs WHERE idempotency_key = ?1",
            params![idempotency_key],
            |row| row.get(0),
        )
    }

    /// Atomically claim the next due job under a lease. A job is
    /// due when it is pending and its scheduled time has come, or
    /// when it is claimed and its lease has expired — the second
    /// case is how a job whose worker crashed mid-flight returns
    /// to work.
    pub fn claim(&self, worker_id: &str, lease_seconds: f64) -> rusqlite::Result<Option<Job>> {
        let now = self.now();
        self.tx(|conn| {
            let mut stmt = conn.prepare(
                "SELECT id, idempotency_key, type, payload, attempts FROM jobs \
                 WHERE (status = 'pending' AND next_attempt_at <= ?1) \
                    OR (status = 'claimed' AND claim_expires_at <= ?1) \
                 ORDER BY id LIMIT 1",
            )?;
            let job = stmt
                .query_row(params![now], |row| {
                    let raw: String = row.get(3)?;
                    Ok(Job {
                        id: row.get(0)?,
                        idempotency_key: row.get(1)?,
                        job_type: row.get(2)?,
                        payload: serde_json::from_str(&raw)
                            .map_err(|_| rusqlite::Error::InvalidQuery)?,
                        attempts: row.get(4)?,
                    })
                })
                .ok();
            drop(stmt);
            match job {
                None => Ok(None),
                Some(job) => {
                    conn.execute(
                        "UPDATE jobs SET status = 'claimed', claimed_by = ?1, claim_expires_at = ?2 WHERE id = ?3",
                        params![worker_id, now + lease_seconds, job.id],
                    )?;
                    Ok(Some(job))
                }
            }
        })
    }

    /// Apply the effect and mark the job done, in one transaction.
    /// Reports whether the effect was applied. When the
    /// idempotency key already has an effect row, this delivery is
    /// a duplicate: the job is still marked done (acked), but the
    /// effect is NOT applied again and no second outbox event is
    /// written — that pair is the whole duplicate-delivery answer.
    pub fn complete(&self, job: &Job, result: &str) -> rusqlite::Result<bool> {
        let result = result.to_string();
        let now = self.now();
        self.tx(|conn| {
            let changed = conn.execute(
                "INSERT OR IGNORE INTO effects (idempotency_key, job_id, result, created_at) VALUES (?1, ?2, ?3, ?4)",
                params![job.idempotency_key, job.id, result, now],
            )?;
            let applied = changed == 1;
            if applied {
                let payload = json!({"job_id": job.id, "result": result});
                conn.execute(
                    "INSERT INTO outbox (idempotency_key, event, payload) VALUES (?1, 'job.completed', ?2)",
                    params![job.idempotency_key, payload.to_string()],
                )?;
            }
            conn.execute(
                "UPDATE jobs SET status = 'done', claimed_by = NULL, claim_expires_at = NULL WHERE id = ?1",
                params![job.id],
            )?;
            Ok(applied)
        })
    }

    /// Record a failure: schedule the retry, or dead-letter the job.
    pub fn fail(
        &self,
        job: &Job,
        error: &str,
        retryable: bool,
        next_attempt_at: f64,
    ) -> rusqlite::Result<()> {
        let error = error.to_string();
        self.tx(|conn| {
            if retryable {
                conn.execute(
                    "UPDATE jobs SET status = 'pending', attempts = attempts + 1, next_attempt_at = ?1, last_error = ?2, claimed_by = NULL, claim_expires_at = NULL WHERE id = ?3",
                    params![next_attempt_at, error, job.id],
                )?;
            } else {
                conn.execute(
                    "UPDATE jobs SET status = 'dead', attempts = attempts + 1, last_error = ?1, claimed_by = NULL, claim_expires_at = NULL WHERE id = ?2",
                    params![error, job.id],
                )?;
            }
            Ok(())
        })
    }

    pub fn dead_jobs(&self) -> rusqlite::Result<Vec<Job>> {
        let conn = self.conn.lock().expect("store mutex poisoned");
        let mut stmt = conn.prepare(
            "SELECT id, idempotency_key, type, payload, attempts FROM jobs WHERE status = 'dead' ORDER BY id",
        )?;
        let rows = stmt.query_map([], |row| {
            let raw: String = row.get(3)?;
            Ok(Job {
                id: row.get(0)?,
                idempotency_key: row.get(1)?,
                job_type: row.get(2)?,
                payload: serde_json::from_str(&raw).map_err(|_| rusqlite::Error::InvalidQuery)?,
                attempts: row.get(4)?,
            })
        })?;
        let mut jobs = Vec::new();
        for job in rows {
            jobs.push(job?);
        }
        Ok(jobs)
    }

    /// Return a dead job to pending with its attempt budget
    /// restored. The replay tool exists from day one — a
    /// dead-letter queue without one is a write-only graveyard.
    pub fn replay(&self, job_id: i64) -> rusqlite::Result<bool> {
        let conn = self.conn.lock().expect("store mutex poisoned");
        let changed = conn.execute(
            "UPDATE jobs SET status = 'pending', attempts = 0, next_attempt_at = 0, last_error = NULL WHERE id = ?1 AND status = 'dead'",
            params![job_id],
        )?;
        Ok(changed == 1)
    }

    /// Queue depths per status. A dead depth above zero is the
    /// alarm: wire the runner's check (or your scheduler's) to
    /// page on it — silently accumulating dead jobs is the failure
    /// mode this type exists to prevent.
    pub fn stats(&self) -> rusqlite::Result<BTreeMap<String, i64>> {
        let conn = self.conn.lock().expect("store mutex poisoned");
        let mut counts: BTreeMap<String, i64> = ["pending", "claimed", "done", "dead"]
            .iter()
            .map(|status| (status.to_string(), 0))
            .collect();
        {
            let mut stmt = conn.prepare("SELECT status, COUNT(*) FROM jobs GROUP BY status")?;
            let rows = stmt.query_map([], |row| {
                Ok((row.get::<_, String>(0)?, row.get::<_, i64>(1)?))
            })?;
            for row in rows {
                let (status, n) = row?;
                counts.insert(status, n);
            }
        }
        let unpublished: i64 = conn.query_row(
            "SELECT COUNT(*) FROM outbox WHERE published_at IS NULL",
            [],
            |row| row.get(0),
        )?;
        counts.insert("outbox_unpublished".to_string(), unpublished);
        Ok(counts)
    }

    /// Publish unpublished outbox rows, marking each after it is
    /// accepted. Marking after acceptance keeps publishing
    /// at-least-once: a crash between publish and mark republishes,
    /// so consumers of the outbox must dedupe on the idempotency
    /// key like everyone else in this design.
    pub fn drain_outbox(&self, publish: &mut dyn FnMut(&str, &Value)) -> rusqlite::Result<usize> {
        let rows: Vec<(i64, String, String, String)> = {
            let conn = self.conn.lock().expect("store mutex poisoned");
            let mut stmt = conn.prepare(
                "SELECT id, idempotency_key, event, payload FROM outbox WHERE published_at IS NULL ORDER BY id",
            )?;
            let mapped = stmt.query_map([], |row| {
                Ok((
                    row.get::<_, i64>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, String>(2)?,
                    row.get::<_, String>(3)?,
                ))
            })?;
            let mut rows = Vec::new();
            for row in mapped {
                rows.push(row?);
            }
            rows
        };
        let mut published = 0;
        for (id, key, event, raw) in rows {
            let mut payload: Value =
                serde_json::from_str(&raw).map_err(|_| rusqlite::Error::InvalidQuery)?;
            payload["idempotency_key"] = Value::String(key);
            publish(&event, &payload);
            let conn = self.conn.lock().expect("store mutex poisoned");
            conn.execute(
                "UPDATE outbox SET published_at = ?1 WHERE id = ?2",
                params![self.now(), id],
            )?;
            published += 1;
        }
        Ok(published)
    }

    /// Raw row count for tests and diagnostics.
    pub fn count_rows(&self, table: &str) -> rusqlite::Result<i64> {
        if table != "effects" && table != "outbox" {
            return Err(rusqlite::Error::InvalidQuery);
        }
        let conn = self.conn.lock().expect("store mutex poisoned");
        conn.query_row(&format!("SELECT COUNT(*) FROM {table}"), [], |row| {
            row.get(0)
        })
    }
}
