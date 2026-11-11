// Copyright (c) {{Year}}. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root for license information.

package textkit_test

import (
	"testing"

	"example.com/{{project-name}}/textkit"
)

// Black-box tests: this file imports the library exactly as a consumer
// does and exercises only the public API.

func TestSlugify(t *testing.T) {
	cases := map[string]string{
		"Hello, World!":   "hello-world",
		"  spaced   out ": "spaced-out",
		"Go 1.26":         "go-1-26",
		"":                "",
		"!!!":             "",
	}
	for in, want := range cases {
		if got := textkit.Slugify(in); got != want {
			t.Errorf("Slugify(%q) = %q, want %q", in, got, want)
		}
	}
}

func TestTruncate(t *testing.T) {
	if got := textkit.Truncate("short", 10); got != "short" {
		t.Errorf("Truncate no-op = %q, want %q", got, "short")
	}
	if got := textkit.Truncate("a longer sentence", 6); got != "a lon…" {
		t.Errorf("Truncate = %q, want %q", got, "a lon…")
	}
	if got := textkit.Truncate("anything", 0); got != "" {
		t.Errorf("Truncate max<1 = %q, want empty", got)
	}
	if got := textkit.Truncate("éclair", 3); got != "éc…" {
		t.Errorf("Truncate must count runes, got %q", got)
	}
}
