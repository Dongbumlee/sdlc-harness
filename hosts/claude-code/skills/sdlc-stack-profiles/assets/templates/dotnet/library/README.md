# {{ProjectName}}

<!-- One line: what the library does and who uses it. The design
phase expands this stub into the full project README. -->

## Install

```bash
dotnet add package {{ProjectName}}
```

## Quickstart

```csharp
using {{ProjectName}};

var slug = TextTransforms.Slugify("Hello, World!");  // "hello-world"
var shortText = TextTransforms.Truncate("hello world", 8);  // "hello w…"
```

## Supported frameworks

.NET 8 and .NET 10. CI builds and tests every target framework the
package declares — the declared support range is tested, not
aspirational.

## Versioning and deprecation

This library follows strict Semantic Versioning. The public surface
is a declared contract: every public symbol is listed in
`PublicAPI.Shipped.txt` / `PublicAPI.Unshipped.txt`, and the build
fails when code and declaration disagree, so an accidental breaking
change fails the PR instead of a consumer's build. Runtime
dependencies are declared as version ranges, never exact versions,
and the library commits no lock file — consumers resolve the ranges
against their own dependency graph. Deprecation path: a public
member is marked `[Obsolete]` (with a changelog entry) in one
release and removed no earlier than the next major version.

## Security

See [SECURITY.md](SECURITY.md) for how to report a vulnerability.

## Changelog

See [CHANGELOG.md](CHANGELOG.md). Releases are cut from version
tags (`vX.Y.Z`): the release workflow verifies the tagged tree,
packs the NuGet package with the version taken from the tag,
smoke-tests the package from a clean consumer project, and
publishes to NuGet by trusted publishing (OIDC — no stored
registry token) before creating the GitHub Release.
