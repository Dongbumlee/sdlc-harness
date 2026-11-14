"""Sample worker: correctness under redelivery.

Delivery is at-least-once, so the same job can arrive twice, a worker
can die mid-job, and a poison job can arrive at any time. The design
answers each case in the store, not in hope:

* every job carries a producer-chosen idempotency key with a UNIQUE
  constraint; the effect row is inserted in the same transaction
  that marks the job done, so a redelivery is detected and acked
  without re-applying the effect;
* events leave through a transactional outbox written in that same
  transaction, never as a side call that can be lost;
* failures are classified: permanent errors dead-letter at once,
  retryable errors retry with exponential backoff and full jitter
  until the attempt budget runs out, then dead-letter too;
* a claim is a lease, not a lock: a job whose worker died becomes
  claimable again when the lease expires;
* dead jobs are replayable from day one (``JobStore.replay``).
"""
