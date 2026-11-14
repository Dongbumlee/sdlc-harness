package com.example.{{PackageName}}.worker;

import java.net.InetAddress;
import java.net.UnknownHostException;

/**
 * Runner: wire the store and handlers into a polling process.
 *
 * <p>Configuration comes from the environment (&lt;PREFIX&gt;_DB_PATH and friends, where the
 * prefix is the upper-cased tool name). Shutdown is graceful: SIGTERM/SIGINT stop the loop after
 * the current job, so a deploy never strands a claimed job — and if one is stranded anyway, its
 * lease expires and another worker picks it up. All diagnostics go to stderr; stdout stays clean.
 */
public final class Main {

  private static final String PREFIX =
      "{{project-name}}".toUpperCase().replace('-', '_') + "_";

  private static volatile boolean stopping = false;

  private Main() {}

  public static void main(String[] args) throws Exception {
    var dbPath = env("DB_PATH", "worker.db");
    try (var store = new JobStore(dbPath)) {
      var worker =
          new Worker(
              store,
              Handlers.ALL,
              hostname(),
              () -> System.currentTimeMillis() / 1000.0,
              new java.util.Random(),
              5,
              1.0,
              60.0,
              30.0);
      // SIGTERM/SIGINT run shutdown hooks: set the flag and let the
      // loop finish the current job before the JVM exits.
      Runtime.getRuntime().addShutdownHook(new Thread(() -> stopping = true));

      log("worker started (db=" + dbPath + ")");
      while (!stopping) {
        var worked = worker.runOnce();
        var published =
            store.drainOutbox((event, payload) -> log("outbox " + event + " " + payload));
        if (published > 0) {
          log("published " + published + " outbox event(s)");
        }
        var dead = store.stats().getOrDefault("dead", 0L);
        if (dead > 0) {
          // The alarm hook: dead depth above zero must reach a human.
          log("ALARM: " + dead + " dead job(s) awaiting replay or triage");
        }
        if (!worked) {
          Thread.sleep((long) (Double.parseDouble(env("POLL_INTERVAL", "0.5")) * 1000));
        }
      }
      log("worker stopped");
    }
  }

  private static String env(String name, String fallback) {
    var value = System.getenv(PREFIX + name);
    return value != null ? value : fallback;
  }

  private static String hostname() {
    try {
      return InetAddress.getLocalHost().getHostName();
    } catch (UnknownHostException e) {
      return "worker-1";
    }
  }

  private static void log(String message) {
    System.err.println(message);
  }
}
