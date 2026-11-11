/**
 * Text helpers published by {{ProjectName}}. Everything a consumer
 * may rely on is re-exported from the package entry point and
 * declared in the API report under `etc/`; anything not exported
 * from there is internal and may change without notice.
 */

/**
 * Returns a URL-safe slug for `text`: accents are folded to their
 * ASCII base letters and every run of remaining non-alphanumeric
 * characters becomes one hyphen.
 *
 * @public
 */
export function slugify(text: string): string {
  const folded = text
    .trim()
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "");
  return folded.replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}

/**
 * Shortens `text` to at most `maxLength` characters, ending with
 * `ellipsis` (which counts toward the limit). Text that already
 * fits is returned unchanged.
 *
 * @public
 */
export function truncate(
  text: string,
  maxLength: number,
  ellipsis: string = "…",
): string {
  if (maxLength < 0) {
    throw new RangeError("maxLength must be non-negative");
  }
  if (text.length <= maxLength) {
    return text;
  }
  if (maxLength <= ellipsis.length) {
    return ellipsis.slice(0, maxLength);
  }
  return text.slice(0, maxLength - ellipsis.length) + ellipsis;
}
