using System;
using System.Collections.Generic;
using System.IO;
using Microsoft.Data.Sqlite;
using Xunit;
using {{ProjectName}}Worker.Jobs;

namespace {{ProjectName}}Worker.Tests;

/// <summary>
/// The worker standard's defining tests (see the sdlc-stack-profiles
/// skill): duplicate delivery applies the effect once, a poison message
/// dead-letters, and a crash mid-job recovers through the claim lease.
/// Plus the supporting guarantees: backoff scheduling, the transactional
/// outbox, and dead-letter replay. All against a fake clock (no sleeping).
/// </summary>
public sealed class WorkerContractTests : IDisposable
{
    private readonly string _dbPath = Path.Combine(Path.GetTempPath(), Guid.NewGuid() + ".db");
    private double _now = 1000.0;

    private JobStore NewStore() => new(_dbPath, () => _now);

    private Worker NewWorker(
        JobStore store,
        IReadOnlyDictionary<string, Func<string, string>>? handlers = null,
        string workerId = "worker-1",
        int maxAttempts = 5,
        double baseDelay = 1.0) =>
        new(
            store,
            handlers ?? Handlers.All,
            workerId: workerId,
            clockSeconds: () => _now,
            rng: new Random(42),
            maxAttempts: maxAttempts,
            baseDelaySeconds: baseDelay);

    private long CountRows(string table)
    {
        using var connection = new SqliteConnection($"Data Source={_dbPath}");
        connection.Open();
        using var command = new SqliteCommand($"SELECT COUNT(*) FROM {table}", connection);
        return (long)command.ExecuteScalar()!;
    }

    [Fact]
    public void DuplicateDeliveryAppliesEffectOnce()
    {
        using var store = NewStore();
        var worker = NewWorker(store);
        var jobId = store.Enqueue("slugify", "{\"text\":\"Hello World\"}", "k-1");
        // The producer retries its own send with the same key: same job.
        Assert.Equal(jobId, store.Enqueue("slugify", "{\"text\":\"Hello World\"}", "k-1"));

        Assert.True(worker.RunOnce());
        Assert.Equal(1, store.Stats()["done"]);

        // The ack was lost, so the same job is completed a second time:
        // Complete must report the duplicate, and the effect must still
        // exist exactly once, with no second outbox row.
        var redelivered = new Job(jobId, "k-1", "slugify", "{\"text\":\"Hello World\"}", 0);
        Assert.False(store.Complete(redelivered, "hello-world"));
        Assert.Equal(1, CountRows("effects"));
        Assert.Equal(1, CountRows("outbox"));
    }

    [Fact]
    public void PoisonMessageDeadLettersImmediately()
    {
        using var store = NewStore();
        var worker = NewWorker(
            store,
            new Dictionary<string, Func<string, string>>
            {
                ["slugify"] = _ => throw new PermanentErrorException("payload.text must be a non-empty string"),
            });
        store.Enqueue("slugify", "{\"text\":\"\"}", "poison-1");

        Assert.True(worker.RunOnce());
        var stats = store.Stats();
        Assert.Equal(1, stats["dead"]);
        Assert.Equal(0, stats["pending"]);
        Assert.Equal("poison-1", store.DeadJobs()[0].IdempotencyKey);
    }

    [Fact]
    public void UnknownJobTypeIsPermanent()
    {
        using var store = NewStore();
        var worker = NewWorker(store);
        store.Enqueue("frobnicate", "{}", "mystery-1");

        Assert.True(worker.RunOnce());
        Assert.Equal(1, store.Stats()["dead"]);
    }

