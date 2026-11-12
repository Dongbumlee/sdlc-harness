# {{project-name}} worker

A background worker built from the java/worker template. The
sample job type (`slugify`) is a placeholder — replace it with your
own job types; the delivery guarantees around it are the template.

## The worker contract

Delivery is **at-least-once**: the same job can arrive twice, a
worker can die mid-job, and a poison job can arrive at any time.
The design answers each case in the store, not in hope:

- **Idempotent effects.** Every job carries a producer-chosen
  idempotency key with a UNIQUE constraint. The effect row is
  inserted in the *same transaction* that marks the job done, so a
  redelivery is acked without re-applying the effect — the effect
  exists exactly once.
- **Transactional outbox.** Completion events are rows written in
  that same transaction and published afterwards by
  `drainOutbox`; a crash can republish, never lose, an event.
- **Classified retries.** Handlers throw `Worker.PermanentError`
  for input that can never succeed (dead-lettered at once) and
  anything else is retryable: exponential backoff with full jitter
  until the attempt budget (5) runs out, then dead-letter too.
- **Claims are leases.** A claimed job whose lease expires — its
  worker crashed — becomes claimable again automatically.
- **Dead-letter queue with replay.** Dead jobs are rows with
  `status='dead'`; `JobStore.replay` returns one to pending with
  its budget restored. The runner logs an ALARM line whenever the
  dead depth is above zero — wire that to your paging.

The store is SQLite through the xerial JDBC driver, which makes
every one of these guarantees testable with no external services.
The schema and claim protocol map onto any transactional store in
production; the guarantees live in the protocol, not in SQLite.
Job scope is per job: a handler receives exactly one job's payload
(a `JSONObject`) and returns its result string.

## The defining tests

`WorkerContractTest` pins the contract: duplicate delivery applies
the effect once, a poison message dead-letters, a crash mid-job
recovers through the lease — plus backoff scheduling,
attempt-budget exhaustion, single-drain outbox publishing, and
dead-letter replay, all against a fake clock (no sleeping).

## Running

```bash
./mvnw package
java -jar target/{{project-name}}-worker-0.1.0.jar
```

Configuration is environment-only, prefixed with the tool name
upper-cased (`<PREFIX>_DB_PATH`, `<PREFIX>_POLL_INTERVAL`).
Shutdown is graceful: SIGTERM/SIGINT finish the current job first.

## Development

```bash
./mvnw test
./mvnw spotless:check
```
