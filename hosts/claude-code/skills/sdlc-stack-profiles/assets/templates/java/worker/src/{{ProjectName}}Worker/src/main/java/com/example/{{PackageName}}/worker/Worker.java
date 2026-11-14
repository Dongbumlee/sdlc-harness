package com.example.{{PackageName}}.worker;

import java.util.Map;
import java.util.Random;
import java.util.function.DoubleSupplier;
import org.json.JSONObject;

/**
 * The worker loop: claim, handle, record — with classified retries.
 *
 * <p>Error classification is the handler's contract: throw {@link PermanentError} for input that
 * will never succeed (bad payload, unknown type), and anything else — including a bare exception
 * the handler did not anticipate — is treated as retryable, because under at-least-once delivery
 * retrying the unknown is safer than dead-lettering it. Retryable failures back off exponentially
 * with full jitter and dead-letter when the attempt budget runs out.
 */
public final class Worker {

  /** A job handler: returns the effect's result string. */
  @FunctionalInterface
  public interface Handler {
    String handle(JSONObject payload);
  }

  /** The job can never succeed as delivered: dead-letter it now. */
  public static final class PermanentError extends RuntimeException {
    public PermanentError(String message) {
      super(message);
    }
  }

  /** The job might succeed later: back off and retry it. */
  public static final class RetryableError extends RuntimeException {
    public RetryableError(String message) {
      super(message);
    }
  }

  private final JobStore store;
  private final Map<String, Handler> handlers;
  private final String workerId;
  private final DoubleSupplier clockSeconds;
  private final Random rng;
  private final int maxAttempts;
  private final double baseDelaySeconds;
  private final double maxDelaySeconds;
  private final double leaseSeconds;

  public Worker(JobStore store, Map<String, Handler> handlers) {
    this(
        store,
        handlers,
        "worker-1",
        () -> System.currentTimeMillis() / 1000.0,
        new Random(),
        5,
        1.0,
        60.0,
        30.0);
  }

  public Worker(
      JobStore store,
      Map<String, Handler> handlers,
      String workerId,
      DoubleSupplier clockSeconds,
      Random rng,
      int maxAttempts,
      double baseDelaySeconds,
      double maxDelaySeconds,
      double leaseSeconds) {
    this.store = store;
    this.handlers = handlers;
    this.workerId = workerId;
    this.clockSeconds = clockSeconds;
    this.rng = rng;
    this.maxAttempts = maxAttempts;
    this.baseDelaySeconds = baseDelaySeconds;
    this.maxDelaySeconds = maxDelaySeconds;
    this.leaseSeconds = leaseSeconds;
  }

  /** Full-jitter exponential backoff for the next attempt number. */
  public double backoff(int attempts) {
    var capped = Math.min(maxDelaySeconds, baseDelaySeconds * Math.pow(2, attempts));
    return rng.nextDouble() * capped;
  }

  /** Process one due job if there is one. Returns true when work was done. */
  public boolean runOnce() {
    var job = store.claim(workerId, leaseSeconds);
    if (job == null) {
      return false;
    }
    var handler = handlers.get(job.type());
    if (handler == null) {
      store.fail(job, "unknown job type '" + job.type() + "'", false, null);
      return true;
    }
    try {
      var result = handler.handle(job.payload());
      store.complete(job, result);
    } catch (PermanentError e) {
      store.fail(job, e.getMessage(), false, null);
    } catch (RuntimeException e) {
      // Classified as retryable, never swallowed.
      scheduleRetry(job, String.valueOf(e.getMessage()));
    }
    return true;
  }

  private void scheduleRetry(JobStore.Job job, String error) {
    var attemptsAfter = job.attempts() + 1;
    if (attemptsAfter >= maxAttempts) {
      store.fail(job, error, false, null);
    } else {
      store.fail(job, error, true, clockSeconds.getAsDouble() + backoff(attemptsAfter));
    }
  }
}
