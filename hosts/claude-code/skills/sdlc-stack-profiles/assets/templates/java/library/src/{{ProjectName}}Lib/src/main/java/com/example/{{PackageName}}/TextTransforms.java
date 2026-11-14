package com.example.{{PackageName}};

import java.text.Normalizer;
import java.util.Locale;

/**
 * Text helpers published by {{ProjectName}}Lib. This class is the library's public surface: everything a
 * consumer may rely on is a public member of a public class in this package, and CI diffs the
 * compiled surface against the last release (japicmp) so an accidental removal or signature change
 * fails the build instead of reaching consumers.
 */
public final class TextTransforms {

  private TextTransforms() {}

  /**
   * Returns a URL-safe slug for {@code text}: accents are folded to their ASCII base letters and
   * every run of remaining non-alphanumeric characters becomes one hyphen.
   *
   * @param text the text to slugify
   * @return the slug; empty when nothing alphanumeric remains
   */
  public static String slugify(String text) {
    String folded =
        Normalizer.normalize(text.trim().toLowerCase(Locale.ROOT), Normalizer.Form.NFD)
            .replaceAll("\\p{M}+", "");
    return folded.replaceAll("[^a-z0-9]+", "-").replaceAll("^-+|-+$", "");
  }

  /**
   * Shortens {@code text} to at most {@code maxLength} characters, ending with an ellipsis that
   * counts toward the limit.
   *
   * @param text the text to shorten
   * @param maxLength the maximum result length; must be non-negative
   * @return the shortened text, or {@code text} itself when it already fits
   */
  public static String truncate(String text, int maxLength) {
    return truncate(text, maxLength, "…");
  }

  /**
   * Shortens {@code text} to at most {@code maxLength} characters, ending with {@code ellipsis}
   * (which counts toward the limit). Text that already fits is returned unchanged.
   *
   * @param text the text to shorten
   * @param maxLength the maximum result length; must be non-negative
   * @param ellipsis the marker appended when text is cut
   * @return the shortened text, or {@code text} itself when it already fits
   * @throws IllegalArgumentException when {@code maxLength} is negative
   */
  public static String truncate(String text, int maxLength, String ellipsis) {
    if (maxLength < 0) {
      throw new IllegalArgumentException("maxLength must be non-negative");
    }
    if (text.length() <= maxLength) {
      return text;
    }
    if (maxLength <= ellipsis.length()) {
      return ellipsis.substring(0, maxLength);
    }
    return text.substring(0, maxLength - ellipsis.length()) + ellipsis;
  }
}
