"""The worker standard's defining tests (see the sdlc-stack-profiles
skill): duplicate delivery applies the effect once, a poison message
dead-letters, and a crash mid-job recovers through the claim lease.
Plus the supporting guarantees: backoff scheduling, the transactional
outbox, and dead-letter replay.
"""

from __future__ import annotations

import random

import pytest

from app.handlers import HANDLERS, slugify
from app.store import Job, JobStore
from app.worker import PermanentError, RetryableError, Worker


class FakeClock:
    def __init__(self, start: float = 1_000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def store(tmp_path, clock) -> JobStore:
    return JobStore(tmp_path / "jobs.db", clock=clock)


def make_worker(
    store: JobStore, clock: FakeClock, handlers=HANDLERS, **kwargs
) -> Worker:
    kwargs.setdefault("rng", random.Random(42))
    return Worker(store, handlers, clock=clock, **kwargs)


def test_duplicate_delivery_applies_effect_once(store, clock):
    worker = make_worker(store, clock)
    job_id = store.enqueue("slugify", {"text": "Hello World"}, idempotency_key="k-1")
    # The producer retries its own send with the same key: same job.
    assert (
        store.enqueue("slugify", {"text": "Hello World"}, idempotency_key="k-1")
        == job_id
    )

    assert worker.run_once() is True
    assert store.stats()["done"] == 1

    # Now simulate the redelivery the design assumes: the ack was
    # lost, so the broker delivers the same job again and it is
    # completed a second time. complete() must report the duplicate
    # and the effect must still exist exactly once, with no second
    # outbox row.
    redelivered = Job(
        id=job_id,
        idempotency_key="k-1",
        type="slugify",
        payload={"text": "Hello World"},
        attempts=0,
    )
    assert store.complete(redelivered, "hello-world") is False
    effects = store._conn.execute("SELECT COUNT(*) FROM effects").fetchone()[0]
    outbox = store._conn.execute("SELECT COUNT(*) FROM outbox").fetchone()[0]
    assert effects == 1
    assert outbox == 1


def test_poison_message_dead_letters_immediately(store, clock):
    def poison(_payload):
        raise PermanentError("payload.text must be a non-empty string")

    worker = make_worker(store, clock, handlers={"slugify": poison})
    store.enqueue("slugify", {"text": ""}, idempotency_key="poison-1")
    assert worker.run_once() is True
    stats = store.stats()
    assert stats["dead"] == 1
    assert stats["pending"] == 0
    assert store.dead_jobs()[0].idempotency_key == "poison-1"


def test_unknown_job_type_is_permanent(store, clock):
    worker = make_worker(store, clock)
    store.enqueue("frobnicate", {}, idempotency_key="mystery-1")
    assert worker.run_once() is True
    assert store.stats()["dead"] == 1


def test_crash_mid_job_recovers_through_lease(store, clock):
    store.enqueue("slugify", {"text": "Crash Test"}, idempotency_key="crash-1")

    # Worker A claims the job and dies before completing it.
    claimed = store.claim("worker-a", lease_seconds=30)
    assert claimed is not None
    assert store.claim("worker-b", lease_seconds=30) is None  # lease still held

    # After the lease expires, worker B picks the same job up and the
    # effect lands exactly once.
    clock.advance(31)
    worker_b = make_worker(store, clock, worker_id="worker-b")
    assert worker_b.run_once() is True
    assert store.stats()["done"] == 1
    assert store._conn.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 1


def test_retryable_failure_backs_off_then_succeeds(store, clock):
    calls = {"n": 0}

    def flaky(payload):
        calls["n"] += 1
        if calls["n"] < 3:
            raise RetryableError("downstream unavailable")
        return slugify(payload)

    worker = make_worker(store, clock, handlers={"slugify": flaky}, base_delay=10.0)
    store.enqueue("slugify", {"text": "Flaky Job"}, idempotency_key="flaky-1")

    assert worker.run_once() is True  # attempt 1 fails, retry scheduled
    assert store.stats()["pending"] == 1
    assert worker.run_once() is False  # not yet due: backoff is real

    clock.advance(21)  # past the max jittered delay for attempt 2 (<= 2 * 10)
    assert worker.run_once() is True  # attempt 2 fails, rescheduled
    clock.advance(41)  # past attempt 3's max delay (<= 4 * 10)
    assert worker.run_once() is True  # attempt 3 succeeds
    assert store.stats()["done"] == 1


def test_retry_budget_exhaustion_dead_letters(store, clock):
    def always_down(_payload):
        raise RetryableError("still down")

    worker = make_worker(
        store, clock, handlers={"slugify": always_down}, max_attempts=3, base_delay=1.0
    )
    store.enqueue("slugify", {"text": "Doomed"}, idempotency_key="doomed-1")
    for _ in range(3):
        assert worker.run_once() is True
        clock.advance(100)
    assert store.stats()["dead"] == 1
    assert store.dead_jobs()[0].attempts == 3


def test_outbox_drains_once_and_marks(store, clock):
    worker = make_worker(store, clock)
    store.enqueue("slugify", {"text": "Outbox Test"}, idempotency_key="ob-1")
    assert worker.run_once() is True

    received: list[tuple[str, dict]] = []
    assert store.drain_outbox(lambda e, p: received.append((e, p))) == 1
    assert received[0][0] == "job.completed"
    assert received[0][1]["idempotency_key"] == "ob-1"
    assert store.drain_outbox(lambda e, p: received.append((e, p))) == 0
    assert len(received) == 1


def test_replay_restores_dead_job(store, clock):
    def poison(_payload):
        raise PermanentError("bad")

    worker = make_worker(store, clock, handlers={"slugify": poison})
    job_id = store.enqueue("slugify", {"text": "x"}, idempotency_key="replay-1")
    assert worker.run_once() is True
    assert store.stats()["dead"] == 1

    assert store.replay(job_id) is True
    assert store.stats()["pending"] == 1

    fixed = make_worker(store, clock)  # the real handler this time
    assert fixed.run_once() is True
    assert store.stats()["done"] == 1
