package jobs_test

// The worker standard's defining tests (see the sdlc-stack-profiles
// skill): duplicate delivery applies the effect once, a poison
// message dead-letters, and a crash mid-job recovers through the
// claim lease. Plus the supporting guarantees: backoff scheduling,
// the transactional outbox, and dead-letter replay. All against a
// fake clock and a fixed random source (no sleeping, no flakiness).

import (
	"fmt"
	"path/filepath"
	"testing"

	"example.com/{{project-name}}/internal/jobs"
)

type fakeClock struct{ now float64 }

func (c *fakeClock) tick() float64 { return c.now }

func setup(t *testing.T, handlers map[string]jobs.Handler, opts jobs.Options) (*jobs.Store, *jobs.Worker, *fakeClock) {
	t.Helper()
	clock := &fakeClock{now: 1000}
	store, err := jobs.NewStore(filepath.Join(t.TempDir(), "jobs.db"), clock.tick)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = store.Close() })
	if opts.Clock == nil {
		opts.Clock = clock.tick
	}
	if opts.RandFloat == nil {
		opts.RandFloat = func() float64 { return 0.5 }
	}
	return store, jobs.NewWorker(store, handlers, opts), clock
}

func stats(t *testing.T, store *jobs.Store) map[string]int {
	t.Helper()
	s, err := store.Stats()
	if err != nil {
		t.Fatal(err)
	}
	return s
}

func TestDuplicateDeliveryAppliesEffectOnce(t *testing.T) {
	store, worker, _ := setup(t, jobs.Handlers(), jobs.Options{})
	payload := map[string]any{"text": "Hello World"}
	jobID, err := store.Enqueue("slugify", payload, "k-1")
	if err != nil {
		t.Fatal(err)
	}
	// The producer retries its own send with the same key: same job.
	again, err := store.Enqueue("slugify", payload, "k-1")
	if err != nil {
		t.Fatal(err)
	}
	if again != jobID {
		t.Fatalf("duplicate enqueue returned %d, want %d", again, jobID)
	}

	worked, err := worker.RunOnce()
	if err != nil || !worked {
		t.Fatalf("RunOnce = %v, %v", worked, err)
	}
	if got := stats(t, store)["done"]; got != 1 {
		t.Fatalf("done = %d, want 1", got)
	}

	// The ack was lost, so the same job is completed a second time:
	// Complete must report the duplicate, and the effect must still
	// exist exactly once, with no second outbox row.
	redelivered := &jobs.Job{ID: jobID, IdempotencyKey: "k-1", Type: "slugify", Payload: payload}
	applied, err := store.Complete(redelivered, "hello-world")
	if err != nil {
		t.Fatal(err)
	}
	if applied {
		t.Fatal("duplicate Complete reported the effect applied")
	}
	if n, _ := store.CountRows("effects"); n != 1 {
		t.Fatalf("effects = %d, want 1", n)
	}
	if n, _ := store.CountRows("outbox"); n != 1 {
		t.Fatalf("outbox = %d, want 1", n)
	}
}

func TestPoisonMessageDeadLettersImmediately(t *testing.T) {
	poison := func(payload map[string]any) (string, error) {
		return "", fmt.Errorf("%w: payload.text must be a non-empty string", jobs.ErrPermanent)
	}
	store, worker, _ := setup(t, map[string]jobs.Handler{"slugify": poison}, jobs.Options{})
	if _, err := store.Enqueue("slugify", map[string]any{"text": ""}, "poison-1"); err != nil {
		t.Fatal(err)
	}
	worked, err := worker.RunOnce()
	if err != nil || !worked {
		t.Fatalf("RunOnce = %v, %v", worked, err)
	}
	s := stats(t, store)
	if s["dead"] != 1 || s["pending"] != 0 {
		t.Fatalf("stats = %v, want dead=1 pending=0", s)
	}
	dead, err := store.DeadJobs()
	if err != nil || len(dead) != 1 || dead[0].IdempotencyKey != "poison-1" {
		t.Fatalf("dead jobs = %v, %v", dead, err)
	}
}

func TestUnknownJobTypeIsPermanent(t *testing.T) {
	store, worker, _ := setup(t, jobs.Handlers(), jobs.Options{})
	if _, err := store.Enqueue("frobnicate", map[string]any{}, "mystery-1"); err != nil {
		t.Fatal(err)
	}
	if _, err := worker.RunOnce(); err != nil {
		t.Fatal(err)
	}
	if got := stats(t, store)["dead"]; got != 1 {
		t.Fatalf("dead = %d, want 1", got)
	}
}

func TestCrashMidJobRecoversThroughLease(t *testing.T) {
	store, worker, clock := setup(t, jobs.Handlers(), jobs.Options{})
	if _, err := store.Enqueue("slugify", map[string]any{"text": "Crash Test"}, "crash-1"); err != nil {
		t.Fatal(err)
	}
	// Worker A claims the job and dies before completing it.
	if claimed, err := store.Claim("worker-a", 30); err != nil || claimed == nil {
		t.Fatalf("claim A = %v, %v", claimed, err)
	}
	if claimed, err := store.Claim("worker-b", 30); err != nil || claimed != nil {
		t.Fatalf("claim B during lease = %v, %v, want nil", claimed, err)
	}
	// After the lease expires, worker B picks the same job up and
	// the effect lands exactly once.
	clock.now += 31
	worked, err := worker.RunOnce()
	if err != nil || !worked {
		t.Fatalf("RunOnce = %v, %v", worked, err)
	}
	if got := stats(t, store)["done"]; got != 1 {
		t.Fatalf("done = %d, want 1", got)
	}
	if n, _ := store.CountRows("effects"); n != 1 {
		t.Fatalf("effects = %d, want 1", n)
	}
}

