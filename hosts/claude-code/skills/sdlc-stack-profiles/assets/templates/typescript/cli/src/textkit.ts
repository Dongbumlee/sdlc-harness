/**
 * The CLI's library core: the testable logic lives here, free of
 * argument parsing and I/O, and the commands in `cli` are a thin
 * shell over it.
 */

/** Convert text to a lowercase, hyphen-separated slug. Letters and
 * digits are kept, every other run of characters becomes one hyphen,
 * and leading/trailing hyphens are trimmed. */
export function slugify(text: string): string {
  let slug = "";
  let lastHyphen = true; // trims leading separators
  for (const char of text) {
    if (/[\p{L}\p{N}]/u.test(char)) {
      slug += char.toLowerCase();
      lastHyphen = false;
    } else if (!lastHyphen) {
      slug += "-";
      lastHyphen = true;
    }
  }
  return slug.replace(/-+$/, "");
}

/** Shorten text to at most `maxLength` characters. An ellipsis
 * marks truncation. A `maxLength` below 1 returns an empty string. */
export function truncate(text: string, maxLength: number): string {
  if (maxLength < 1) {
    return "";
  }
  if (text.length <= maxLength) {
    return text;
  }
  return maxLength === 1 ? "…" : text.slice(0, maxLength - 1) + "…";
}
