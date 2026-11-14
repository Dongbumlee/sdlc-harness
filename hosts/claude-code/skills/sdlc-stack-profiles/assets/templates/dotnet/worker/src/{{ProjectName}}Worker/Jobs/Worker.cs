using System;
using System.Collections.Generic;

namespace {{ProjectName}}Worker.Jobs;

/// <summary>The job can never succeed as delivered: dead-letter it now.</summary>
public sealed class PermanentErrorException(string message) : Exception(message);

/// <summary>The job might succeed later: back off and retry it.</summary>
public sealed class RetryableErrorException(string message) : Exception(message);

/// <summary>
/// The worker loop: claim, handle, record — with classified retries.
///
/// Error classification is the handler's contract: throw
/// <see cref="PermanentErrorException"/> for input that will never succeed
/// (bad payload, unknown type), and anything else — including a bare
/// exception the handler did not anticipate — is treated as retryable,
/// because under at-least-once delivery retrying the unknown is safer than
/// dead-lettering it. Retryable failures back off exponentially with full
/// jitter and dead-letter when the attempt budget runs out.
/// </summary>
public sealed class Worker
{
    private readonly JobStore _store;
    private readonly IReadOnlyDictionary<string, Func<string, string>> _handlers;
    private readonly string _workerId;
    private readonly Func<double> _clockSeconds;
    private readonly Random _rng;
    private readonly int _maxAttempts;
    private readonly double _baseDelaySeconds;
    private readonly double _maxDelaySeconds;
    private readonly double _leaseSeconds;

    public Worker(
        JobStore store,
        IReadOnlyDictionary<string, Func<string, string>> handlers,
        string workerId = "worker-1",
        Func<double>? clockSeconds = null,
        Random? rng = null,
        int maxAttempts = 5,
        double baseDelaySeconds = 1.0,
        double maxDelaySeconds = 60.0,
        double leaseSeconds = 30.0)
    {
        _store = store;
        _handlers = handlers;
        _workerId = workerId;
        _clockSeconds = clockSeconds ?? (() => DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() / 1000.0);
        _rng = rng ?? new Random();
        _maxAttempts = maxAttempts;
        _baseDelaySeconds = baseDelaySeconds;
        _maxDelaySeconds = maxDelaySeconds;
        _leaseSeconds = leaseSeconds;
    }

    /// <summary>Full-jitter exponential backoff for the next attempt number.</summary>
    public double Backoff(int attempts)
    {
        var capped = Math.Min(_maxDelaySeconds, _baseDelaySeconds * Math.Pow(2, attempts));
        return _rng.NextDouble() * capped;
    }

    /// <summary>Process one due job if there is one. Returns true when work was done.</summary>
    public bool RunOnce()
    {
        var job = _store.Claim(_workerId, _leaseSeconds);
        if (job is null)
        {
            return false;
        }

        if (!_handlers.TryGetValue(job.Type, out var handler))
        {
            _store.Fail(job, $"unknown job type '{job.Type}'", retryable: false, nextAttemptAt: null);
            return true;
        }

        try
        {
            var result = handler(job.PayloadJson);
            _store.Complete(job, result);
        }
        catch (PermanentErrorException ex)
        {
            _store.Fail(job, ex.Message, retryable: false, nextAttemptAt: null);
        }
        catch (Exception ex)
        {
            // Classified as retryable, never swallowed.
            ScheduleRetry(job, ex.Message);
        }

        return true;
    }

    private void ScheduleRetry(Job job, string error)
    {
        var attemptsAfter = job.Attempts + 1;
        if (attemptsAfter >= _maxAttempts)
        {
            _store.Fail(job, error, retryable: false, nextAttemptAt: null);
        }
        else
        {
            _store.Fail(job, error, retryable: true, nextAttemptAt: _clockSeconds() + Backoff(attemptsAfter));
        }
    }
}
