// Package jobs is the job store: one SQLite database holding jobs,
// effects, and the outbox, through the pure-Go modernc.org/sqlite
// driver (no cgo, so the shipped binary is exactly the tested one).
//
// SQLite is the pinned store for the template because it makes the
// whole correctness story testable with no external services — the
// transactions the guarantees rest on are real here. In production
// the same schema and claim protocol map onto any transactional
// store; the guarantees live in the protocol, not in SQLite. All
// state transitions happen here, each in its own transaction,
// mirroring the other stacks' worker stores statement for
// statement. The pool is limited to one open connection so the
// raw BEGIN IMMEDIATE / COMMIT / ROLLBACK statements are
// serialized the way the protocol assumes.
package jobs

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"strings"

	_ "modernc.org/sqlite" // register the pure-Go SQLite driver
)

const schema = `
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
);`

// Clock returns epoch seconds. Tests inject a fake one.
type Clock func() float64

// Job is a claimed or dead job as the worker loop sees it.
type Job struct {
	ID             int64
	IdempotencyKey string
	Type           string
	Payload        map[string]any
	Attempts       int
}

// Store is the job store.
type Store struct {
	db    *sql.DB
	clock Clock
}

// NewStore opens (or creates) the store at path.
func NewStore(path string, clock Clock) (*Store, error) {
	db, err := sql.Open("sqlite", path)
	if err != nil {
		return nil, fmt.Errorf("open job store: %w", err)
	}
	db.SetMaxOpenConns(1)
	if _, err := db.Exec("PRAGMA journal_mode=WAL"); err != nil {
		return nil, err
	}
	if _, err := db.Exec(schema); err != nil {
		return nil, err
	}
	return &Store{db: db, clock: clock}, nil
}

func (s *Store) Close() error { return s.db.Close() }

func (s *Store) exec(sql string, args ...any) error {
	_, err := s.db.Exec(sql, args...)
	return err
}

// Enqueue adds a job, deduplicated by idempotency key. A producer
// retrying its own send gets the original job's id back; the key's
// UNIQUE constraint is what makes that safe.
func (s *Store) Enqueue(jobType string, payload map[string]any, idempotencyKey string) (int64, error) {
	raw, err := json.Marshal(payload)
	if err != nil {
		return 0, err
	}
	res, err := s.db.Exec(
		"INSERT OR IGNORE INTO jobs (idempotency_key, type, payload, created_at) VALUES (?, ?, ?, ?)",
		idempotencyKey, jobType, string(raw), s.clock())
	if err != nil {
		return 0, err
	}
	if n, err := res.RowsAffected(); err == nil && n == 1 {
		id, err := res.LastInsertId()
		if err != nil {
			return 0, err
		}
		return id, nil
	}
	var id int64
	err = s.db.QueryRow("SELECT id FROM jobs WHERE idempotency_key = ?", idempotencyKey).Scan(&id)
	return id, err
}

// Claim atomically claims the next due job under a lease. A job is
// due when it is pending and its scheduled time has come, or when it
// is claimed and its lease has expired — the second case is how a
// job whose worker crashed mid-flight returns to work.
func (s *Store) Claim(workerID string, leaseSeconds float64) (*Job, error) {
	now := s.clock()
	if err := s.exec("BEGIN IMMEDIATE"); err != nil {
		return nil, err
	}
	defer func() { _ = s.exec("ROLLBACK") }() // no-op after COMMIT
	row := s.db.QueryRow(
		`SELECT id, idempotency_key, type, payload, attempts FROM jobs
		 WHERE (status = 'pending' AND next_attempt_at <= ?)
		    OR (status = 'claimed' AND claim_expires_at <= ?)
		 ORDER BY id LIMIT 1`, now, now)
	var job Job
	var raw string
	if err := row.Scan(&job.ID, &job.IdempotencyKey, &job.Type, &raw, &job.Attempts); err != nil {
		if err == sql.ErrNoRows {
			_ = s.exec("COMMIT")
			return nil, nil
		}
		return nil, err
	}
	if err := json.Unmarshal([]byte(raw), &job.Payload); err != nil {
		return nil, err
	}
	if err := s.exec(
		"UPDATE jobs SET status = 'claimed', claimed_by = ?, claim_expires_at = ? WHERE id = ?",
		workerID, now+leaseSeconds, job.ID); err != nil {
		return nil, err
	}
	if err := s.exec("COMMIT"); err != nil {
		return nil, err
	}
	return &job, nil
}

// Complete applies the effect and marks the job done, in one
// transaction. It reports whether the effect was applied. When the
// idempotency key already has an effect row, this delivery is a
// duplicate: the job is still marked done (acked), but the effect
// is NOT applied again and no second outbox event is written —
// that pair is the whole duplicate-delivery answer.
func (s *Store) Complete(job *Job, result string) (bool, error) {
	if err := s.exec("BEGIN IMMEDIATE"); err != nil {
		return false, err
	}
	defer func() { _ = s.exec("ROLLBACK") }()
	res, err := s.db.Exec(
		"INSERT OR IGNORE INTO effects (idempotency_key, job_id, result, created_at) VALUES (?, ?, ?, ?)",
		job.IdempotencyKey, job.ID, result, s.clock())
	if err != nil {
		return false, err
	}
	applied := false
	if n, err := res.RowsAffected(); err == nil && n == 1 {
		applied = true
	}
	if applied {
		raw, err := json.Marshal(map[string]any{"job_id": job.ID, "result": result})
		if err != nil {
			return false, err
		}
		if err := s.exec(
			"INSERT INTO outbox (idempotency_key, event, payload) VALUES (?, 'job.completed', ?)",
			job.IdempotencyKey, string(raw)); err != nil {
			return false, err
		}
	}
	if err := s.exec(
		"UPDATE jobs SET status = 'done', claimed_by = NULL, claim_expires_at = NULL WHERE id = ?",
		job.ID); err != nil {
		return false, err
	}
	return applied, s.exec("COMMIT")
}

