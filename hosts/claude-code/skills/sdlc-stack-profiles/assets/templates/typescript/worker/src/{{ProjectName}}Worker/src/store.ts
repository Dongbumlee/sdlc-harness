/**
 * The job store: one SQLite database holding jobs, effects, and the
 * outbox, through Node's built-in `node:sqlite` — no third-party
 * driver, so the shipped artefact is exactly the tested artefact.
 *
 * SQLite is the pinned store for the template because it makes the
 * whole correctness story testable with no external services — the
 * transactions the guarantees rest on are real here. In production
 * the same schema and claim protocol map onto any transactional
 * store; the guarantees live in the protocol, not in SQLite.
 */

import { DatabaseSync } from "node:sqlite";

const SCHEMA = `
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
);`;

export interface Job {
  id: number;
  idempotencyKey: string;
  type: string;
  payload: Record<string, unknown>;
  attempts: number;
}

export type Stats = Record<string, number>;

interface JobRow {
  id: number;
  idempotency_key: string;
  type: string;
  payload: string;
  attempts: number;
}

export class JobStore {
  readonly #db: DatabaseSync;
  readonly #clock: () => number;

  constructor(path: string, clock: () => number = () => Date.now() / 1000) {
    this.#clock = clock;
    this.#db = new DatabaseSync(path);
    this.#db.exec("PRAGMA journal_mode=WAL");
    this.#db.exec(SCHEMA);
  }

