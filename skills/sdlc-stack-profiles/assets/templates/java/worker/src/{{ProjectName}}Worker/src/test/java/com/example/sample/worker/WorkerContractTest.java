package com.example.{{PackageName}}.worker;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Map;
import java.util.Random;
import java.util.concurrent.atomic.AtomicInteger;
import org.json.JSONObject;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/**
 * The worker standard's defining tests (see the sdlc-stack-profiles skill): duplicate delivery
 * applies the effect once, a poison message dead-letters, and a crash mid-job recovers through the
 * claim lease. Plus the supporting guarantees: backoff scheduling, the transactional outbox, and
 * dead-letter replay. All against a fake clock (no sleeping); the random source is fixed so backoff
 * delays are exact.
 */
class WorkerContractTest {

  // A one-cell mutable clock: tests advance it by hand (no sleeping).
  private final double[] now = {1000.0};

  private JobStore newStore(Path dir) {
    return new JobStore(dir.resolve("jobs.db").toString(), () -> now[0]);
  }

  private Worker newWorker(JobStore store, Map<String, Worker.Handler> handlers) {
    return newWorker(store, handlers, 5, 1.0);
  }

  private Worker newWorker(
      JobStore store, Map<String, Worker.Handler> handlers, int maxAttempts, double baseDelay) {
    // A Random whose nextDouble is always 0.5: full-jitter delays land
    // exactly halfway, so the schedule is deterministic.
    var fixed =
        new Random() {
          @Override
          public double nextDouble() {
            return 0.5;
          }
        };
    return new Worker(
        store, handlers, "worker-1", () -> now[0], fixed, maxAttempts, baseDelay, 60.0, 30.0);
  }

  @Test
  void duplicateDeliveryAppliesEffectOnce(@TempDir Path dir) {
    try (var store = newStore(dir)) {
      var worker = newWorker(store, Handlers.ALL);
      var payload = new JSONObject().put("text", "Hello World");
      var jobId = store.enqueue("slugify", payload, "k-1");
      // The producer retries its own send with the same key: same job.
      assertEquals(jobId, store.enqueue("slugify", payload, "k-1"));

      assertTrue(worker.runOnce());
      assertEquals(1L, store.stats().get("done"));

      // The ack was lost, so the same job is completed a second time:
      // complete() must report the duplicate, and the effect must
      // still exist exactly once, with no second outbox row.
      var redelivered = new JobStore.Job(jobId, "k-1", "slugify", payload, 0);
      assertFalse(store.complete(redelivered, "hello-world"));
      assertEquals(1, store.countRows("effects"));
      assertEquals(1, store.countRows("outbox"));
    }
  }

  @Test
  void poisonMessageDeadLettersImmediately(@TempDir Path dir) {
    try (var store = newStore(dir)) {
      Map<String, Worker.Handler> poison =
          Map.of(
              "slugify",
              payload -> {
                throw new Worker.PermanentError("payload.text must be a non-empty string");
              });
      var worker = newWorker(store, poison);
      store.enqueue("slugify", new JSONObject().put("text", ""), "poison-1");

      assertTrue(worker.runOnce());
      var stats = store.stats();
      assertEquals(1L, stats.get("dead"));
      assertEquals(0L, stats.get("pending"));
      assertEquals("poison-1", store.deadJobs().get(0).idempotencyKey());
    }
  }

  @Test
  void unknownJobTypeIsPermanent(@TempDir Path dir) {
    try (var store = newStore(dir)) {
      var worker = newWorker(store, Handlers.ALL);
      store.enqueue("frobnicate", new JSONObject(), "mystery-1");
      assertTrue(worker.runOnce());
      assertEquals(1L, store.stats().get("dead"));
    }
  }

