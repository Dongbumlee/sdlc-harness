/**
 * Server-only configuration: never imported by client code.
 *
 * Values here have no NEXT_PUBLIC_ prefix, so Next.js never
 * inlines them into the client bundle — they exist only where
 * this module can be imported: server components, route
 * handlers, and build-time code. The architecture test fails the
 * build if a client component ("use client") or a
 * Components/Services module imports this file. Never render
 * these values, pass them as props to a client component, or log
 * them: any of those ships the secret to the browser.
 */
export interface ServerConfig {
  /** Credential for server-side calls only. */
  apiKey: string;
}

export const serverConfig: ServerConfig = {
  apiKey: process.env.SERVER_API_KEY ?? "",
};
