package com.example.{{PackageName}}.textkit;

/**
 * The CLI's library core: the testable logic lives here, free of argument parsing and I/O, and the
 * commands in the {@code cli} package are a thin shell over it.
 */
public final class TextKit {

  private TextKit() {}

  /**
   * Convert text to a lowercase, hyphen-separated slug. Letters and digits are kept, every other
   * run of characters becomes one hyphen, and leading/trailing hyphens are trimmed.
   */
  public static String slugify(String text) {
    var slug = new StringBuilder();
    var lastHyphen = true; // trims leading separators
    for (var c : text.toCharArray()) {
      if (Character.isLetterOrDigit(c)) {
        slug.append(Character.toLowerCase(c));
        lastHyphen = false;
      } else if (!lastHyphen) {
        slug.append('-');
        lastHyphen = true;
      }
    }
    return slug.toString().replaceAll("-+$", "");
  }

  /**
   * Shorten text to at most {@code maxLength} characters. An ellipsis marks truncation. A {@code
   * maxLength} below 1 returns an empty string.
   */
  public static String truncate(String text, int maxLength) {
    if (maxLength < 1) {
      return "";
    }
    if (text.length() <= maxLength) {
      return text;
    }
    return maxLength == 1 ? "…" : text.substring(0, maxLength - 1) + "…";
  }
}
