package com.example.{{PackageName}}.worker;

import java.util.Map;
import org.json.JSONObject;

/**
 * Sample handlers. Replace with your own job types; the contract is what matters: return the
 * effect's result string, throw {@link Worker.PermanentError} for payloads that can never succeed,
 * and let everything else surface as retryable.
 */
public final class Handlers {

  private Handlers() {}

  /**
   * Turn payload.text into a slug — the sample job's effect. Lowercase, letters and digits kept,
   * every other run of characters becomes one hyphen, leading/trailing hyphens trimmed — the same
   * sample semantics as the other bundled templates.
   */
  public static String slugify(JSONObject payload) {
    var text = payload.optString("text", "");
    if (text.isBlank()) {
      throw new Worker.PermanentError("payload.text must be a non-empty string");
    }
    var slug = new StringBuilder();
    var lastHyphen = true; // trims leading separators
    for (var c : text.toLowerCase().toCharArray()) {
      if (Character.isLetterOrDigit(c)) {
        slug.append(c);
        lastHyphen = false;
      } else if (!lastHyphen) {
        slug.append('-');
        lastHyphen = true;
      }
    }
    return slug.toString().replaceAll("-+$", "");
  }

  public static final Map<String, Worker.Handler> ALL = Map.of("slugify", Handlers::slugify);
}
