/**
 * Runner: wire the store and handlers into a polling process.
 *
 * Configuration comes from the environment (<PREFIX>_DB_PATH and
 * friends, where the prefix is the upper-cased tool name). Shutdown
 * is graceful: SIGTERM/SIGINT stop the loop after the current job,
 * so a deploy never strands a claimed job — and if one is stranded
 * anyway, its lease expires and another worker picks it up. All
 * diagnostics go to stderr; stdout stays clean.
 */

import os from "node:os";

import { HANDLERS } from "./handlers.js";
import { JobStore } from "./store.js";
import { Worker } from "./worker.js";

const PREFIX = "{{project-name}}".toUpperCase().replaceAll("-", "_") + "_";

function env(name: string, fallback: string): string {
  return process.env[PREFIX + name] ?? fallback;
}

function log(message: string): void {
  process.stderr.write(message + "\n");
}

const store = new JobStore(env("DB_PATH", "worker.db"));
const worker = new Worker(store, HANDLERS, { workerId: os.hostname() });

let stopping = false;
process.on("SIGTERM", () => {
  stopping = true;
});
process.on("SIGINT", () => {
  stopping = true;
});

log(`worker started (db=${env("DB_PATH", "worker.db")})`);
while (!stopping) {
  const worked = worker.runOnce();
  const published = store.drainOutbox((event, payload) =>
    log(`outbox ${event} ${JSON.stringify(payload)}`),
  );
  if (published > 0) {
    log(`published ${published} outbox event(s)`);
  }
  const dead = store.stats()["dead"] ?? 0;
  if (dead > 0) {
    // The alarm hook: dead depth above zero must reach a human.
    log(`ALARM: ${dead} dead job(s) awaiting replay or triage`);
  }
  if (!worked) {
    await new Promise((resolve) =>
      setTimeout(resolve, Number(env("POLL_INTERVAL", "0.5")) * 1000),
    );
  }
}
log("worker stopped");
