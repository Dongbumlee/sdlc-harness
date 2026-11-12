"""Runner: wire the store and handlers into a polling process.

Configuration comes from the environment (<PREFIX>_DB_PATH and
friends, where the prefix is the upper-cased tool name). Shutdown is
graceful: SIGTERM/SIGINT stop the loop after the current job, so a
deploy never strands a claimed job — and if one is stranded anyway,
its lease expires and another worker picks it up.
"""

from __future__ import annotations

import logging
import os
import signal
import socket
import time

from .handlers import HANDLERS
from .store import JobStore
from .worker import Worker

log = logging.getLogger("{{project-name}}")

_PREFIX = "{{project-name}}".upper().replace("-", "_") + "_"


def _env(name: str, default: str) -> str:
    return os.environ.get(_PREFIX + name, default)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    store = JobStore(_env("DB_PATH", "worker.db"))
    worker = Worker(store, HANDLERS, worker_id=socket.gethostname())
    stopping = False

    def _stop(_signum, _frame):  # noqa: ANN001 — signal handler shape
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    log.info("worker started (db=%s)", _env("DB_PATH", "worker.db"))
    while not stopping:
        worked = worker.run_once()
        published = store.drain_outbox(
            lambda event, payload: log.info("outbox %s %s", event, payload)
        )
        if published:
            log.info("published %d outbox event(s)", published)
        dead = store.stats()["dead"]
        if dead > 0:
            # The alarm hook: dead depth above zero must reach a human.
            log.warning("ALARM: %d dead job(s) awaiting replay or triage", dead)
        if not worked:
            time.sleep(float(_env("POLL_INTERVAL", "0.5")))
    log.info("worker stopped")


if __name__ == "__main__":
    main()
