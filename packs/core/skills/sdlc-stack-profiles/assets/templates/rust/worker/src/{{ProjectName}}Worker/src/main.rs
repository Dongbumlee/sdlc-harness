//! Runner: wire the store and handlers into a polling process.
//!
//! Configuration comes from the environment (<PREFIX>_DB_PATH and
//! friends, where the prefix is the upper-cased tool name).
//! Shutdown is graceful: SIGTERM/SIGINT stop the loop after the
//! current job, so a deploy never strands a claimed job — and if
//! one is stranded anyway, its lease expires and another worker
//! picks it up. All diagnostics go to stderr; stdout stays clean.

use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};
use std::time::Duration;

use {{CrateName}}_worker::handlers::handlers;
use {{CrateName}}_worker::store::JobStore;
use {{CrateName}}_worker::worker::{Worker, WorkerOptions};

static STOPPING: std::sync::LazyLock<Arc<AtomicBool>> =
    std::sync::LazyLock::new(|| Arc::new(AtomicBool::new(false)));

fn prefix() -> String {
    "{{project-name}}".to_uppercase().replace('-', "_") + "_"
}

fn env(name: &str, fallback: &str) -> String {
    std::env::var(format!("{}{name}", prefix())).unwrap_or_else(|_| fallback.to_string())
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    signal_hook::flag::register(signal_hook::consts::SIGTERM, STOPPING.clone())?;
    signal_hook::flag::register(signal_hook::consts::SIGINT, STOPPING.clone())?;

    let db_path = env("DB_PATH", "worker.db");
    let store = JobStore::open(&db_path)?;
    // The worker id only labels claims; container runtimes set
    // HOSTNAME, and anything unique per process is enough.
    let options = WorkerOptions {
        worker_id: std::env::var("HOSTNAME").unwrap_or_else(|_| "worker-1".to_string()),
        ..WorkerOptions::default()
    };
    let mut worker = Worker::with_options(store, handlers(), options);
    let poll = Duration::from_secs_f64(env("POLL_INTERVAL", "0.5").parse().unwrap_or(0.5));

    eprintln!("worker started (db={db_path})");
    while !STOPPING.load(Ordering::Relaxed) {
        let worked = worker.run_once()?;
        let published = worker.store().drain_outbox(&mut |event, payload| {
            eprintln!("outbox {event} {payload}");
        })?;
        if published > 0 {
            eprintln!("published {published} outbox event(s)");
        }
        let dead = worker.store().stats()?.get("dead").copied().unwrap_or(0);
        if dead > 0 {
            // The alarm hook: dead depth above zero must reach a human.
            eprintln!("ALARM: {dead} dead job(s) awaiting replay or triage");
        }
        if !worked {
            std::thread::sleep(poll);
        }
    }
    eprintln!("worker stopped");
    Ok(())
}
