// Copyright (c) {{Year}}. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root for license information.

// Package cli builds the command tree over the textkit core. The
// command surface is a contract (see the cli standard in the
// sdlc-stack-profiles skill): data goes to stdout, diagnostics to
// stderr, and exit codes follow the documented map — 0 success,
// 1 failure, 2 usage error.
package cli

import (
	"errors"
	"fmt"
	"os"
	"strings"

	"github.com/spf13/cobra"
)

// Exit codes — the documented map. Changes here are breaking changes.
const (
	ExitOK      = 0
	ExitFailure = 1
	ExitUsage   = 2
)

// usageError marks errors caused by how the tool was invoked (bad
// arguments, invalid flag values); they map to ExitUsage.
type usageError struct{ msg string }

func (e *usageError) Error() string { return e.msg }

func usagef(format string, args ...any) *usageError {
	return &usageError{msg: fmt.Sprintf(format, args...)}
}

// options are the resolved global settings, after configuration
// precedence (flags, then environment, then defaults) is applied.
type options struct {
	format  string // "plain" or "json"
	noColor bool
	verbose bool
	quiet   bool
	noInput bool
	dryRun  bool
}

// state is shared across the command tree for one execution.
type state struct {
	opts      options
	flagErr   bool // set by the flag error func: a parse failure is a usage error
	version   string
	envPrefix string
}

// Main builds the root command, executes it, prints any error to
// stderr, and returns the process exit code.
func Main(version string) int {
	root, st := newRootCmd(version)
	root.SetOut(os.Stdout)
	root.SetErr(os.Stderr)
	root.SetIn(os.Stdin)
	return execute(root, st)
}

// execute runs the command and classifies the outcome into the
// exit-code map. It is separate from Main so tests can drive the
// whole tree in-process with buffers.
func execute(root *cobra.Command, st *state) int {
	_, err := root.ExecuteC()
	if err == nil {
		return ExitOK
	}
	code := ExitFailure
	var ue *usageError
	// Usage errors: our own argument validation, flag parse failures
	// (via the flag error func), and cobra's unknown-command error,
	// which carries no type and is matched by its stable prefix.
	if st.flagErr || errors.As(err, &ue) || strings.HasPrefix(err.Error(), "unknown command") {
		code = ExitUsage
	}
	_, _ = fmt.Fprintf(root.ErrOrStderr(), "Error: %s\n", err.Error())
	if code == ExitUsage {
		_, _ = fmt.Fprintf(root.ErrOrStderr(), "Run '%s --help' for usage.\n", root.Name())
	}
	return code
}

func newRootCmd(version string) (*cobra.Command, *state) {
	st := &state{version: version}
	var flagJSON bool
	var flagFormat string

	root := &cobra.Command{
		Use:   "{{project-name}}",
		Short: "{{ProjectName}} sample command-line tool",
		Long: `{{ProjectName}} is a sample command-line tool built from the go/cli
template. It demonstrates the CLI contract: data goes to stdout,
diagnostics go to stderr, and the command surface (flags, output
schema, exit codes) is a tested API.

Exit codes:
  0  success
  1  failure (the command ran but could not complete)
  2  usage error (unknown command, bad flags, invalid arguments)

Configuration precedence: flags, then environment
(<PREFIX>_FORMAT and friends, where the prefix is the
upper-cased tool name), then defaults. Secrets are read from
the environment, never from flags.`,
		Version:       version,
		SilenceErrors: true,
		SilenceUsage:  true,
		PersistentPreRunE: func(cmd *cobra.Command, args []string) error {
			return st.resolve(cmd, flagFormat, flagJSON)
		},
	}
	st.envPrefix = strings.ToUpper(strings.ReplaceAll(root.Name(), "-", "_")) + "_"
	root.SetFlagErrorFunc(func(cmd *cobra.Command, err error) error {
		st.flagErr = true
		return err
	})

	pf := root.PersistentFlags()
	pf.StringVar(&flagFormat, "format", "plain", "output format: plain or json")
	pf.BoolVar(&flagJSON, "json", false, "shorthand for --format json")
	pf.BoolVar(&st.opts.noColor, "no-color", false, "disable color in diagnostics (NO_COLOR is also honoured)")
	pf.BoolVar(&st.opts.verbose, "verbose", false, "print diagnostics about what the command is doing")
	pf.BoolVar(&st.opts.quiet, "quiet", false, "suppress diagnostics")
	pf.BoolVar(&st.opts.noInput, "no-input", false, "never prompt; fail instead of asking")
	pf.BoolVar(&st.opts.dryRun, "dry-run", false, "show what would happen without writing anything")

	root.AddCommand(newTextCmd(st))
	root.AddCommand(newManCmd(st))
	return root, st
}

// resolve applies configuration precedence for the format setting:
// an explicitly changed flag wins, then the environment, then the
// default. --json counts as a flag-level choice.
func (st *state) resolve(cmd *cobra.Command, flagFormat string, flagJSON bool) error {
	format := flagFormat
	switch {
	case cmd.Flags().Changed("json") && flagJSON:
		format = "json"
	case cmd.Flags().Changed("format"):
		format = flagFormat
	default:
		if env := os.Getenv(st.envPrefix + "FORMAT"); env != "" {
			format = env
		}
	}
	if format != "plain" && format != "json" {
		return usagef("invalid format %q: want plain or json", format)
	}
	st.opts.format = format
	return nil
}

// out returns the output writer bound to this command's streams and
// the resolved options.
func (st *state) out(cmd *cobra.Command) *output {
	return &output{
		stdout: cmd.OutOrStdout(),
		stderr: cmd.ErrOrStderr(),
		format: st.opts.format,
		color:  colorEnabled(cmd.OutOrStdout(), st.opts.noColor),
		quiet:  st.opts.quiet,
	}
}
