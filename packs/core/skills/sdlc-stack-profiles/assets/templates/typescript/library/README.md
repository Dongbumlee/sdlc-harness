# {{ProjectName}}

A TypeScript library. This README is the contract a consumer reads:
install, quickstart, supported versions, and how the API evolves.

## Install

```sh
npm install {{project-name}}
```

## Quickstart

```js
import { slugify, truncate } from "{{project-name}}";

console.log(slugify("Hello, World!")); // "hello-world"
console.log(truncate("hello world", 8)); // "hello w…"
```

This example lives in `examples/quickstart.mjs` and CI executes it
against the built package, so it cannot drift from the shipped API.

## API

The public surface is exactly what `src/index.ts` exports; the
machine-readable report is [`etc/{{project-name}}.api.md`](etc/{{project-name}}.api.md).
CI fails when the code and the report disagree — regenerate it
after an intentional API change with `pnpm api` and commit the
updated report.

## Supported versions

Node.js **20 and later** (CI tests 20, 22, and 24).
TypeScript consumers need TypeScript 5.x or later for the shipped
declarations.

Dependencies are declared as version ranges and no lock file is
committed: a library must resolve cleanly inside the consumer's
own dependency set, not impose one.

## Versioning and deprecation

Releases follow Semantic Versioning. Inside a major version, API
changes are additive only. Deprecation is a process, never a
surprise removal: a member is marked deprecated in one release
(release notes name the replacement), stays functional, and may be
removed only in the next major version.

## Security

See [SECURITY.md](SECURITY.md) for how to report a vulnerability.

## Releases

Releases are cut from `v*.*.*` tags by
`.github/workflows/release.yml`: the tree is verified, the tag is
checked against the `package.json` version, the packed tarball is
smoke-tested in a clean project, and the package is published to
npm with provenance, then a GitHub Release is created from the
matching [CHANGELOG.md](CHANGELOG.md) section.

Publishing uses npm trusted publishing (OIDC) — there is no stored
registry token. One-time setup: publish the first release manually
once, then configure this repository as a trusted publisher on
npmjs.com; every release after that runs tokenless.