  /**
   * Add a job, deduplicated by idempotency key. A producer retrying
   * its own send gets the original job's id back; the key's UNIQUE
   * constraint is what makes that safe.
   */
  enqueue(
    type: string,
    payload: Record<string, unknown>,
    idempotencyKey: string,
  ): number {
    const info = this.#db
      .prepare(
        "INSERT OR IGNORE INTO jobs (idempotency_key, type, payload, created_at) VALUES (?, ?, ?, ?)",
      )
      .run(idempotencyKey, type, JSON.stringify(payload), this.#clock());
    if (info.changes === 1) {
      return Number(info.lastInsertRowid);
    }
    const row = this.#db
      .prepare("SELECT id FROM jobs WHERE idempotency_key = ?")
      .get(idempotencyKey) as { id: number };
    return row.id;
  }

  /**
   * Atomically claim the next due job under a lease. A job is due
   * when it is pending and its scheduled time has come, or when it
   * is claimed and its lease has expired — the second case is how a
   * job whose worker crashed mid-flight returns to work.
   */
  claim(workerId: string, leaseSeconds: number): Job | undefined {
    const now = this.#clock();
    this.#db.exec("BEGIN IMMEDIATE");
    try {
      const row = this.#db
        .prepare(
          `SELECT id, idempotency_key, type, payload, attempts FROM jobs
           WHERE (status = 'pending' AND next_attempt_at <= ?)
              OR (status = 'claimed' AND claim_expires_at <= ?)
           ORDER BY id LIMIT 1`,
        )
        .get(now, now) as JobRow | undefined;
      if (!row) {
        this.#db.exec("COMMIT");
        return undefined;
      }
      this.#db
        .prepare(
          "UPDATE jobs SET status = 'claimed', claimed_by = ?, claim_expires_at = ? WHERE id = ?",
        )
        .run(workerId, now + leaseSeconds, row.id);
      this.#db.exec("COMMIT");
      return {
        id: row.id,
        idempotencyKey: row.idempotency_key,
        type: row.type,
        payload: JSON.parse(row.payload) as Record<string, unknown>,
        attempts: row.attempts,
      };
    } catch (error) {
      this.#db.exec("ROLLBACK");
      throw error;
    }
  }

  /**
   * Apply the effect and mark the job done, in one transaction.
   * Returns true when the effect was applied. When the idempotency
   * key already has an effect row, this delivery is a duplicate:
   * the job is still marked done (acked), but the effect is NOT
   * applied again and no second outbox event is written — that pair
   * is the whole duplicate-delivery answer.
   */
  complete(job: Job, result: string): boolean {
    this.#db.exec("BEGIN IMMEDIATE");
    try {
      const info = this.#db
        .prepare(
          "INSERT OR IGNORE INTO effects (idempotency_key, job_id, result, created_at) VALUES (?, ?, ?, ?)",
        )
        .run(job.idempotencyKey, job.id, result, this.#clock());
      const applied = info.changes === 1;
      if (applied) {
        this.#db
          .prepare(
            "INSERT INTO outbox (idempotency_key, event, payload) VALUES (?, 'job.completed', ?)",
          )
          .run(job.idempotencyKey, JSON.stringify({ job_id: job.id, result }));
      }
      this.#db
        .prepare(
          "UPDATE jobs SET status = 'done', claimed_by = NULL, claim_expires_at = NULL WHERE id = ?",
        )
        .run(job.id);
      this.#db.exec("COMMIT");
      return applied;
    } catch (error) {
      this.#db.exec("ROLLBACK");
      throw error;
    }
  }

  /** Record a failure: schedule the retry, or dead-letter the job. */
  fail(
    job: Job,
    error: string,
    retryable: boolean,
    nextAttemptAt: number | null,
  ): void {
    this.#db.exec("BEGIN IMMEDIATE");
    try {
      if (retryable && nextAttemptAt !== null) {
        this.#db
          .prepare(
            "UPDATE jobs SET status = 'pending', attempts = attempts + 1, next_attempt_at = ?, last_error = ?, claimed_by = NULL, claim_expires_at = NULL WHERE id = ?",
          )
          .run(nextAttemptAt, error, job.id);
      } else {
        this.#db
          .prepare(
            "UPDATE jobs SET status = 'dead', attempts = attempts + 1, last_error = ?, claimed_by = NULL, claim_expires_at = NULL WHERE id = ?",
          )
          .run(error, job.id);
      }
      this.#db.exec("COMMIT");
    } catch (caught) {
      this.#db.exec("ROLLBACK");
      throw caught;
    }
  }

  deadJobs(): Job[] {
    const rows = this.#db
      .prepare(
        "SELECT id, idempotency_key, type, payload, attempts FROM jobs WHERE status = 'dead' ORDER BY id",
      )
      .all() as unknown as JobRow[];
    return rows.map((row) => ({
      id: row.id,
      idempotencyKey: row.idempotency_key,
      type: row.type,
      payload: JSON.parse(row.payload) as Record<string, unknown>,
      attempts: row.attempts,
    }));
  }

  /**
   * Return a dead job to pending with its attempt budget restored.
   * The replay tool exists from day one — a dead-letter queue
   * without one is a write-only graveyard.
   */
  replay(jobId: number): boolean {
    const info = this.#db
      .prepare(
        "UPDATE jobs SET status = 'pending', attempts = 0, next_attempt_at = 0, last_error = NULL WHERE id = ? AND status = 'dead'",
      )
      .run(jobId);
    return info.changes === 1;
  }

  /**
   * Queue depths per status. A dead depth above zero is the alarm:
   * wire the runner's check (or your scheduler's) to page on it —
   * silently accumulating dead jobs is the failure mode this type
   * exists to prevent.
   */
  stats(): Stats {
    const counts: Stats = { pending: 0, claimed: 0, done: 0, dead: 0 };
    const rows = this.#db
      .prepare("SELECT status, COUNT(*) AS n FROM jobs GROUP BY status")
      .all() as unknown as Array<{ status: string; n: number }>;
    for (const row of rows) {
      counts[row.status] = row.n;
    }
    const outbox = this.#db
      .prepare("SELECT COUNT(*) AS n FROM outbox WHERE published_at IS NULL")
      .get() as { n: number };
    counts["outbox_unpublished"] = outbox.n;
    return counts;
  }

  /**
   * Publish unpublished outbox rows, marking each after it is
   * accepted. Marking after acceptance keeps publishing
   * at-least-once: a crash between publish and mark republishes, so
   * consumers of the outbox must dedupe on the idempotency key like
   * everyone else in this design.
   */
  drainOutbox(
    publish: (event: string, payload: Record<string, unknown>) => void,
  ): number {
    const rows = this.#db
      .prepare(
        "SELECT id, idempotency_key, event, payload FROM outbox WHERE published_at IS NULL ORDER BY id",
      )
      .all() as unknown as Array<{
      id: number;
      idempotency_key: string;
      event: string;
      payload: string;
    }>;
    let published = 0;
    for (const row of rows) {
      publish(row.event, {
        idempotency_key: row.idempotency_key,
        ...(JSON.parse(row.payload) as Record<string, unknown>),
      });
      this.#db
        .prepare("UPDATE outbox SET published_at = ? WHERE id = ?")
        .run(this.#clock(), row.id);
      published += 1;
    }
    return published;
  }

  /** Raw row count for tests and diagnostics. */
  countRows(table: "effects" | "outbox"): number {
    const row = this.#db
      .prepare(`SELECT COUNT(*) AS n FROM ${table}`)
      .get() as { n: number };
    return row.n;
  }
}
