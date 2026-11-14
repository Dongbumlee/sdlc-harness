using System;
using System.Runtime.InteropServices;
using System.Threading;
using {{ProjectName}}Worker.Jobs;

namespace {{ProjectName}}Worker;

/// <summary>
/// Runner: wire the store and handlers into a polling process.
///
/// Configuration comes from the environment (&lt;PREFIX&gt;_DB_PATH and
/// friends, where the prefix is the upper-cased tool name). Shutdown is
/// graceful: SIGTERM/SIGINT stop the loop after the current job, so a
/// deploy never strands a claimed job — and if one is stranded anyway, its
/// lease expires and another worker picks it up. All diagnostics go to
/// stderr; stdout stays clean.
/// </summary>
public static class Program
{
    private static readonly string Prefix = "{{project-name}}".ToUpperInvariant().Replace('-', '_') + "_";

    public static void Main()
    {
        var dbPath = Env("DB_PATH", "worker.db");
        using var store = new JobStore(dbPath);
        var worker = new Worker(store, Handlers.All, workerId: Environment.MachineName);
        using var stopping = new CancellationTokenSource();
        using var sigterm = PosixSignalRegistration.Create(PosixSignal.SIGTERM, _ => stopping.Cancel());
        using var sigint = PosixSignalRegistration.Create(PosixSignal.SIGINT, _ => stopping.Cancel());

        Log($"worker started (db={dbPath})");
        while (!stopping.IsCancellationRequested)
        {
            var worked = worker.RunOnce();
            var published = store.DrainOutbox((evt, payload) => Log($"outbox {evt} {payload}"));
            if (published > 0)
            {
                Log($"published {published} outbox event(s)");
            }

            if (store.Stats()["dead"] > 0)
            {
                // The alarm hook: dead depth above zero must reach a human.
                Log($"ALARM: {store.Stats()["dead"]} dead job(s) awaiting replay or triage");
            }

            if (!worked)
            {
                var pollSeconds = double.Parse(
                    Env("POLL_INTERVAL", "0.5"), System.Globalization.CultureInfo.InvariantCulture);
                stopping.Token.WaitHandle.WaitOne(TimeSpan.FromSeconds(pollSeconds));
            }
        }

        Log("worker stopped");
    }

    private static string Env(string name, string fallback) =>
        Environment.GetEnvironmentVariable(Prefix + name) ?? fallback;

    private static void Log(string message) => Console.Error.WriteLine(message);
}
