# {{project-name}}

A Go library. The sample package, `textkit`, provides small
text-normalization helpers — replace it with your own packages; the
structure, gates, and policies around it are the template.

## Quickstart

```go
package main

import (
    "fmt"

    "example.com/{{project-name}}/textkit"
)

func main() {
    fmt.Println(textkit.Slugify("Hello, World!"))       // hello-world
    fmt.Println(textkit.Truncate("a longer sentence", 6)) // a lon…
}
```

This exact usage is executable: it lives in
`src/{{ProjectName}}Lib/textkit/example_test.go` as Go examples, and
`go test` runs and verifies it on every supported Go version — the
quickstart cannot drift from the shipped API.

## Install

```bash
go get example.com/{{project-name}}@latest
```

## Supported Go versions

| Go       | Status    |
| -------- | --------- |
| 1.26     | Supported |
| 1.27     | Supported |

The floor is the `go` directive in `go.mod`. CI tests every version in
this table. Raising the floor is a breaking change: it ships only in a
major release.

## Versioning and API stability

Releases follow semantic versioning, and the tag is the version — the
Go module proxy serves the library from the tag, so there is nothing
else to publish. The public API is every exported identifier of the
non-`internal/` packages. CI diffs the exported API against the last
release tag with apidiff and fails on incompatible changes; a major
version (`/v2` module-path suffix from v2 on) is the only place the API
may break.

Dependencies are declared as minimum versions in `go.mod` — a library
states what it can work with and lets the consumer's build resolve the
exact set.

## Deprecation policy

Mark a deprecated identifier with a `Deprecated:` paragraph in its doc
comment (the standard Go convention — tooling surfaces it) in one
release; remove it no earlier than the next major release.

## Development

```bash
cd src/{{ProjectName}}Lib
go build ./...
go test ./...
gofmt -l .
go vet ./...
```

Releasing: move the CHANGELOG *Unreleased* entries under a
`## [X.Y.Z] - YYYY-MM-DD` heading, then tag `vX.Y.Z`. The release
workflow verifies the tag, smoke-tests consumption from a clean module,
and creates the GitHub Release.
