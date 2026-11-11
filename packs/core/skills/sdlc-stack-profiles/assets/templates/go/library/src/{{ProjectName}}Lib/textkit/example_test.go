// Copyright (c) {{Year}}. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root for license information.

package textkit_test

import (
	"fmt"

	"example.com/{{project-name}}/textkit"
)

// These examples are the README quickstart in executable form: `go test`
// runs them and verifies the output, so the documented usage can never
// drift from the shipped API.

func ExampleSlugify() {
	fmt.Println(textkit.Slugify("Hello, World!"))
	// Output: hello-world
}

func ExampleTruncate() {
	fmt.Println(textkit.Truncate("a longer sentence", 6))
	// Output: a lon…
}
