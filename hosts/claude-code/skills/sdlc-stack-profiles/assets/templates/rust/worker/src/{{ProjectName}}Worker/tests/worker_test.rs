//! The worker standard's defining tests (see the
//! sdlc-stack-profiles skill): duplicate delivery applies the
//! effect once, a poison message dead-letters, and a crash mid-job
//! recovers through the claim lease. Plus the supporting
//! guarantees: backoff scheduling, the transactional outbox, and
//! dead-letter replay. All against a fake clock and a fixed jitter
//! source (no sleeping, no flakiness).

use std::collections::HashMap;
use std::path::PathBuf;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, Mutex};

use {{CrateName}}_worker::handlers::{handlers, slugify};
use {{CrateName}}_worker::store::{Job, JobStore};
use {{CrateName}}_worker::worker::{Handler, JobError, Worker, WorkerOptions};
use serde_json::{Value, json};

type SharedClock = Arc<Mutex<f64>>;

static COUNTER: AtomicU64 = AtomicU64::new(0);

fn fake_clock() -> (SharedClock, Box<dyn Fn() -> f64 + Send>) {
    let now: SharedClock = Arc::new(Mutex::new(1000.0));
    let tick = now.clone();
    (now, Box::new(move || *tick.lock().unwrap()))
}

fn store_on(path: &std::path::Path, now: &SharedClock) -> JobStore {
    let tick = now.clone();
    JobStore::with_clock(
        path.to_str().unwrap(),
        Box::new(move || *tick.lock().unwrap()),
    )
    .unwrap()
}

fn setup(
    handlers_map: HashMap<String, Handler>,
    base_delay: f64,
    max_attempts: i64,
) -> (Worker, SharedClock, PathBuf) {
    let (now, clock) = fake_clock();
    let unique = COUNTER.fetch_add(1, Ordering::Relaxed);
    let path = std::env::temp_dir().join(format!("worker-test-{}-{unique}.db", std::process::id()));
    let store = store_on(&path, &now);
    let options = WorkerOptions {
        clock,
        jitter: Box::new(|| 0.5),
        max_attempts,
        base_delay_seconds: base_delay,
        ..WorkerOptions::default()
    };
    (
        Worker::with_options(store, handlers_map, options),
        now,
        path,
    )
}

fn advance(now: &SharedClock, seconds: f64) {
    *now.lock().unwrap() += seconds;
}

fn stat(worker: &Worker, key: &str) -> i64 {
    worker
        .store()
        .stats()
        .unwrap()
        .get(key)
        .copied()
        .unwrap_or(-1)
}

#[test]
fn duplicate_delivery_applies_effect_once() {
    let (mut worker, _now, _path) = setup(handlers(), 1.0, 5);
    let job_id = {
        let store = worker.store();
        let job_id = store
            .enqueue("slugify", &json!({"text": "Hello World"}), "k-1")
            .unwrap();
        // The producer retries its own send with the same key: same job.
        assert_eq!(
            store
                .enqueue("slugify", &json!({"text": "Hello World"}), "k-1")
                .unwrap(),
            job_id
        );
        job_id
    };

    assert!(worker.run_once().unwrap());
    assert_eq!(stat(&worker, "done"), 1);
    let store = worker.store();

    // The ack was lost, so the same job is completed a second time:
    // complete() must report the duplicate, and the effect must
    // still exist exactly once, with no second outbox row.
    let redelivered = Job {
        id: job_id,
        idempotency_key: "k-1".to_string(),
        job_type: "slugify".to_string(),
        payload: json!({"text": "Hello World"}),
        attempts: 0,
    };
    assert!(!store.complete(&redelivered, "hello-world").unwrap());
    assert_eq!(store.count_rows("effects").unwrap(), 1);
    assert_eq!(store.count_rows("outbox").unwrap(), 1);
}

#[test]
fn poison_message_dead_letters_immediately() {
    let mut poisoned: HashMap<String, Handler> = HashMap::new();
    poisoned.insert(
        "slugify".to_string(),
        Box::new(|_payload: &Value| {
            Err(JobError::Permanent(
                "payload.text must be a non-empty string".to_string(),
            ))
        }),
    );
    let (mut worker, _now, _path) = setup(poisoned, 1.0, 5);
    worker
        .store()
        .enqueue("slugify", &json!({"text": ""}), "poison-1")
        .unwrap();

    assert!(worker.run_once().unwrap());
    assert_eq!(stat(&worker, "dead"), 1);
    assert_eq!(stat(&worker, "pending"), 0);
    assert_eq!(
        worker.store().dead_jobs().unwrap()[0].idempotency_key,
        "poison-1"
    );
}

#[test]
fn unknown_job_type_is_permanent() {
    let (mut worker, _now, _path) = setup(handlers(), 1.0, 5);
    worker
        .store()
        .enqueue("frobnicate", &json!({}), "mystery-1")
        .unwrap();
    assert!(worker.run_once().unwrap());
    assert_eq!(stat(&worker, "dead"), 1);
}

