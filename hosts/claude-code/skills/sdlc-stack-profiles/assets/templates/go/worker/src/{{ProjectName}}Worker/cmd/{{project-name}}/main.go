// Runner: wire the store and handlers into a polling process.
//
// Configuration comes from the environment (<PREFIX>_DB_PATH and
// friends, where the prefix is the upper-cased tool name). Shutdown
// is graceful: SIGTERM/SIGINT stop the loop after the current job,
// so a deploy never strands a claimed job — and if one is stranded
// anyway, its lease expires and another worker picks it up. All
// diagnostics go to stderr; stdout stays clean.
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"syscall"
	"time"

	"example.com/{{project-name}}/internal/jobs"
)

var prefix = strings.ReplaceAll(strings.ToUpper("{{project-name}}"), "-", "_") + "_"

func env(name, fallback string) string {
	if value, ok := os.LookupEnv(prefix + name); ok {
		return value
	}
	return fallback
}

func logf(format string, args ...any) {
	_, _ = fmt.Fprintf(os.Stderr, format+"\n", args...)
}

func main() {
	clock := func() float64 { return float64(time.Now().UnixNano()) / 1e9 }
	dbPath := env("DB_PATH", "worker.db")
	store, err := jobs.NewStore(dbPath, clock)
	if err != nil {
		logf("cannot open job store: %v", err)
		os.Exit(1)
	}
	defer func() { _ = store.Close() }()

	hostname, err := os.Hostname()
	if err != nil {
		hostname = "worker-1"
	}
	worker := jobs.NewWorker(store, jobs.Handlers(), jobs.Options{WorkerID: hostname, Clock: clock})

	stop := make(chan os.Signal, 1)
	signal.Notify(stop, syscall.SIGTERM, syscall.SIGINT)

	poll := 500 * time.Millisecond
	if raw, err := strconv.ParseFloat(env("POLL_INTERVAL", "0.5"), 64); err == nil {
		poll = time.Duration(raw * float64(time.Second))
	}

	logf("worker started (db=%s)", dbPath)
loop:
	for {
		worked, err := worker.RunOnce()
		if err != nil {
			logf("job processing error: %v", err)
		}
		published, err := store.DrainOutbox(func(event string, payload map[string]any) {
			raw, _ := json.Marshal(payload)
			logf("outbox %s %s", event, raw)
		})
		if err == nil && published > 0 {
			logf("published %d outbox event(s)", published)
		}
		if stats, err := store.Stats(); err == nil && stats["dead"] > 0 {
			// The alarm hook: dead depth above zero must reach a human.
			logf("ALARM: %d dead job(s) awaiting replay or triage", stats["dead"])
		}
		if !worked {
			select {
			case <-stop:
				break loop
			case <-time.After(poll):
			}
		} else {
			select {
			case <-stop:
				break loop
			default:
			}
		}
	}
	logf("worker stopped")
}
