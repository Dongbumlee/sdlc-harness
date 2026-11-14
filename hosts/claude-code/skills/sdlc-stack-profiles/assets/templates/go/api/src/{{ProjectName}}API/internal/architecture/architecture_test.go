// Package architecture enforces the profile's dependency direction
// mechanically: layers may only depend in the declared direction
// (web -> service -> model), and only the composition root (cmd) may
// wire implementations together. A violation fails the test run
// instead of waiting for a reviewer to notice it.
package architecture

import (
	"fmt"
	"go/parser"
	"go/token"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"testing"
)

// forbidden maps a layer to layers it must never import.
var forbidden = map[string][]string{
	"model":   {"service", "web", "cmd"},
	"service": {"web", "cmd"},
	"web":     {"cmd"},
}

func modulePath(t *testing.T, root string) string {
	t.Helper()
	content, err := os.ReadFile(filepath.Join(root, "go.mod"))
	if err != nil {
		t.Fatalf("read go.mod: %v", err)
	}
	for _, line := range strings.Split(string(content), "\n") {
		if strings.HasPrefix(line, "module ") {
			return strings.TrimSpace(strings.TrimPrefix(line, "module "))
		}
	}
	t.Fatal("go.mod has no module line")
	return ""
}

func layerOf(root, path string) (string, error) {
	rel, err := filepath.Rel(root, path)
	if err != nil {
		return "", err
	}
	parts := strings.Split(filepath.ToSlash(rel), "/")
	switch parts[0] {
	case "cmd":
		return "cmd", nil
	case "internal":
		if len(parts) > 1 {
			return parts[1], nil
		}
	}
	return "", nil
}

func TestDependencyDirection(t *testing.T) {
	root, err := filepath.Abs(filepath.Join("..", ".."))
	if err != nil {
		t.Fatalf("resolve module root: %v", err)
	}
	module := modulePath(t, root)

	var violations []string
	err = filepath.WalkDir(root, func(path string, entry os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if entry.IsDir() || !strings.HasSuffix(path, ".go") {
			return nil
		}
		layer, err := layerOf(root, path)
		if err != nil || layer == "" {
			return err
		}
		banned := forbidden[layer]
		if len(banned) == 0 {
			return nil
		}
		file, err := parser.ParseFile(token.NewFileSet(), path, nil, parser.ImportsOnly)
		if err != nil {
			return fmt.Errorf("parse %s: %w", path, err)
		}
		for _, imp := range file.Imports {
			importPath, err := strconv.Unquote(imp.Path.Value)
			if err != nil {
				return err
			}
			for _, layerName := range banned {
				if importPath == module+"/internal/"+layerName ||
					importPath == module+"/cmd" ||
					strings.HasPrefix(importPath, module+"/cmd/") {
					rel, _ := filepath.Rel(root, path)
					violations = append(violations,
						fmt.Sprintf("%s (%s) imports %s", filepath.ToSlash(rel), layer, importPath))
				}
			}
		}
		return nil
	})
	if err != nil {
		t.Fatalf("walk module: %v", err)
	}
	if len(violations) > 0 {
		t.Fatalf("Layering violations:\n%s", strings.Join(violations, "\n"))
	}
}
