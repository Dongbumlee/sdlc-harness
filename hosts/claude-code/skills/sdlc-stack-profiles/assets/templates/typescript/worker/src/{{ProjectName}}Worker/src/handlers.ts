/**
 * Sample handlers. Replace with your own job types; the contract is
 * what matters: return the effect's result string, throw
 * PermanentError for payloads that can never succeed, and let
 * everything else surface as retryable.
 */

import { PermanentError, type Handler } from "./worker.js";

/**
 * Turn payload.text into a slug — the sample job's effect.
 * Lowercase, letters and digits kept, every other run of characters
 * becomes one hyphen, leading/trailing hyphens trimmed — the same
 * sample semantics as the other bundled templates.
 */
export function slugify(payload: Record<string, unknown>): string {
  const text = payload["text"];
  if (typeof text !== "string" || text.trim() === "") {
    throw new PermanentError("payload.text must be a non-empty string");
  }
  let slug = "";
  let lastHyphen = true; // trims leading separators
  for (const char of text.toLowerCase()) {
    if (/[\p{L}\p{N}]/u.test(char)) {
      slug += char;
      lastHyphen = false;
    } else if (!lastHyphen) {
      slug += "-";
      lastHyphen = true;
    }
  }
  return slug.replace(/-+$/, "");
}

export const HANDLERS: Record<string, Handler> = { slugify };
