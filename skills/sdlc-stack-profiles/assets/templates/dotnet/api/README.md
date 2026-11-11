# {{ProjectName}}

<!-- One line: what this service does and who it serves. The design
phase expands this stub into the full project README. -->

## Getting started

Prerequisites: .NET 10 SDK.

```bash
dotnet restore {{ProjectName}}.sln
dotnet run --project src/{{ProjectName}}API
dotnet test {{ProjectName}}.sln
```

## Security

See [SECURITY.md](SECURITY.md) for how to report a vulnerability.

## Changelog

See [CHANGELOG.md](CHANGELOG.md). Releases are cut from version
tags (`vX.Y.Z`): the release workflow verifies the tagged tree and
publishes the matching changelog section as the GitHub Release
notes.
