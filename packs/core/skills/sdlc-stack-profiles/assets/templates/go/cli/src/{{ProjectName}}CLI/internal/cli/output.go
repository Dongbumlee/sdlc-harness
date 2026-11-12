// Copyright (c) {{Year}}. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root for license information.

package cli

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
)

// output owns the stream contract: results on stdout (plain or JSON),
// diagnostics on stderr, and color only where a human is looking at
// a terminal — never in piped data.
type output struct {
	stdout io.Writer
	stderr io.Writer
	format string
	color  bool
	quiet  bool
}

// result prints a command's primary data to stdout. In JSON mode the
// value is wrapped in an object with a stable "result" field; extra
// fields may be added by the caller but the shape never changes
// within a major version.
func (o *output) result(value string, extra map[string]any) error {
	if o.format == "json" {
		payload := map[string]any{"result": value}
		for k, v := range extra {
			payload[k] = v
		}
		enc := json.NewEncoder(o.stdout)
		return enc.Encode(payload)
	}
	_, err := fmt.Fprintln(o.stdout, value)
	return err
}

// diagnostic prints a human-only note to stderr, unless --quiet.
// Diagnostics never carry primary data.
func (o *output) diagnostic(format string, args ...any) {
	if o.quiet {
		return
	}
	msg := fmt.Sprintf(format, args...)
	if o.color {
		_, _ = fmt.Fprintf(o.stderr, "\u001b[2m%s\u001b[0m\n", msg)
		return
	}
	_, _ = fmt.Fprintln(o.stderr, msg)
}

// colorEnabled decides whether styled diagnostics are appropriate:
// an explicit --no-color or the NO_COLOR environment variable wins,
// and color is only ever used on a terminal.
func colorEnabled(w io.Writer, noColorFlag bool) bool {
	if noColorFlag {
		return false
	}
	if _, present := os.LookupEnv("NO_COLOR"); present {
		return false
	}
	f, ok := w.(*os.File)
	if !ok {
		return false
	}
	info, err := f.Stat()
	if err != nil {
		return false
	}
	return info.Mode()&os.ModeCharDevice != 0
}

// stdinIsTTY reports whether the command's input is a terminal —
// the only situation in which prompting is allowed.
func stdinIsTTY(cmd interface{ InOrStdin() io.Reader }) bool {
	f, ok := cmd.InOrStdin().(*os.File)
	if !ok {
		return false
	}
	info, err := f.Stat()
	if err != nil {
		return false
	}
	return info.Mode()&os.ModeCharDevice != 0
}
