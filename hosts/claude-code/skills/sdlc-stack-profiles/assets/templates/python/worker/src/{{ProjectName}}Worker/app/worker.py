"""The worker loop: claim, handle, record — with classified retries.

Error classification is the handler's contract: raise
:class:`PermanentError` for input that will never succeed (bad
payload, unknown type), and anything else — including a bare
exception the handler did not anticipate — is treated as retryable,
because under at-least-once delivery retrying the unknown is safer
than dead-lettering it. Retryable failures back off exponentially
with full jitter and dead-letter when the attempt budget runs out.
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable

from .store import Job, JobStore

Handler = Callable[[dict], str]


class PermanentError(Exception):
    """The job can never succeed as delivered: dead-letter it now."""


class RetryableError(Exception):
    """The job might succeed later: back off and retry it."""


class Worker:
    def __init__(
        self,
        store: JobStore,
        handlers: dict[str, Handler],
        *,
        worker_id: str = "worker-1",
        clock: Callable[[], float] = time.time,
        rng: random.Random | None = None,
        max_attempts: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        lease_seconds: float = 30.0,
    ) -> None:
        self._store = store
        self._handlers = handlers
        self._worker_id = worker_id
        self._clock = clock
        self._rng = rng if rng is not None else random.Random()
        self._max_attempts = max_attempts
        self._base_delay = base_delay
        self._max_delay = max_delay
        self._lease_seconds = lease_seconds

    def backoff(self, attempts: int) -> float:
        """Full-jitter exponential backoff for the next attempt number."""
        capped = min(self._max_delay, self._base_delay * (2**attempts))
        return self._rng.uniform(0, capped)

    def run_once(self) -> bool:
        """Process one due job if there is one. Returns True when work was done."""
        job = self._store.claim(self._worker_id, self._lease_seconds)
        if job is None:
            return False
        handler = self._handlers.get(job.type)
        if handler is None:
            self._store.fail(
                job,
                f"unknown job type '{job.type}'",
                retryable=False,
                next_attempt_at=None,
            )
            return True
        try:
            result = handler(job.payload)
        except PermanentError as exc:
            self._store.fail(job, str(exc), retryable=False, next_attempt_at=None)
        except Exception as exc:  # classified as retryable, never swallowed
            self._schedule_retry(job, str(exc))
        else:
            self._store.complete(job, result)
        return True

    def _schedule_retry(self, job: Job, error: str) -> None:
        attempts_after = job.attempts + 1
        if attempts_after >= self._max_attempts:
            self._store.fail(job, error, retryable=False, next_attempt_at=None)
        else:
            self._store.fail(
                job,
                error,
                retryable=True,
                next_attempt_at=self._clock() + self.backoff(attempts_after),
            )

    def run_forever(self, stop: Callable[[], bool], poll_interval: float = 0.5) -> None:
        """Poll until ``stop`` says so; drain-checks stay the caller's job."""
        while not stop():
            if not self.run_once():
                time.sleep(poll_interval)