    [Fact]
    public void CrashMidJobRecoversThroughLease()
    {
        using var store = NewStore();
        store.Enqueue("slugify", "{\"text\":\"Crash Test\"}", "crash-1");

        // Worker A claims the job and dies before completing it.
        Assert.NotNull(store.Claim("worker-a", leaseSeconds: 30));
        Assert.Null(store.Claim("worker-b", leaseSeconds: 30)); // lease still held

        // After the lease expires, worker B picks the same job up and the
        // effect lands exactly once.
        _now += 31;
        var workerB = NewWorker(store, workerId: "worker-b");
        Assert.True(workerB.RunOnce());
        Assert.Equal(1, store.Stats()["done"]);
        Assert.Equal(1, CountRows("effects"));
    }

    [Fact]
    public void RetryableFailureBacksOffThenSucceeds()
    {
        using var store = NewStore();
        var calls = 0;
        var worker = NewWorker(
            store,
            new Dictionary<string, Func<string, string>>
            {
                ["slugify"] = payload =>
                {
                    calls++;
                    if (calls < 3)
                    {
                        throw new RetryableErrorException("downstream unavailable");
                    }

                    return Handlers.Slugify(payload);
                },
            },
            baseDelay: 10.0);
        store.Enqueue("slugify", "{\"text\":\"Flaky Job\"}", "flaky-1");

        Assert.True(worker.RunOnce()); // attempt 1 fails, retry scheduled
        Assert.Equal(1, store.Stats()["pending"]);
        Assert.False(worker.RunOnce()); // not yet due: backoff is real

        _now += 21; // past the max jittered delay for attempt 2 (<= 2 * 10)
        Assert.True(worker.RunOnce()); // attempt 2 fails, rescheduled
        _now += 41; // past attempt 3's max delay (<= 4 * 10)
        Assert.True(worker.RunOnce()); // attempt 3 succeeds
        Assert.Equal(1, store.Stats()["done"]);
    }

    [Fact]
    public void RetryBudgetExhaustionDeadLetters()
    {
        using var store = NewStore();
        var worker = NewWorker(
            store,
            new Dictionary<string, Func<string, string>>
            {
                ["slugify"] = _ => throw new RetryableErrorException("still down"),
            },
            maxAttempts: 3);
        store.Enqueue("slugify", "{\"text\":\"Doomed\"}", "doomed-1");

        for (var i = 0; i < 3; i++)
        {
            Assert.True(worker.RunOnce());
            _now += 100;
        }

        Assert.Equal(1, store.Stats()["dead"]);
        Assert.Equal(3, store.DeadJobs()[0].Attempts);
    }

    [Fact]
    public void OutboxDrainsOnceAndMarks()
    {
        using var store = NewStore();
        var worker = NewWorker(store);
        store.Enqueue("slugify", "{\"text\":\"Outbox Test\"}", "ob-1");
        Assert.True(worker.RunOnce());

        var received = new List<(string Event, string Payload)>();
        Assert.Equal(1, store.DrainOutbox((evt, payload) => received.Add((evt, payload))));
        Assert.Equal("job.completed", received[0].Event);
        Assert.Contains("ob-1", received[0].Payload);
        Assert.Equal(0, store.DrainOutbox((evt, payload) => received.Add((evt, payload))));
        Assert.Single(received);
    }

    [Fact]
    public void ReplayRestoresDeadJob()
    {
        using var store = NewStore();
        var poison = NewWorker(
            store,
            new Dictionary<string, Func<string, string>>
            {
                ["slugify"] = _ => throw new PermanentErrorException("bad"),
            });
        var jobId = store.Enqueue("slugify", "{\"text\":\"x\"}", "replay-1");
        Assert.True(poison.RunOnce());
        Assert.Equal(1, store.Stats()["dead"]);

        Assert.True(store.Replay(jobId));
        Assert.Equal(1, store.Stats()["pending"]);

        var fixedWorker = NewWorker(store); // the real handler this time
        Assert.True(fixedWorker.RunOnce());
        Assert.Equal(1, store.Stats()["done"]);
    }

    public void Dispose()
    {
        SqliteConnection.ClearAllPools();
        File.Delete(_dbPath);
    }
}
