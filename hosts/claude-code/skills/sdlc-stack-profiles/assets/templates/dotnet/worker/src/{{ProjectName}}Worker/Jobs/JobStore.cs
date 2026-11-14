using System;
using System.Collections.Generic;
using Microsoft.Data.Sqlite;

namespace {{ProjectName}}Worker.Jobs;

/// <summary>A claimed or dead job as the worker loop sees it.</summary>
public sealed record Job(long Id, string IdempotencyKey, string Type, string PayloadJson, int Attempts);

/// <summary>
/// The job store: one SQLite database holding jobs, effects, and the outbox.
///
/// SQLite is the pinned store for the template because it makes the whole
/// correctness story testable with no external services — the transactions
/// the guarantees rest on are real here. In production the same schema and
/// claim protocol map onto any transactional store; the guarantees live in
/// the protocol, not in SQLite. All state transitions happen here, each in
/// its own transaction.
/// </summary>
public sealed class JobStore : IDisposable
{
    private const string Schema = """
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
        """;

    private readonly SqliteConnection _connection;
    private readonly Func<double> _clockSeconds;
    private readonly object _gate = new();

    public JobStore(string path, Func<double>? clockSeconds = null)
    {
        _clockSeconds = clockSeconds ?? (() => DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() / 1000.0);
        _connection = new SqliteConnection($"Data Source={path}");
        _connection.Open();
        using var pragma = new SqliteCommand("PRAGMA journal_mode=WAL", _connection);
        pragma.ExecuteNonQuery();
        using var schema = new SqliteCommand(Schema, _connection);
        schema.ExecuteNonQuery();
    }

    /// <summary>
    /// Add a job, deduplicated by idempotency key. A producer retrying its
    /// own send gets the original job's id back; the key's UNIQUE constraint
    /// is what makes that safe.
    /// </summary>
    public long Enqueue(string type, string payloadJson, string idempotencyKey)
    {
        lock (_gate)
        {
            using var insert = Command(
                "INSERT OR IGNORE INTO jobs (idempotency_key, type, payload, created_at) VALUES ($key, $type, $payload, $now)",
                ("$key", idempotencyKey), ("$type", type), ("$payload", payloadJson), ("$now", _clockSeconds()));
            if (insert.ExecuteNonQuery() == 1)
            {
                using var lastId = new SqliteCommand("SELECT last_insert_rowid()", _connection);
                return (long)lastId.ExecuteScalar()!;
            }

            using var select = Command(
                "SELECT id FROM jobs WHERE idempotency_key = $key", ("$key", idempotencyKey));
            return (long)select.ExecuteScalar()!;
        }
    }

    /// <summary>
    /// Atomically claim the next due job under a lease. A job is due when it
    /// is pending and its scheduled time has come, or when it is claimed and
    /// its lease has expired — the second case is how a job whose worker
    /// crashed mid-flight returns to work.
    /// </summary>
    public Job? Claim(string workerId, double leaseSeconds)
    {
        lock (_gate)
        {
            var now = _clockSeconds();
            Exec("BEGIN IMMEDIATE");
            try
            {
                using var select = Command(
                    """
                    SELECT id, idempotency_key, type, payload, attempts FROM jobs
                    WHERE (status = 'pending' AND next_attempt_at <= $now)
                       OR (status = 'claimed' AND claim_expires_at <= $now)
                    ORDER BY id LIMIT 1
                    """,
                    ("$now", now));
                using var reader = select.ExecuteReader();
                if (!reader.Read())
                {
                    Exec("COMMIT");
                    return null;
                }

                var job = new Job(reader.GetInt64(0), reader.GetString(1), reader.GetString(2), reader.GetString(3), reader.GetInt32(4));
                reader.Close();
                using var update = Command(
                    "UPDATE jobs SET status = 'claimed', claimed_by = $worker, claim_expires_at = $expiry WHERE id = $id",
                    ("$worker", workerId), ("$expiry", now + leaseSeconds), ("$id", job.Id));
                update.ExecuteNonQuery();
                Exec("COMMIT");
                return job;
            }
            catch
            {
                Exec("ROLLBACK");
                throw;
            }
        }
    }

    /// <summary>
    /// Apply the effect and mark the job done, in one transaction. Returns
    /// true when the effect was applied. When the idempotency key already
    /// has an effect row, this delivery is a duplicate: the job is still
    /// marked done (acked), but the effect is NOT applied again and no
    /// second outbox event is written — that pair is the whole
    /// duplicate-delivery answer.
    /// </summary>
    public bool Complete(Job job, string result)
    {
        lock (_gate)
        {
            Exec("BEGIN IMMEDIATE");
            try
            {
                using var insertEffect = Command(
                    "INSERT OR IGNORE INTO effects (idempotency_key, job_id, result, created_at) VALUES ($key, $job, $result, $now)",
                    ("$key", job.IdempotencyKey), ("$job", job.Id), ("$result", result), ("$now", _clockSeconds()));
                var applied = insertEffect.ExecuteNonQuery() == 1;
                if (applied)
                {
                    var payload = new System.Text.Json.Nodes.JsonObject
                    {
                        ["job_id"] = job.Id,
                        ["result"] = result,
                    };
                    using var insertOutbox = Command(
                        "INSERT INTO outbox (idempotency_key, event, payload) VALUES ($key, 'job.completed', $payload)",
                        ("$key", job.IdempotencyKey), ("$payload", payload.ToJsonString()));
                    insertOutbox.ExecuteNonQuery();
                }

                using var update = Command(
                    "UPDATE jobs SET status = 'done', claimed_by = NULL, claim_expires_at = NULL WHERE id = $id",
                    ("$id", job.Id));
                update.ExecuteNonQuery();
                Exec("COMMIT");
                return applied;
            }
            catch
            {
                Exec("ROLLBACK");
                throw;
            }
        }
    }

