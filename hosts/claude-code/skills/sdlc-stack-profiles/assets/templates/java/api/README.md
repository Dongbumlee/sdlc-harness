# {{ProjectName}}

<!-- One line: what this service does and who it serves. The design
phase expands this stub into the full project README. -->

## Getting started

Prerequisites: JDK 21 (the Maven wrapper is included).

```bash
cd src/{{ProjectName}}API
./mvnw spring-boot:run
./mvnw -B verify
```

## Security

See [SECURITY.md](SECURITY.md) for how to report a vulnerability.

## Changelog

See [CHANGELOG.md](CHANGELOG.md). Releases are cut from version
tags (`vX.Y.Z`): the release workflow verifies the tagged tree and
publishes the matching changelog section as the GitHub Release
notes.
