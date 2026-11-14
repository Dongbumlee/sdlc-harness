// Copyright (c) {{Year}}. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root for license information.

// Package textkit is the CLI's library core: the testable logic lives
// here, free of flag parsing and I/O, and the commands in internal/cli
// are a thin shell over it.
package textkit

import (
	"strings"
	"unicode"
)

// Slugify converts s to a lowercase, hyphen-separated slug: letters and
// digits are kept, every other run of characters becomes one hyphen, and
// leading/trailing hyphens are trimmed.
func Slugify(s string) string {
	var b strings.Builder
	lastHyphen := true // trims leading separators
	for _, r := range s {
		switch {
		case unicode.IsLetter(r) || unicode.IsDigit(r):
			b.WriteRune(unicode.ToLower(r))
			lastHyphen = false
		case !lastHyphen:
			b.WriteByte('-')
			lastHyphen = true
		}
	}
	return strings.TrimSuffix(b.String(), "-")
}

// Truncate shortens s to at most max runes, appending an ellipsis when
// truncation occurs. A max below 1 returns an empty string.
func Truncate(s string, max int) string {
	if max < 1 {
		return ""
	}
	runes := []rune(s)
	if len(runes) <= max {
		return s
	}
	if max == 1 {
		return "…"
	}
	return string(runes[:max-1]) + "…"
}
