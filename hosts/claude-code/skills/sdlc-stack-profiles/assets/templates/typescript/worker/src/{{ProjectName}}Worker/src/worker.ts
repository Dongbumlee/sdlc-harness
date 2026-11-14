/**
 * The worker loop: claim, handle, record — with classified retries.
 *
 * Error classification is the handler's contract: throw
 * `PermanentError` for input that will never succeed (bad payload,
 * unknown type), and anything else — including a bare error the
 * handler did not anticipate — is treated as retryable, because
 * under at-least-once delivery retrying the unknown is safer than
 * dead-lettering it. Retryable failures back off exponentially with
 * full jitter and dead-letter when the attempt budget runs out.
 */

import type { Job, JobStore } from "./store.js";

export type Handler = (payload: Record<string, unknown>) => string;

/** The job can never succeed as delivered: dead-letter it now. */
export class PermanentError extends Error {}

/** The job might succeed later: back off and retry it. */
export class RetryableError extends Error {}

export interface WorkerOptions {
  workerId?: string;
  clock?: () => number;
  random?: () => number;
  maxAttempts?: number;
  baseDelaySeconds?: number;
  maxDelaySeconds?: number;
  leaseSeconds?: number;
}

export class Worker {
  readonly #store: JobStore;
  readonly #handlers: Record<string, Handler>;
  readonly #workerId: string;
  readonly #clock: () => number;
  readonly #random: () => number;
  readonly #maxAttempts: number;
  readonly #baseDelaySeconds: number;
  readonly #maxDelaySeconds: number;
  readonly #leaseSeconds: number;

  constructor(
    store: JobStore,
    handlers: Record<string, Handler>,
    options: WorkerOptions = {},
  ) {
    this.#store = store;
    this.#handlers = handlers;
    this.#workerId = options.workerId ?? "worker-1";
    this.#clock = options.clock ?? (() => Date.now() / 1000);
    this.#random = options.random ?? Math.random;
    this.#maxAttempts = options.maxAttempts ?? 5;
    this.#baseDelaySeconds = options.baseDelaySeconds ?? 1;
    this.#maxDelaySeconds = options.maxDelaySeconds ?? 60;
    this.#leaseSeconds = options.leaseSeconds ?? 30;
  }

  /** Full-jitter exponential backoff for the next attempt number. */
  backoff(attempts: number): number {
    const capped = Math.min(
      this.#maxDelaySeconds,
      this.#baseDelaySeconds * 2 ** attempts,
    );
    return this.#random() * capped;
  }

  /** Process one due job if there is one. Returns true when work was done. */
  runOnce(): boolean {
    const job = this.#store.claim(this.#workerId, this.#leaseSeconds);
    if (!job) {
      return false;
    }
    const handler = this.#handlers[job.type];
    if (!handler) {
      this.#store.fail(job, `unknown job type '${job.type}'`, false, null);
      return true;
    }
    try {
      const result = handler(job.payload);
      this.#store.complete(job, result);
    } catch (error) {
      if (error instanceof PermanentError) {
        this.#store.fail(job, error.message, false, null);
      } else {
        // Classified as retryable, never swallowed.
        this.#scheduleRetry(
          job,
          error instanceof Error ? error.message : String(error),
        );
      }
    }
    return true;
  }

  #scheduleRetry(job: Job, error: string): void {
    const attemptsAfter = job.attempts + 1;
    if (attemptsAfter >= this.#maxAttempts) {
      this.#store.fail(job, error, false, null);
    } else {
      this.#store.fail(
        job,
        error,
        true,
        this.#clock() + this.backoff(attemptsAfter),
      );
    }
  }
}
