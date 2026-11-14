/**
 * Application configuration, split the way the web type requires.
 *
 * The split is structural, and Next.js enforces the mechanism:
 * only variables prefixed NEXT_PUBLIC_ are inlined into the
 * client bundle. This module is the public half — browser-safe
 * values that any component may read. Server-only values live in
 * lib/server-config.ts, which client code must never import (the
 * architecture test enforces that mechanically). Leaking a server
 * secret into the bundle is this type's signature security
 * defect.
 */
export interface PublicConfig {
  /** Browser-safe display name, rendered into pages. */
  appName: string;
}

export const publicConfig: PublicConfig = {
  appName: process.env.NEXT_PUBLIC_APP_NAME ?? "{{ProjectName}}",
};