    /// <summary>Record a failure: schedule the retry, or dead-letter the job.</summary>
    public void Fail(Job job, string error, bool retryable, double? nextAttemptAt)
    {
        lock (_gate)
        {
            Exec("BEGIN IMMEDIATE");
            try
            {
                using var update = retryable && nextAttemptAt is not null
                    ? Command(
                        "UPDATE jobs SET status = 'pending', attempts = attempts + 1, next_attempt_at = $next, last_error = $error, claimed_by = NULL, claim_expires_at = NULL WHERE id = $id",
                        ("$next", nextAttemptAt.Value), ("$error", error), ("$id", job.Id))
                    : Command(
                        "UPDATE jobs SET status = 'dead', attempts = attempts + 1, last_error = $error, claimed_by = NULL, claim_expires_at = NULL WHERE id = $id",
                        ("$error", error), ("$id", job.Id));
                update.ExecuteNonQuery();
                Exec("COMMIT");
            }
            catch
            {
                Exec("ROLLBACK");
                throw;
            }
        }
    }

    public IReadOnlyList<Job> DeadJobs()
    {
        lock (_gate)
        {
            using var select = new SqliteCommand(
                "SELECT id, idempotency_key, type, payload, attempts FROM jobs WHERE status = 'dead' ORDER BY id",
                _connection);
            using var reader = select.ExecuteReader();
            var jobs = new List<Job>();
            while (reader.Read())
            {
                jobs.Add(new Job(reader.GetInt64(0), reader.GetString(1), reader.GetString(2), reader.GetString(3), reader.GetInt32(4)));
            }

            return jobs;
        }
    }

    /// <summary>
    /// Return a dead job to pending with its attempt budget restored. The
    /// replay tool exists from day one — a dead-letter queue without one is
    /// a write-only graveyard.
    /// </summary>
    public bool Replay(long jobId)
    {
        lock (_gate)
        {
            using var update = Command(
                "UPDATE jobs SET status = 'pending', attempts = 0, next_attempt_at = 0, last_error = NULL WHERE id = $id AND status = 'dead'",
                ("$id", jobId));
            return update.ExecuteNonQuery() == 1;
        }
    }

    /// <summary>
    /// Queue depths per status. A dead depth above zero is the alarm: wire
    /// the runner's check (or your scheduler's) to page on it — silently
    /// accumulating dead jobs is the failure mode this type exists to prevent.
    /// </summary>
    public IReadOnlyDictionary<string, long> Stats()
    {
        lock (_gate)
        {
            var counts = new Dictionary<string, long>
            {
                ["pending"] = 0,
                ["claimed"] = 0,
                ["done"] = 0,
                ["dead"] = 0,
            };
            using var select = new SqliteCommand("SELECT status, COUNT(*) FROM jobs GROUP BY status", _connection);
            using (var reader = select.ExecuteReader())
            {
                while (reader.Read())
                {
                    counts[reader.GetString(0)] = reader.GetInt64(1);
                }
            }

            using var outbox = new SqliteCommand("SELECT COUNT(*) FROM outbox WHERE published_at IS NULL", _connection);
            counts["outbox_unpublished"] = (long)outbox.ExecuteScalar()!;
            return counts;
        }
    }

    /// <summary>
    /// Publish unpublished outbox rows, marking each after it is accepted.
    /// Marking after acceptance keeps publishing at-least-once: a crash
    /// between publish and mark republishes, so consumers of the outbox must
    /// dedupe on the idempotency key like everyone else in this design.
    /// </summary>
    public int DrainOutbox(Action<string, string> publish)
    {
        lock (_gate)
        {
            var rows = new List<(long Id, string Key, string Event, string Payload)>();
            using (var select = new SqliteCommand(
                "SELECT id, idempotency_key, event, payload FROM outbox WHERE published_at IS NULL ORDER BY id",
                _connection))
            using (var reader = select.ExecuteReader())
            {
                while (reader.Read())
                {
                    rows.Add((reader.GetInt64(0), reader.GetString(1), reader.GetString(2), reader.GetString(3)));
                }
            }

            var published = 0;
            foreach (var (id, key, evt, payload) in rows)
            {
                // The published shape is the stored payload with the
                // idempotency key merged in, so consumers can dedupe on it.
                var merged = System.Text.Json.Nodes.JsonNode.Parse(payload)!.AsObject();
                merged["idempotency_key"] = key;
                publish(evt, merged.ToJsonString());
                using var update = Command(
                    "UPDATE outbox SET published_at = $now WHERE id = $id",
                    ("$now", _clockSeconds()), ("$id", id));
                update.ExecuteNonQuery();
                published++;
            }

            return published;
        }
    }

    public void Dispose() => _connection.Dispose();

    private SqliteCommand Command(string sql, params (string Name, object Value)[] parameters)
    {
        var command = new SqliteCommand(sql, _connection);
        foreach (var (name, value) in parameters)
        {
            command.Parameters.AddWithValue(name, value);
        }

        return command;
    }

    private void Exec(string sql)
    {
        using var command = new SqliteCommand(sql, _connection);
        command.ExecuteNonQuery();
    }
}
