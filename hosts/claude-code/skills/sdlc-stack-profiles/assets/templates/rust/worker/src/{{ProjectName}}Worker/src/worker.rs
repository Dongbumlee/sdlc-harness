//! The worker loop: claim, handle, record — with classified
//! retries (exponential backoff with full jitter until the attempt
//! budget runs out, then dead-letter).
//!
//! Error classification is the handler's contract: return
//! [`JobError::Permanent`] for input that will never succeed (bad
//! payload, unknown type), and anything else — including a bare
//! error the handler did not anticipate — is treated as retryable,
//! because under at-least-once delivery retrying the unknown is
//! safer than dead-lettering it.

use std::collections::HashMap;

use serde_json::Value;

use crate::store::{Job, JobStore};

/// A job handler: returns the effect's result string.
pub type Handler = Box<dyn Fn(&Value) -> Result<String, JobError> + Send>;

/// A classified handler failure.
#[derive(Debug)]
pub enum JobError {
    /// The job can never succeed as delivered: dead-letter it now.
    Permanent(String),
    /// The job might succeed later: back off and retry it.
    Retryable(String),
}

impl std::fmt::Display for JobError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            JobError::Permanent(message) | JobError::Retryable(message) => {
                write!(f, "{message}")
            }
        }
    }
}

impl std::error::Error for JobError {}

/// The worker loop over one store and handler set.
pub struct Worker {
    store: JobStore,
    handlers: HashMap<String, Handler>,
    worker_id: String,
    clock: Box<dyn Fn() -> f64 + Send>,
    jitter: Box<dyn FnMut() -> f64 + Send>,
    max_attempts: i64,
    base_delay_seconds: f64,
    max_delay_seconds: f64,
    lease_seconds: f64,
}

/// Tunables for [`Worker::with_options`]; defaults are the standard:
/// 5 attempts, 1s base doubling to a 60s cap, 30s claim leases.
pub struct WorkerOptions {
    pub worker_id: String,
    pub clock: Box<dyn Fn() -> f64 + Send>,
    pub jitter: Box<dyn FnMut() -> f64 + Send>,
    pub max_attempts: i64,
    pub base_delay_seconds: f64,
    pub max_delay_seconds: f64,
    pub lease_seconds: f64,
}

impl Default for WorkerOptions {
    fn default() -> Self {
        Self {
            worker_id: "worker-1".to_string(),
            clock: Box::new(crate::now_seconds),
            jitter: Box::new(default_jitter()),
            max_attempts: 5,
            base_delay_seconds: 1.0,
            max_delay_seconds: 60.0,
            lease_seconds: 30.0,
        }
    }
}

/// Jitter source: a small xorshift seeded from the clock. Jitter
/// only spreads retries out — it carries no correctness weight, so
/// a standard-library source is enough and no RNG dependency is
/// taken.
fn default_jitter() -> impl FnMut() -> f64 {
    let mut state = (crate::now_seconds() * 1e9) as u64 ^ 0x9E37_79B9_7F4A_7C15;
    move || {
        state ^= state >> 12;
        state ^= state << 25;
        state ^= state >> 27;
        let value = state.wrapping_mul(0x2545_F491_4F6C_DD1D);
        (value >> 11) as f64 / (1u64 << 53) as f64
    }
}

impl Worker {
    pub fn new(store: JobStore, handlers: HashMap<String, Handler>) -> Self {
        Self::with_options(store, handlers, WorkerOptions::default())
    }

    pub fn with_options(
        store: JobStore,
        handlers: HashMap<String, Handler>,
        options: WorkerOptions,
    ) -> Self {
        Self {
            store,
            handlers,
            worker_id: options.worker_id,
            clock: options.clock,
            jitter: options.jitter,
            max_attempts: options.max_attempts,
            base_delay_seconds: options.base_delay_seconds,
            max_delay_seconds: options.max_delay_seconds,
            lease_seconds: options.lease_seconds,
        }
    }

    pub fn store(&self) -> &JobStore {
        &self.store
    }

    /// Full-jitter exponential backoff for the next attempt number.
    pub fn backoff(&mut self, attempts: i64) -> f64 {
        let capped = self
            .max_delay_seconds
            .min(self.base_delay_seconds * 2f64.powi(attempts as i32));
        (self.jitter)() * capped
    }

    /// Process one due job if there is one. Reports whether work
    /// was done.
    pub fn run_once(&mut self) -> rusqlite::Result<bool> {
        let Some(job) = self.store.claim(&self.worker_id, self.lease_seconds)? else {
            return Ok(false);
        };
        let Some(handler) = self.handlers.get(&job.job_type) else {
            self.store.fail(
                &job,
                &format!("unknown job type '{}'", job.job_type),
                false,
                0.0,
            )?;
            return Ok(true);
        };
        match handler(&job.payload) {
            Ok(result) => {
                self.store.complete(&job, &result)?;
            }
            Err(JobError::Permanent(message)) => {
                self.store.fail(&job, &message, false, 0.0)?;
            }
            Err(error) => {
                // Classified as retryable, never swallowed.
                self.schedule_retry(&job, &error.to_string())?;
            }
        }
        Ok(true)
    }

    fn schedule_retry(&mut self, job: &Job, error: &str) -> rusqlite::Result<()> {
        let attempts_after = job.attempts + 1;
        if attempts_after >= self.max_attempts {
            self.store.fail(job, error, false, 0.0)
        } else {
            let next = (self.clock)() + self.backoff(attempts_after);
            self.store.fail(job, error, true, next)
        }
    }
}