  @Test
  void crashMidJobRecoversThroughLease(@TempDir Path dir) {
    try (var store = newStore(dir)) {
      store.enqueue("slugify", new JSONObject().put("text", "Crash Test"), "crash-1");

      // Worker A claims the job and dies before completing it.
      var claimed = store.claim("worker-a", 30);
      assertTrue(claimed != null);
      assertNull(store.claim("worker-b", 30)); // lease still held

      // After the lease expires, worker B picks the same job up and
      // the effect lands exactly once.
      now[0] += 31;
      var workerB = newWorker(store, Handlers.ALL);
      assertTrue(workerB.runOnce());
      assertEquals(1L, store.stats().get("done"));
      assertEquals(1, store.countRows("effects"));
    }
  }

  @Test
  void retryableFailureBacksOffThenSucceeds(@TempDir Path dir) {
    try (var store = newStore(dir)) {
      var calls = new AtomicInteger();
      Map<String, Worker.Handler> flaky =
          Map.of(
              "slugify",
              payload -> {
                if (calls.incrementAndGet() < 3) {
                  throw new Worker.RetryableError("downstream unavailable");
                }
                return Handlers.slugify(payload);
              });
      var worker = newWorker(store, flaky, 5, 10.0);
      store.enqueue("slugify", new JSONObject().put("text", "Flaky Job"), "flaky-1");

      assertTrue(worker.runOnce()); // attempt 1 fails; delay = 0.5 * 20 = 10
      assertEquals(1L, store.stats().get("pending"));
      assertFalse(worker.runOnce()); // not yet due: backoff is real

      now[0] += 11;
      assertTrue(worker.runOnce()); // attempt 2 fails; delay = 0.5 * 40 = 20
      now[0] += 21;
      assertTrue(worker.runOnce()); // attempt 3 succeeds
      assertEquals(1L, store.stats().get("done"));
    }
  }

  @Test
  void retryBudgetExhaustionDeadLetters(@TempDir Path dir) {
    try (var store = newStore(dir)) {
      Map<String, Worker.Handler> alwaysDown =
          Map.of(
              "slugify",
              payload -> {
                throw new Worker.RetryableError("still down");
              });
      var worker = newWorker(store, alwaysDown, 3, 1.0);
      store.enqueue("slugify", new JSONObject().put("text", "Doomed"), "doomed-1");

      for (int i = 0; i < 3; i++) {
        assertTrue(worker.runOnce());
        now[0] += 100;
      }
      assertEquals(1L, store.stats().get("dead"));
      assertEquals(3, store.deadJobs().get(0).attempts());
    }
  }

  @Test
  void outboxDrainsOnceAndMarks(@TempDir Path dir) {
    try (var store = newStore(dir)) {
      var worker = newWorker(store, Handlers.ALL);
      store.enqueue("slugify", new JSONObject().put("text", "Outbox Test"), "ob-1");
      assertTrue(worker.runOnce());

      var received = new ArrayList<Object[]>();
      assertEquals(
          1, store.drainOutbox((event, payload) -> received.add(new Object[] {event, payload})));
      assertEquals("job.completed", received.get(0)[0]);
      assertEquals("ob-1", ((JSONObject) received.get(0)[1]).getString("idempotency_key"));
      assertEquals(
          0, store.drainOutbox((event, payload) -> received.add(new Object[] {event, payload})));
      assertEquals(1, received.size());
    }
  }

  @Test
  void replayRestoresDeadJob(@TempDir Path dir) {
    try (var store = newStore(dir)) {
      Map<String, Worker.Handler> poison =
          Map.of(
              "slugify",
              payload -> {
                throw new Worker.PermanentError("bad");
              });
      var jobId = store.enqueue("slugify", new JSONObject().put("text", "x"), "replay-1");
      assertTrue(newWorker(store, poison).runOnce());
      assertEquals(1L, store.stats().get("dead"));

      assertTrue(store.replay(jobId));
      assertEquals(1L, store.stats().get("pending"));

      var fixed = newWorker(store, Handlers.ALL); // the real handler this time
      assertTrue(fixed.runOnce());
      assertEquals(1L, store.stats().get("done"));
    }
  }
}
