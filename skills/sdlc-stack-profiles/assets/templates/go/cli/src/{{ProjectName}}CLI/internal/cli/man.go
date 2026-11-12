// Copyright (c) {{Year}}. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root for license information.

package cli

import (
	"os"
	"strings"

	"github.com/spf13/cobra"
	"github.com/spf13/cobra/doc"
)

// newManCmd returns the hidden `man` command: man pages are generated
// from the command tree itself, never written by hand, so they cannot
// drift from the shipped flags. The release pipeline runs this and
// ships the output with the archives.
func newManCmd(st *state) *cobra.Command {
	return &cobra.Command{
		Use:    "man [directory]",
		Short:  "Generate man pages for all commands",
		Hidden: true,
		Args: func(cmd *cobra.Command, args []string) error {
			if len(args) > 1 {
				return usagef("man takes at most one directory argument")
			}
			return nil
		},
		RunE: func(cmd *cobra.Command, args []string) error {
			dir := "./man"
			if len(args) == 1 {
				dir = args[0]
			}
			if err := os.MkdirAll(dir, 0o755); err != nil {
				return err
			}
			header := &doc.GenManHeader{
				Title:   strings.ToUpper(cmd.Root().Name()),
				Section: "1",
			}
			return doc.GenManTree(cmd.Root(), header, dir)
		},
	}
}