func TestRetryableFailureBacksOffThenSucceeds(t *testing.T) {
	calls := 0
	flaky := func(payload map[string]any) (string, error) {
		calls++
		if calls < 3 {
			return "", fmt.Errorf("%w: downstream unavailable", jobs.ErrRetryable)
		}
		return jobs.Slugify(payload)
	}
	store, worker, clock := setup(t, map[string]jobs.Handler{"slugify": flaky}, jobs.Options{BaseDelay: 10})
	if _, err := store.Enqueue("slugify", map[string]any{"text": "Flaky Job"}, "flaky-1"); err != nil {
		t.Fatal(err)
	}

	worked, err := worker.RunOnce() // attempt 1 fails; delay = 0.5 * 20 = 10
	if err != nil || !worked {
		t.Fatalf("RunOnce = %v, %v", worked, err)
	}
	if got := stats(t, store)["pending"]; got != 1 {
		t.Fatalf("pending = %d, want 1", got)
	}
	if worked, _ := worker.RunOnce(); worked { // not yet due: backoff is real
		t.Fatal("job ran before its backoff elapsed")
	}
	clock.now += 11
	if worked, err := worker.RunOnce(); err != nil || !worked { // attempt 2 fails; delay = 0.5 * 40 = 20
		t.Fatalf("RunOnce = %v, %v", worked, err)
	}
	clock.now += 21
	if worked, err := worker.RunOnce(); err != nil || !worked { // attempt 3 succeeds
		t.Fatalf("RunOnce = %v, %v", worked, err)
	}
	if got := stats(t, store)["done"]; got != 1 {
		t.Fatalf("done = %d, want 1", got)
	}
}

func TestRetryBudgetExhaustionDeadLetters(t *testing.T) {
	alwaysDown := func(payload map[string]any) (string, error) {
		return "", fmt.Errorf("%w: still down", jobs.ErrRetryable)
	}
	store, worker, clock := setup(t, map[string]jobs.Handler{"slugify": alwaysDown}, jobs.Options{MaxAttempts: 3})
	if _, err := store.Enqueue("slugify", map[string]any{"text": "Doomed"}, "doomed-1"); err != nil {
		t.Fatal(err)
	}
	for i := 0; i < 3; i++ {
		if worked, err := worker.RunOnce(); err != nil || !worked {
			t.Fatalf("RunOnce = %v, %v", worked, err)
		}
		clock.now += 100
	}
	if got := stats(t, store)["dead"]; got != 1 {
		t.Fatalf("dead = %d, want 1", got)
	}
	dead, _ := store.DeadJobs()
	if len(dead) != 1 || dead[0].Attempts != 3 {
		t.Fatalf("dead = %v, want one job with 3 attempts", dead)
	}
}

func TestOutboxDrainsOnceAndMarks(t *testing.T) {
	store, worker, _ := setup(t, jobs.Handlers(), jobs.Options{})
	if _, err := store.Enqueue("slugify", map[string]any{"text": "Outbox Test"}, "ob-1"); err != nil {
		t.Fatal(err)
	}
	if _, err := worker.RunOnce(); err != nil {
		t.Fatal(err)
	}
	var events []string
	var keys []any
	publish := func(event string, payload map[string]any) {
		events = append(events, event)
		keys = append(keys, payload["idempotency_key"])
	}
	n, err := store.DrainOutbox(publish)
	if err != nil || n != 1 {
		t.Fatalf("DrainOutbox = %d, %v", n, err)
	}
	if events[0] != "job.completed" || keys[0] != "ob-1" {
		t.Fatalf("published %v / %v", events, keys)
	}
	if n, err := store.DrainOutbox(publish); err != nil || n != 0 {
		t.Fatalf("second DrainOutbox = %d, %v, want 0", n, err)
	}
	if len(events) != 1 {
		t.Fatalf("published %d events, want 1", len(events))
	}
}

func TestReplayRestoresDeadJob(t *testing.T) {
	poison := func(payload map[string]any) (string, error) {
		return "", fmt.Errorf("%w: bad", jobs.ErrPermanent)
	}
	store, worker, clock := setup(t, map[string]jobs.Handler{"slugify": poison}, jobs.Options{})
	jobID, err := store.Enqueue("slugify", map[string]any{"text": "x"}, "replay-1")
	if err != nil {
		t.Fatal(err)
	}
	if _, err := worker.RunOnce(); err != nil {
		t.Fatal(err)
	}
	if got := stats(t, store)["dead"]; got != 1 {
		t.Fatalf("dead = %d, want 1", got)
	}
	ok, err := store.Replay(jobID)
	if err != nil || !ok {
		t.Fatalf("Replay = %v, %v", ok, err)
	}
	if got := stats(t, store)["pending"]; got != 1 {
		t.Fatalf("pending = %d, want 1", got)
	}
	fixed := jobs.NewWorker(store, jobs.Handlers(), jobs.Options{Clock: clock.tick})
	if worked, err := fixed.RunOnce(); err != nil || !worked {
		t.Fatalf("RunOnce = %v, %v", worked, err)
	}
	if got := stats(t, store)["done"]; got != 1 {
		t.Fatalf("done = %d, want 1", got)
	}
}
