package jobs

import (
	"errors"
	"math"
	"math/rand/v2"
)

// A Handler returns the effect's result string.
type Handler func(payload map[string]any) (string, error)

// PermanentError marks a job that can never succeed as delivered:
// dead-letter it now. Handlers return an error wrapping this type
// for permanent failures.
var ErrPermanent = errors.New("permanent failure")

// RetryableError marks a failure that might succeed later. Any
// error NOT wrapping ErrPermanent is treated as retryable, because
// under at-least-once delivery retrying the unknown is safer than
// dead-lettering it.
var ErrRetryable = errors.New("retryable failure")

// Worker is the loop: claim, handle, record — with classified
// retries (exponential backoff with full jitter until the attempt
// budget runs out, then dead-letter).
type Worker struct {
	store        *Store
	handlers     map[string]Handler
	workerID     string
	clock        Clock
	randFloat    func() float64
	maxAttempts  int
	baseDelay    float64
	maxDelay     float64
	leaseSeconds float64
}

// Options tunes a Worker. Zero values get the standard defaults:
// 5 attempts, 1s base doubling to a 60s cap, 30s claim leases.
type Options struct {
	WorkerID     string
	Clock        Clock
	RandFloat    func() float64
	MaxAttempts  int
	BaseDelay    float64
	MaxDelay     float64
	LeaseSeconds float64
}

// NewWorker wires a store and handler set into a worker.
func NewWorker(store *Store, handlers map[string]Handler, opts Options) *Worker {
	w := &Worker{
		store: store, handlers: handlers, workerID: opts.WorkerID,
		clock: opts.Clock, randFloat: opts.RandFloat,
		maxAttempts: opts.MaxAttempts, baseDelay: opts.BaseDelay,
		maxDelay: opts.MaxDelay, leaseSeconds: opts.LeaseSeconds,
	}
	if w.workerID == "" {
		w.workerID = "worker-1"
	}
	if w.clock == nil {
		w.clock = store.clock
	}
	if w.randFloat == nil {
		w.randFloat = rand.Float64
	}
	if w.maxAttempts == 0 {
		w.maxAttempts = 5
	}
	if w.baseDelay == 0 {
		w.baseDelay = 1
	}
	if w.maxDelay == 0 {
		w.maxDelay = 60
	}
	if w.leaseSeconds == 0 {
		w.leaseSeconds = 30
	}
	return w
}

// Backoff returns the full-jitter delay before the next attempt.
func (w *Worker) Backoff(attempts int) float64 {
	capped := math.Min(w.maxDelay, w.baseDelay*math.Pow(2, float64(attempts)))
	return w.randFloat() * capped
}

// RunOnce processes one due job if there is one and reports
// whether work was done.
func (w *Worker) RunOnce() (bool, error) {
	job, err := w.store.Claim(w.workerID, w.leaseSeconds)
	if err != nil {
		return false, err
	}
	if job == nil {
		return false, nil
	}
	handler, ok := w.handlers[job.Type]
	if !ok {
		return true, w.store.Fail(job, "unknown job type", false, 0)
	}
	result, err := handler(job.Payload)
	if err == nil {
		_, err := w.store.Complete(job, result)
		return true, err
	}
	if errors.Is(err, ErrPermanent) {
		return true, w.store.Fail(job, err.Error(), false, 0)
	}
	// Classified as retryable, never swallowed.
	if attemptsAfter := job.Attempts + 1; attemptsAfter >= w.maxAttempts {
		return true, w.store.Fail(job, err.Error(), false, 0)
	} else {
		return true, w.store.Fail(job, err.Error(), true, w.clock()+w.Backoff(attemptsAfter))
	}
}
