# {{ProjectName}}

<!-- One line: what this app does and who it serves. The design
phase expands this stub into the full project README. -->

## Getting started

Prerequisites: Node.js 22+ and pnpm.

```bash
cd src/{{ProjectName}}Web
pnpm install
pnpm dev
pnpm test
```

## The web contract

This template follows the web standard in the sdlc-stack-profiles
skill ("Web type — the browser is untrusted"):

- **Environment split, structurally.** Next.js inlines only
  `NEXT_PUBLIC_`-prefixed variables into the client bundle, and
  the configuration lives in two modules on that line:
  `src/lib/config.ts` (public, browser-safe) and
  `src/lib/server-config.ts` (server-only). The architecture
  test fails the build if a client component or a
  Components/Services module imports the server module — leaking
  a server secret into the bundle is this type's signature
  security defect. See `.env.example` for the two sections.
- **Markup floor (WCAG 2.2 AA).** The root layout ships with a
  language attribute, a skip link, landmark regions, and visible
  focus; each page carries exactly one `<h1>` and labelled form
  controls. `src/app/page.test.tsx` asserts the floor on the
  composed page so a new page cannot silently drop it.
- **Server-rendered first.** Pages render on the server (this
  template exports statically); client components enhance, they
  are not the only path to the content.

## Security

See [SECURITY.md](SECURITY.md) for how to report a vulnerability.

## Changelog

See [CHANGELOG.md](CHANGELOG.md). Releases are cut from version
tags (`vX.Y.Z`): the release workflow verifies the tagged tree and
publishes the matching changelog section as the GitHub Release
notes.
