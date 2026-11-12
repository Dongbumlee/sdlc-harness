/**
 * The worker standard's defining tests (see the sdlc-stack-profiles
 * skill): duplicate delivery applies the effect once, a poison
 * message dead-letters, and a crash mid-job recovers through the
 * claim lease. Plus the supporting guarantees: backoff scheduling,
 * the transactional outbox, and dead-letter replay. All against a
 * fake clock and a fixed random source (no sleeping, no flakiness).
 */

import fs from "node:fs";
import os from "node:os";
import path from "node:path";

import { describe, expect, it } from "vitest";

import { HANDLERS, slugify } from "../src/handlers.js";
import { JobStore, type Job } from "../src/store.js";
import {
  PermanentError,
  RetryableError,
  Worker,
  type Handler,
} from "../src/worker.js";

class FakeClock {
  now = 1000;
  readonly tick = (): number => this.now;
  advance(seconds: number): void {
    this.now += seconds;
  }
}

function setup(
  handlers: Record<string, Handler> = HANDLERS,
  options: object = {},
) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "worker-test-"));
  const clock = new FakeClock();
  const store = new JobStore(path.join(dir, "jobs.db"), clock.tick);
  const worker = new Worker(store, handlers, {
    clock: clock.tick,
    random: () => 0.5,
    ...options,
  });
  return { store, worker, clock };
}

describe("worker contract", () => {
  it("duplicate delivery applies the effect once", () => {
    const { store, worker } = setup();
    const jobId = store.enqueue("slugify", { text: "Hello World" }, "k-1");
    // The producer retries its own send with the same key: same job.
    expect(store.enqueue("slugify", { text: "Hello World" }, "k-1")).toBe(
      jobId,
    );

    expect(worker.runOnce()).toBe(true);
    expect(store.stats()["done"]).toBe(1);

    // The ack was lost, so the same job is completed a second time:
    // complete() must report the duplicate, and the effect must
    // still exist exactly once, with no second outbox row.
    const redelivered: Job = {
      id: jobId,
      idempotencyKey: "k-1",
      type: "slugify",
      payload: { text: "Hello World" },
      attempts: 0,
    };
    expect(store.complete(redelivered, "hello-world")).toBe(false);
    expect(store.countRows("effects")).toBe(1);
    expect(store.countRows("outbox")).toBe(1);
  });

  it("poison message dead-letters immediately", () => {
    const poison: Handler = () => {
      throw new PermanentError("payload.text must be a non-empty string");
    };
    const { store, worker } = setup({ slugify: poison });
    store.enqueue("slugify", { text: "" }, "poison-1");

    expect(worker.runOnce()).toBe(true);
    const stats = store.stats();
    expect(stats["dead"]).toBe(1);
    expect(stats["pending"]).toBe(0);
    expect(store.deadJobs()[0]?.idempotencyKey).toBe("poison-1");
  });

  it("unknown job type is permanent", () => {
    const { store, worker } = setup();
    store.enqueue("frobnicate", {}, "mystery-1");
    expect(worker.runOnce()).toBe(true);
    expect(store.stats()["dead"]).toBe(1);
  });

  it("crash mid-job recovers through the lease", () => {
    const { store, worker, clock } = setup();
    store.enqueue("slugify", { text: "Crash Test" }, "crash-1");

    // Worker A claims the job and dies before completing it.
    expect(store.claim("worker-a", 30)).toBeDefined();
    expect(store.claim("worker-b", 30)).toBeUndefined(); // lease still held

    // After the lease expires, worker B picks the same job up and
    // the effect lands exactly once.
    clock.advance(31);
    expect(worker.runOnce()).toBe(true);
    expect(store.stats()["done"]).toBe(1);
    expect(store.countRows("effects")).toBe(1);
  });

  it("retryable failure backs off, then succeeds", () => {
    let calls = 0;
    const flaky: Handler = (payload) => {
      calls += 1;
      if (calls < 3) {
        throw new RetryableError("downstream unavailable");
      }
      return slugify(payload);
    };
    const { store, worker, clock } = setup(
      { slugify: flaky },
      { baseDelaySeconds: 10 },
    );
    store.enqueue("slugify", { text: "Flaky Job" }, "flaky-1");

    expect(worker.runOnce()).toBe(true); // attempt 1 fails; delay = 0.5 * 20 = 10
    expect(store.stats()["pending"]).toBe(1);
    expect(worker.runOnce()).toBe(false); // not yet due: backoff is real

    clock.advance(11);
    expect(worker.runOnce()).toBe(true); // attempt 2 fails; delay = 0.5 * 40 = 20
    clock.advance(21);
    expect(worker.runOnce()).toBe(true); // attempt 3 succeeds
    expect(store.stats()["done"]).toBe(1);
  });

  it("retry budget exhaustion dead-letters", () => {
    const alwaysDown: Handler = () => {
      throw new RetryableError("still down");
    };
    const { store, worker, clock } = setup(
      { slugify: alwaysDown },
      { maxAttempts: 3 },
    );
    store.enqueue("slugify", { text: "Doomed" }, "doomed-1");
    for (let i = 0; i < 3; i += 1) {
      expect(worker.runOnce()).toBe(true);
      clock.advance(100);
    }
    expect(store.stats()["dead"]).toBe(1);
    expect(store.deadJobs()[0]?.attempts).toBe(3);
  });

  it("outbox drains once and marks", () => {
    const { store, worker } = setup();
    store.enqueue("slugify", { text: "Outbox Test" }, "ob-1");
    expect(worker.runOnce()).toBe(true);

    const received: Array<[string, Record<string, unknown>]> = [];
    expect(
      store.drainOutbox((event, payload) => received.push([event, payload])),
    ).toBe(1);
    expect(received[0]?.[0]).toBe("job.completed");
    expect(received[0]?.[1]["idempotency_key"]).toBe("ob-1");
    expect(
      store.drainOutbox((event, payload) => received.push([event, payload])),
    ).toBe(0);
    expect(received).toHaveLength(1);
  });

  it("replay restores a dead job", () => {
    const poison: Handler = () => {
      throw new PermanentError("bad");
    };
    const { store, worker } = setup({ slugify: poison });
    const jobId = store.enqueue("slugify", { text: "x" }, "replay-1");
    expect(worker.runOnce()).toBe(true);
    expect(store.stats()["dead"]).toBe(1);

    expect(store.replay(jobId)).toBe(true);
    expect(store.stats()["pending"]).toBe(1);

    const fixed = new Worker(store, HANDLERS, { clock: () => 1000 });
    expect(fixed.runOnce()).toBe(true);
    expect(store.stats()["done"]).toBe(1);
  });
});
