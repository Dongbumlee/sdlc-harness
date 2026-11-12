package com.example.{{PackageName}};

import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.fail;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Stream;
import org.junit.jupiter.api.Test;

/**
 * Mechanical layering checks for the profile's dependency direction (web → service/config/model;
 * service → model; config and model depend on nothing internal), enforced by scanning the main
 * sources' package and import statements. No extra dependencies: this runs as part of the normal
 * test suite, so a layering violation fails the build instead of waiting for a reviewer to notice
 * it.
 */
class ArchitectureTest {

  private static final String BASE_PACKAGE = "com.example.{{PackageName}}";
  private static final Pattern PACKAGE_RE = Pattern.compile("(?m)^package\\s+([\\w.]+);");
  private static final Pattern IMPORT_RE =
      Pattern.compile("(?m)^import\\s+(?:static\\s+)?([\\w.]+);");

  private record SourceFile(Path path, String packageName, List<String> imports) {}

  private static List<SourceFile> mainSources() {
    Path root = Path.of("src/main/java");
    if (!Files.isDirectory(root)) {
      fail("src/main/java not found — tests must run from the project directory");
    }
    List<SourceFile> sources = new ArrayList<>();
    try (Stream<Path> walk = Files.walk(root)) {
      walk.filter(p -> p.toString().endsWith(".java"))
          .forEach(
              p -> {
                try {
                  String text = Files.readString(p);
                  Matcher pkg = PACKAGE_RE.matcher(text);
                  String packageName = pkg.find() ? pkg.group(1) : "";
                  List<String> imports = new ArrayList<>();
                  Matcher imp = IMPORT_RE.matcher(text);
                  while (imp.find()) {
                    imports.add(imp.group(1));
                  }
                  sources.add(new SourceFile(p, packageName, imports));
                } catch (IOException e) {
                  throw new UncheckedIOException(e);
                }
              });
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    }
    return sources;
  }

  private static String layerOf(String packageName) {
    if (packageName.equals(BASE_PACKAGE)) {
      return "root";
    }
    String rest = packageName.substring(BASE_PACKAGE.length() + 1);
    return rest.split("\\.")[0];
  }

  @Test
  void layeringDirectionHolds() {
    List<SourceFile> sources = mainSources();
    assertTrue(sources.size() >= 5, "expected the sample slice sources to be present");
    List<String> violations = new ArrayList<>();
    for (SourceFile source : sources) {
      String layer = layerOf(source.packageName());
      for (String imported : source.imports()) {
        if (!imported.startsWith(BASE_PACKAGE)) {
          continue;
        }
        String importedLayer = layerOf(imported.substring(0, imported.lastIndexOf('.')));
        switch (layer) {
          case "model" -> {
            if (!importedLayer.equals("model")) {
              violations.add(source.path() + ": model must not depend on " + importedLayer);
            }
          }
          case "config" -> {
            if (!importedLayer.equals("config")) {
              violations.add(source.path() + ": config must not depend on " + importedLayer);
            }
          }
          case "service" -> {
            if (importedLayer.equals("web") || importedLayer.equals("config")) {
              violations.add(source.path() + ": service must not depend on " + importedLayer);
            }
          }
          default -> {
            // web and the composition root may reference the layers below them.
          }
        }
      }
    }
    assertTrue(violations.isEmpty(), () -> "layering violations: " + violations);
  }
}
