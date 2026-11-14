// Copyright (c) {{Year}}. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root for license information.

package cli

import (
	"bytes"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// run drives the whole command tree in-process, exactly as Main does,
// and captures the exit code and both streams.
func run(t *testing.T, stdin string, args ...string) (int, string, string) {
	t.Helper()
	root, st := newRootCmd("v0.0.0-test")
	var stdout, stderr bytes.Buffer
	root.SetOut(&stdout)
	root.SetErr(&stderr)
	root.SetIn(strings.NewReader(stdin))
	root.SetArgs(args)
	code := execute(root, st)
	return code, stdout.String(), stderr.String()
}

// Golden tests: the help and primary outputs are the CLI's contract.
// Regenerate deliberately with UPDATE_GOLDEN=1 go test ./... and
// review the diff like an API change.
func TestGoldenOutputs(t *testing.T) {
	cases := map[string][]string{
		"help-root":     {"--help"},
		"help-text":     {"text", "--help"},
		"slugify":       {"text", "slugify", "Hello, World!"},
		"slugify-json":  {"text", "slugify", "--json", "Hello, World!"},
		"truncate":      {"text", "truncate", "--max", "6", "a longer sentence"},
		"truncate-json": {"text", "truncate", "--max", "6", "--json", "a longer sentence"},
		"version":       {"--version"},
	}
	for name, args := range cases {
		t.Run(name, func(t *testing.T) {
			code, stdout, _ := run(t, "", args...)
			if code != ExitOK {
				t.Fatalf("exit = %d, want %d", code, ExitOK)
			}
			path := filepath.Join("testdata", name+".golden")
			if os.Getenv("UPDATE_GOLDEN") == "1" {
				if err := os.WriteFile(path, []byte(stdout), 0o644); err != nil {
					t.Fatal(err)
				}
				return
			}
			want, err := os.ReadFile(path)
			if err != nil {
				t.Fatal(err)
			}
			if stdout != string(want) {
				t.Errorf("output drifted from golden %s:\n--- got ---\n%s\n--- want ---\n%s", path, stdout, want)
			}
		})
	}
}

// Exit-code tests: each failure mode maps to the documented code.
func TestExitCodes(t *testing.T) {
	cases := []struct {
		name string
		args []string
		want int
	}{
		{"success", []string{"text", "slugify", "Hello"}, ExitOK},
		{"unknown command", []string{"frobnicate"}, ExitUsage},
		{"missing argument", []string{"text", "slugify"}, ExitUsage},
		{"bad flag value", []string{"text", "truncate", "--max", "abc", "text"}, ExitUsage},
		{"invalid max", []string{"text", "truncate", "--max", "0", "text"}, ExitUsage},
		{"invalid format", []string{"--format", "yaml", "text", "slugify", "Hi"}, ExitUsage},
		{"unwritable out", []string{"text", "slugify", "--out", "/nonexistent-dir/x.txt", "Hi"}, ExitFailure},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			code, _, _ := run(t, "", tc.args...)
			if code != tc.want {
				t.Errorf("exit = %d, want %d", code, tc.want)
			}
		})
	}
}

// Configuration precedence: flags beat the environment, the
// environment beats the default.
func TestFormatPrecedence(t *testing.T) {
	t.Setenv("SAMPLE_FORMAT", "json")
	if _, stdout, _ := run(t, "", "text", "slugify", "Hi There"); !strings.HasPrefix(stdout, "{") {
		t.Errorf("env format not applied, stdout = %q", stdout)
	}
	if _, stdout, _ := run(t, "", "--format", "plain", "text", "slugify", "Hi There"); stdout != "hi-there\n" {
		t.Errorf("flag should beat env, stdout = %q", stdout)
	}
}

// File delivery: dry-run writes nothing, an existing file is not
// overwritten without --force (and never prompts a non-terminal),
// --force overwrites.
func TestFileDelivery(t *testing.T) {
	dir := t.TempDir()
	target := filepath.Join(dir, "out.txt")

	code, _, _ := run(t, "", "text", "slugify", "--dry-run", "--out", target, "Hello World")
	if code != ExitOK {
		t.Fatalf("dry-run exit = %d", code)
	}
	if _, err := os.Stat(target); !os.IsNotExist(err) {
		t.Fatal("dry-run must not write the file")
	}

	code, _, _ = run(t, "", "text", "slugify", "--out", target, "Hello World")
	if code != ExitOK {
		t.Fatalf("write exit = %d", code)
	}
	if body, _ := os.ReadFile(target); string(body) != "hello-world\n" {
		t.Fatalf("file body = %q", body)
	}

	code, _, _ = run(t, "", "text", "slugify", "--out", target, "Changed Text")
	if code != ExitFailure {
		t.Fatalf("overwrite without --force exit = %d, want %d", code, ExitFailure)
	}
	if body, _ := os.ReadFile(target); string(body) != "hello-world\n" {
		t.Fatalf("file must be unchanged, body = %q", body)
	}

	code, _, _ = run(t, "", "text", "slugify", "--out", target, "--force", "Changed Text")
	if code != ExitOK {
		t.Fatalf("force exit = %d", code)
	}
	if body, _ := os.ReadFile(target); string(body) != "changed-text\n" {
		t.Fatalf("forced body = %q", body)
	}
}