// Fail records a failure: schedule the retry, or dead-letter the job.
func (s *Store) Fail(job *Job, errMsg string, retryable bool, nextAttemptAt float64) error {
	if err := s.exec("BEGIN IMMEDIATE"); err != nil {
		return err
	}
	defer func() { _ = s.exec("ROLLBACK") }()
	var err error
	if retryable {
		err = s.exec(
			"UPDATE jobs SET status = 'pending', attempts = attempts + 1, next_attempt_at = ?, last_error = ?, claimed_by = NULL, claim_expires_at = NULL WHERE id = ?",
			nextAttemptAt, errMsg, job.ID)
	} else {
		err = s.exec(
			"UPDATE jobs SET status = 'dead', attempts = attempts + 1, last_error = ?, claimed_by = NULL, claim_expires_at = NULL WHERE id = ?",
			errMsg, job.ID)
	}
	if err != nil {
		return err
	}
	return s.exec("COMMIT")
}

func (s *Store) DeadJobs() ([]*Job, error) {
	rows, err := s.db.Query(
		"SELECT id, idempotency_key, type, payload, attempts FROM jobs WHERE status = 'dead' ORDER BY id")
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var jobs []*Job
	for rows.Next() {
		var job Job
		var raw string
		if err := rows.Scan(&job.ID, &job.IdempotencyKey, &job.Type, &raw, &job.Attempts); err != nil {
			return nil, err
		}
		if err := json.Unmarshal([]byte(raw), &job.Payload); err != nil {
			return nil, err
		}
		jobs = append(jobs, &job)
	}
	return jobs, rows.Err()
}

// Replay returns a dead job to pending with its attempt budget
// restored. The replay tool exists from day one — a dead-letter
// queue without one is a write-only graveyard.
func (s *Store) Replay(jobID int64) (bool, error) {
	res, err := s.db.Exec(
		"UPDATE jobs SET status = 'pending', attempts = 0, next_attempt_at = 0, last_error = NULL WHERE id = ? AND status = 'dead'",
		jobID)
	if err != nil {
		return false, err
	}
	n, err := res.RowsAffected()
	return n == 1, err
}

// Stats returns queue depths per status. A dead depth above zero
// is the alarm: wire the runner's check (or your scheduler's) to
// page on it — silently accumulating dead jobs is the failure
// mode this type exists to prevent.
func (s *Store) Stats() (map[string]int, error) {
	counts := map[string]int{"pending": 0, "claimed": 0, "done": 0, "dead": 0}
	rows, err := s.db.Query("SELECT status, COUNT(*) FROM jobs GROUP BY status")
	if err != nil {
		return nil, err
	}
	for rows.Next() {
		var status string
		var n int
		if err := rows.Scan(&status, &n); err != nil {
			rows.Close()
			return nil, err
		}
		counts[status] = n
	}
	rows.Close()
	if err := rows.Err(); err != nil {
		return nil, err
	}
	var unpublished int
	if err := s.db.QueryRow("SELECT COUNT(*) FROM outbox WHERE published_at IS NULL").Scan(&unpublished); err != nil {
		return nil, err
	}
	counts["outbox_unpublished"] = unpublished
	return counts, nil
}

// Publisher publishes one outbox event; see DrainOutbox.
type Publisher func(event string, payload map[string]any)

// DrainOutbox publishes unpublished outbox rows, marking each
// after it is accepted. Marking after acceptance keeps publishing
// at-least-once: a crash between publish and mark republishes, so
// consumers of the outbox must dedupe on the idempotency key like
// everyone else in this design.
func (s *Store) DrainOutbox(publish Publisher) (int, error) {
	rows, err := s.db.Query(
		"SELECT id, idempotency_key, event, payload FROM outbox WHERE published_at IS NULL ORDER BY id")
	if err != nil {
		return 0, err
	}
	type pending struct {
		id             int64
		idempotencyKey string
		event          string
		raw            string
	}
	var pendingRows []pending
	for rows.Next() {
		var p pending
		if err := rows.Scan(&p.id, &p.idempotencyKey, &p.event, &p.raw); err != nil {
			rows.Close()
			return 0, err
		}
		pendingRows = append(pendingRows, p)
	}
	rows.Close()
	if err := rows.Err(); err != nil {
		return 0, err
	}
	for _, p := range pendingRows {
		var payload map[string]any
		if err := json.Unmarshal([]byte(p.raw), &payload); err != nil {
			return 0, err
		}
		payload["idempotency_key"] = p.idempotencyKey
		publish(p.event, payload)
		if err := s.exec("UPDATE outbox SET published_at = ? WHERE id = ?", s.clock(), p.id); err != nil {
			return 0, err
		}
	}
	return len(pendingRows), nil
}

// CountRows returns a raw row count, for tests and diagnostics.
func (s *Store) CountRows(table string) (int, error) {
	if table != "effects" && table != "outbox" {
		return 0, fmt.Errorf("table must be effects or outbox")
	}
	var n int
	err := s.db.QueryRow(fmt.Sprintf("SELECT COUNT(*) FROM %s", strings.TrimSpace(table))).Scan(&n)
	return n, err
}
