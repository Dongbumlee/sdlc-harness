// Copyright (c) {{Year}}. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root for license information.

package cli

import (
	"bufio"
	"fmt"
	"os"
	"strings"

	"github.com/spf13/cobra"

	"example.com/{{project-name}}/internal/textkit"
)

// newTextCmd builds the `text` noun with its verbs. The structure is
// tool <noun> <verb>; every verb shares the file-delivery behaviour
// (--out/--force/--dry-run) from the global safety flags.
func newTextCmd(st *state) *cobra.Command {
	text := &cobra.Command{
		Use:   "text",
		Short: "Text transformations",
		Long:  "Text transformations over the textkit core. Results go to stdout, or to a file with --out.",
	}

	var outPath string
	var force bool

	slugify := &cobra.Command{
		Use:   "slugify <text>",
		Short: "Convert text to a lowercase hyphenated slug",
		Example: `  {{project-name}} text slugify "Hello, World!"
  {{project-name}} text slugify --json "Hello, World!"
  {{project-name}} text slugify --out slug.txt "Hello, World!"`,
		Args: func(cmd *cobra.Command, args []string) error {
			if len(args) < 1 {
				return usagef("slugify requires the text to convert")
			}
			return nil
		},
		RunE: func(cmd *cobra.Command, args []string) error {
			result := textkit.Slugify(strings.Join(args, " "))
			return deliver(cmd, st, result, nil, outPath, force)
		},
	}

	var max int
	truncate := &cobra.Command{
		Use:   "truncate <text>",
		Short: "Shorten text to at most --max characters",
		Example: `  {{project-name}} text truncate --max 6 "a longer sentence"
  {{project-name}} text truncate --max 6 --json "a longer sentence"`,
		Args: func(cmd *cobra.Command, args []string) error {
			if len(args) < 1 {
				return usagef("truncate requires the text to shorten")
			}
			return nil
		},
		RunE: func(cmd *cobra.Command, args []string) error {
			if max < 1 {
				return usagef("--max must be at least 1, got %d", max)
			}
			input := strings.Join(args, " ")
			result := textkit.Truncate(input, max)
			extra := map[string]any{"truncated": result != input}
			return deliver(cmd, st, result, extra, outPath, force)
		},
	}
	truncate.Flags().IntVar(&max, "max", 40, "maximum length in characters (including the ellipsis)")

	for _, verb := range []*cobra.Command{slugify, truncate} {
		verb.Flags().StringVar(&outPath, "out", "", "write the result to this file instead of stdout")
		verb.Flags().BoolVar(&force, "force", false, "overwrite the --out file if it exists")
		text.AddCommand(verb)
	}
	return text
}

// deliver routes a verb's result: to stdout by default, or to a file
// when --out is set. File delivery honours the safety contract —
// --dry-run writes nothing, an existing file is never overwritten
// without --force, and the user is only ever prompted at a terminal
// (and never with --no-input).
func deliver(cmd *cobra.Command, st *state, result string, extra map[string]any, outPath string, force bool) error {
	out := st.out(cmd)
	if outPath == "" {
		return out.result(result, extra)
	}
	if st.opts.dryRun {
		out.diagnostic("dry-run: would write %d bytes to %s", len(result)+1, outPath)
		return nil
	}
	if _, err := os.Stat(outPath); err == nil && !force {
		if st.opts.noInput || !stdinIsTTY(cmd) {
			return fmt.Errorf("%s already exists (use --force to overwrite)", outPath)
		}
		_, _ = fmt.Fprintf(cmd.ErrOrStderr(), "Overwrite %s? [y/N] ", outPath)
		reader := bufio.NewReader(cmd.InOrStdin())
		answer, _ := reader.ReadString('\n')
		if strings.ToLower(strings.TrimSpace(answer)) != "y" {
			out.diagnostic("aborted; %s left unchanged", outPath)
			return nil
		}
	}
	if err := os.WriteFile(outPath, []byte(result+"\n"), 0o644); err != nil {
		return err
	}
	out.diagnostic("wrote %s", outPath)
	return nil
}
