package com.example.{{PackageName}}.worker;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.DoubleSupplier;
import org.json.JSONObject;

/**
 * The job store: one SQLite database holding jobs, effects, and the outbox, through the xerial JDBC
 * driver.
 *
 * <p>SQLite is the pinned store for the template because it makes the whole correctness story
 * testable with no external services — the transactions the guarantees rest on are real here. In
 * production the same schema and claim protocol map onto any transactional store; the guarantees
 * live in the protocol, not in SQLite. All state transitions happen here, each in its own
 * transaction, mirroring the other stacks' worker stores statement for statement.
 */
public final class JobStore implements AutoCloseable {

  private static final String SCHEMA =
      """
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

  private final Connection connection;
  private final DoubleSupplier clockSeconds;

  public JobStore(String path) {
    this(path, () -> System.currentTimeMillis() / 1000.0);
  }

  public JobStore(String path, DoubleSupplier clockSeconds) {
    this.clockSeconds = clockSeconds;
    try {
      this.connection = DriverManager.getConnection("jdbc:sqlite:" + path);
      try (var stmt = connection.createStatement()) {
        stmt.execute("PRAGMA journal_mode=WAL");
        stmt.executeUpdate(SCHEMA);
      }
    } catch (SQLException e) {
      throw new IllegalStateException("cannot open job store at " + path, e);
    }
  }

  /** A claimed or dead job as the worker loop sees it. */
  public record Job(
      long id, String idempotencyKey, String type, JSONObject payload, int attempts) {}

  /**
   * Add a job, deduplicated by idempotency key. A producer retrying its own send gets the original
   * job's id back; the key's UNIQUE constraint is what makes that safe.
   */
  public synchronized long enqueue(String type, JSONObject payload, String idempotencyKey) {
    try (var insert =
        connection.prepareStatement(
            "INSERT OR IGNORE INTO jobs (idempotency_key, type, payload, created_at)"
                + " VALUES (?, ?, ?, ?)")) {
      insert.setString(1, idempotencyKey);
      insert.setString(2, type);
      insert.setString(3, payload.toString());
      insert.setDouble(4, clockSeconds.getAsDouble());
      if (insert.executeUpdate() == 1) {
        try (var stmt = connection.createStatement();
            var rs = stmt.executeQuery("SELECT last_insert_rowid()")) {
          rs.next();
          return rs.getLong(1);
        }
      }
      try (var select =
          connection.prepareStatement("SELECT id FROM jobs WHERE idempotency_key = ?")) {
        select.setString(1, idempotencyKey);
        try (var rs = select.executeQuery()) {
          rs.next();
          return rs.getLong(1);
        }
      }
    } catch (SQLException e) {
      throw new IllegalStateException(e);
    }
  }

  /**
   * Atomically claim the next due job under a lease. A job is due when it is pending and its
   * scheduled time has come, or when it is claimed and its lease has expired — the second case is
   * how a job whose worker crashed mid-flight returns to work.
   */
  public synchronized Job claim(String workerId, double leaseSeconds) {
    var now = clockSeconds.getAsDouble();
    try {
      exec("BEGIN IMMEDIATE");
      try (var select =
          connection.prepareStatement(
              "SELECT id, idempotency_key, type, payload, attempts FROM jobs"
                  + " WHERE (status = 'pending' AND next_attempt_at <= ?)"
                  + "    OR (status = 'claimed' AND claim_expires_at <= ?)"
                  + " ORDER BY id LIMIT 1")) {
        select.setDouble(1, now);
        select.setDouble(2, now);
        try (var rs = select.executeQuery()) {
          if (!rs.next()) {
            exec("COMMIT");
            return null;
          }
          var job =
              new Job(
                  rs.getLong(1),
                  rs.getString(2),
                  rs.getString(3),
                  new JSONObject(rs.getString(4)),
                  rs.getInt(5));
          try (var update =
              connection.prepareStatement(
                  "UPDATE jobs SET status = 'claimed', claimed_by = ?, claim_expires_at = ?"
                      + " WHERE id = ?")) {
            update.setString(1, workerId);
            update.setDouble(2, now + leaseSeconds);
            update.setLong(3, job.id());
            update.executeUpdate();
          }
          exec("COMMIT");
          return job;
        }
      } catch (SQLException | RuntimeException e) {
        execQuietly("ROLLBACK");
        throw e;
      }
    } catch (SQLException e) {
      throw new IllegalStateException(e);
    }
  }

  /**
   * Apply the effect and mark the job done, in one transaction. Returns true when the effect was
   * applied. When the idempotency key already has an effect row, this delivery is a duplicate: the
   * job is still marked done (acked), but the effect is NOT applied again and no second outbox
   * event is written — that pair is the whole duplicate-delivery answer.
   */
  public synchronized boolean complete(Job job, String result) {
    try {
      exec("BEGIN IMMEDIATE");
      try {
        boolean applied;
        try (var insert =
            connection.prepareStatement(
                "INSERT OR IGNORE INTO effects (idempotency_key, job_id, result, created_at)"
                    + " VALUES (?, ?, ?, ?)")) {
          insert.setString(1, job.idempotencyKey());
          insert.setLong(2, job.id());
          insert.setString(3, result);
          insert.setDouble(4, clockSeconds.getAsDouble());
          applied = insert.executeUpdate() == 1;
        }
        if (applied) {
          var payload = new JSONObject().put("job_id", job.id()).put("result", result);
          try (var insert =
              connection.prepareStatement(
                  "INSERT INTO outbox (idempotency_key, event, payload)"
                      + " VALUES (?, 'job.completed', ?)")) {
            insert.setString(1, job.idempotencyKey());
            insert.setString(2, payload.toString());
            insert.executeUpdate();
          }
        }
        try (var update =
            connection.prepareStatement(
                "UPDATE jobs SET status = 'done', claimed_by = NULL, claim_expires_at = NULL"
                    + " WHERE id = ?")) {
          update.setLong(1, job.id());
          update.executeUpdate();
        }
        exec("COMMIT");
        return applied;
      } catch (SQLException | RuntimeException e) {
        execQuietly("ROLLBACK");
        throw e;
      }
    } catch (SQLException e) {
      throw new IllegalStateException(e);
    }
  }

  /** Record a failure: schedule the retry, or dead-letter the job. */
  public synchronized void fail(Job job, String error, boolean retryable, Double nextAttemptAt) {
    try {
      exec("BEGIN IMMEDIATE");
      try {
        if (retryable && nextAttemptAt != null) {
          try (var update =
              connection.prepareStatement(
                  "UPDATE jobs SET status = 'pending', attempts = attempts + 1,"
                      + " next_attempt_at = ?, last_error = ?, claimed_by = NULL,"
                      + " claim_expires_at = NULL WHERE id = ?")) {
            update.setDouble(1, nextAttemptAt);
            update.setString(2, error);
            update.setLong(3, job.id());
            update.executeUpdate();
          }
        } else {
          try (var update =
              connection.prepareStatement(
                  "UPDATE jobs SET status = 'dead', attempts = attempts + 1, last_error = ?,"
                      + " claimed_by = NULL, claim_expires_at = NULL WHERE id = ?")) {
            update.setString(1, error);
            update.setLong(2, job.id());
            update.executeUpdate();
          }
        }
        exec("COMMIT");
      } catch (SQLException | RuntimeException e) {
        execQuietly("ROLLBACK");
        throw e;
      }
    } catch (SQLException e) {
      throw new IllegalStateException(e);
    }
  }

  public synchronized List<Job> deadJobs() {
    var jobs = new ArrayList<Job>();
    try (var stmt = connection.createStatement();
        var rs =
            stmt.executeQuery(
                "SELECT id, idempotency_key, type, payload, attempts FROM jobs"
                    + " WHERE status = 'dead' ORDER BY id")) {
      while (rs.next()) {
        jobs.add(
            new Job(
                rs.getLong(1),
                rs.getString(2),
                rs.getString(3),
                new JSONObject(rs.getString(4)),
                rs.getInt(5)));
      }
      return jobs;
    } catch (SQLException e) {
      throw new IllegalStateException(e);
    }
  }

  /**
   * Return a dead job to pending with its attempt budget restored. The replay tool exists from day
   * one — a dead-letter queue without one is a write-only graveyard.
   */
  public synchronized boolean replay(long jobId) {
    try (var update =
        connection.prepareStatement(
            "UPDATE jobs SET status = 'pending', attempts = 0, next_attempt_at = 0,"
                + " last_error = NULL WHERE id = ? AND status = 'dead'")) {
      update.setLong(1, jobId);
      return update.executeUpdate() == 1;
    } catch (SQLException e) {
      throw new IllegalStateException(e);
    }
  }

  /**
   * Queue depths per status. A dead depth above zero is the alarm: wire the runner's check (or your
   * scheduler's) to page on it — silently accumulating dead jobs is the failure mode this type
   * exists to prevent.
   */
  public synchronized Map<String, Long> stats() {
    var counts = new LinkedHashMap<String, Long>();
    counts.put("pending", 0L);
    counts.put("claimed", 0L);
    counts.put("done", 0L);
    counts.put("dead", 0L);
    try (var stmt = connection.createStatement()) {
      try (var rs = stmt.executeQuery("SELECT status, COUNT(*) FROM jobs GROUP BY status")) {
        while (rs.next()) {
          counts.put(rs.getString(1), rs.getLong(2));
        }
      }
      try (var rs = stmt.executeQuery("SELECT COUNT(*) FROM outbox WHERE published_at IS NULL")) {
        rs.next();
        counts.put("outbox_unpublished", rs.getLong(1));
      }
      return counts;
    } catch (SQLException e) {
      throw new IllegalStateException(e);
    }
  }

  /** A consumer of outbox events; see {@link #drainOutbox}. */
  @FunctionalInterface
  public interface OutboxPublisher {
    void publish(String event, JSONObject payload);
  }

  /**
   * Publish unpublished outbox rows, marking each after it is accepted. Marking after acceptance
   * keeps publishing at-least-once: a crash between publish and mark republishes, so consumers of
   * the outbox must dedupe on the idempotency key like everyone else in this design.
   */
  public synchronized int drainOutbox(OutboxPublisher publisher) {
    var rows = new ArrayList<Object[]>();
    try (var stmt = connection.createStatement();
        var rs =
            stmt.executeQuery(
                "SELECT id, idempotency_key, event, payload FROM outbox"
                    + " WHERE published_at IS NULL ORDER BY id")) {
      while (rs.next()) {
        rows.add(new Object[] {rs.getLong(1), rs.getString(2), rs.getString(3), rs.getString(4)});
      }
    } catch (SQLException e) {
      throw new IllegalStateException(e);
    }
    var published = 0;
    for (var row : rows) {
      var merged = new JSONObject((String) row[3]).put("idempotency_key", (String) row[1]);
      publisher.publish((String) row[2], merged);
      try (var update =
          connection.prepareStatement("UPDATE outbox SET published_at = ? WHERE id = ?")) {
        update.setDouble(1, clockSeconds.getAsDouble());
        update.setLong(2, (Long) row[0]);
        update.executeUpdate();
      } catch (SQLException e) {
        throw new IllegalStateException(e);
      }
      published++;
    }
    return published;
  }

  /** Raw row count for tests and diagnostics. */
  public synchronized long countRows(String table) {
    if (!table.equals("effects") && !table.equals("outbox")) {
      throw new IllegalArgumentException("table must be effects or outbox");
    }
    try (var stmt = connection.createStatement();
        var rs = stmt.executeQuery("SELECT COUNT(*) FROM " + table)) {
      rs.next();
      return rs.getLong(1);
    } catch (SQLException e) {
      throw new IllegalStateException(e);
    }
  }

  @Override
  public void close() {
    try {
      connection.close();
    } catch (SQLException e) {
      throw new IllegalStateException(e);
    }
  }

  private void exec(String sql) throws SQLException {
    try (var stmt = connection.createStatement()) {
      stmt.execute(sql);
    }
  }

  private void execQuietly(String sql) {
    try {
      exec(sql);
    } catch (SQLException ignored) {
      // A failed rollback leaves the connection to surface the original error.
    }
  }
}