#[test]
fn crash_mid_job_recovers_through_lease() {
    let (mut worker, now, _path) = setup(handlers(), 1.0, 5);
    {
        let store = worker.store();
        store
            .enqueue("slugify", &json!({"text": "Crash Test"}), "crash-1")
            .unwrap();

        // Worker A claims the job and dies before completing it.
        assert!(store.claim("worker-a", 30.0).unwrap().is_some());
        assert!(store.claim("worker-b", 30.0).unwrap().is_none()); // lease held
    }

    // After the lease expires, worker B picks the same job up and
    // the effect lands exactly once.
    advance(&now, 31.0);
    assert!(worker.run_once().unwrap());
    assert_eq!(stat(&worker, "done"), 1);
    assert_eq!(worker.store().count_rows("effects").unwrap(), 1);
}

#[test]
fn retryable_failure_backs_off_then_succeeds() {
    let calls = Arc::new(Mutex::new(0i64));
    let mut flaky_map: HashMap<String, Handler> = HashMap::new();
    let counter = calls.clone();
    flaky_map.insert(
        "slugify".to_string(),
        Box::new(move |payload: &Value| {
            let mut n = counter.lock().unwrap();
            *n += 1;
            if *n < 3 {
                return Err(JobError::Retryable("downstream unavailable".to_string()));
            }
            slugify(payload)
        }),
    );
    let (mut worker, now, _path) = setup(flaky_map, 10.0, 5);
    worker
        .store()
        .enqueue("slugify", &json!({"text": "Flaky Job"}), "flaky-1")
        .unwrap();

    assert!(worker.run_once().unwrap()); // attempt 1 fails; delay = 0.5 * 20 = 10
    assert_eq!(stat(&worker, "pending"), 1);
    assert!(!worker.run_once().unwrap()); // not yet due: backoff is real

    advance(&now, 11.0);
    assert!(worker.run_once().unwrap()); // attempt 2 fails; delay = 0.5 * 40 = 20
    advance(&now, 21.0);
    assert!(worker.run_once().unwrap()); // attempt 3 succeeds
    assert_eq!(stat(&worker, "done"), 1);
}

#[test]
fn retry_budget_exhaustion_dead_letters() {
    let mut down: HashMap<String, Handler> = HashMap::new();
    down.insert(
        "slugify".to_string(),
        Box::new(|_payload: &Value| Err(JobError::Retryable("still down".to_string()))),
    );
    let (mut worker, now, _path) = setup(down, 1.0, 3);
    worker
        .store()
        .enqueue("slugify", &json!({"text": "Doomed"}), "doomed-1")
        .unwrap();
    for _ in 0..3 {
        assert!(worker.run_once().unwrap());
        advance(&now, 100.0);
    }
    assert_eq!(stat(&worker, "dead"), 1);
    assert_eq!(worker.store().dead_jobs().unwrap()[0].attempts, 3);
}

#[test]
fn outbox_drains_once_and_marks() {
    let (mut worker, _now, _path) = setup(handlers(), 1.0, 5);
    worker
        .store()
        .enqueue("slugify", &json!({"text": "Outbox Test"}), "ob-1")
        .unwrap();
    assert!(worker.run_once().unwrap());

    let mut received: Vec<(String, Value)> = Vec::new();
    let n = worker
        .store()
        .drain_outbox(&mut |event, payload| received.push((event.to_string(), payload.clone())))
        .unwrap();
    assert_eq!(n, 1);
    assert_eq!(received[0].0, "job.completed");
    assert_eq!(received[0].1["idempotency_key"], json!("ob-1"));
    let n = worker
        .store()
        .drain_outbox(&mut |event, payload| received.push((event.to_string(), payload.clone())))
        .unwrap();
    assert_eq!(n, 0);
    assert_eq!(received.len(), 1);
}

#[test]
fn replay_restores_dead_job() {
    let mut poisoned: HashMap<String, Handler> = HashMap::new();
    poisoned.insert(
        "slugify".to_string(),
        Box::new(|_payload: &Value| Err(JobError::Permanent("bad".to_string()))),
    );
    let (mut worker, now, path) = setup(poisoned, 1.0, 5);
    let job_id = worker
        .store()
        .enqueue("slugify", &json!({"text": "x"}), "replay-1")
        .unwrap();
    assert!(worker.run_once().unwrap());
    assert_eq!(stat(&worker, "dead"), 1);

    assert!(worker.store().replay(job_id).unwrap());
    assert_eq!(stat(&worker, "pending"), 1);

    // A second worker over the same database file, with the fixed
    // handler set this time, completes the replayed job.
    let (_shared, clock) = fake_clock_at(&now);
    let options = WorkerOptions {
        clock,
        jitter: Box::new(|| 0.5),
        ..WorkerOptions::default()
    };
    let mut fixed = Worker::with_options(store_on(&path, &now), handlers(), options);
    assert!(fixed.run_once().unwrap());
    assert_eq!(fixed.store().stats().unwrap()["done"], 1);
}

fn fake_clock_at(now: &SharedClock) -> ((), Box<dyn Fn() -> f64 + Send>) {
    let tick = now.clone();
    ((), Box::new(move || *tick.lock().unwrap()))
}
