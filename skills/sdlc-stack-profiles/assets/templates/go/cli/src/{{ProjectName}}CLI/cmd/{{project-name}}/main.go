// Copyright (c) {{Year}}. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root for license information.

// Command {{project-name}} is the thin entry point: all behaviour lives
// in internal/cli over the internal/textkit core, so the logic is
// importable and testable without the binary.
package main

import (
	"os"

	"example.com/{{project-name}}/internal/cli"
)

// version is injected at release time from the git tag
// (-ldflags "-X main.version=..."); untagged builds report "dev".
var version = "dev"

func main() {
	os.Exit(cli.Main(version))
}
