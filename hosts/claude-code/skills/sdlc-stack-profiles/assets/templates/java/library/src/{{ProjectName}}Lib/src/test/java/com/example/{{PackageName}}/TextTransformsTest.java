package com.example.{{PackageName}};

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import org.junit.jupiter.api.Test;

// Black-box tests: they use only the public API, exactly like a
// consumer. Nothing here reaches into package-private internals.
class TextTransformsTest {

  @Test
  void slugifyLowercasesAndHyphenates() {
    assertEquals("hello-world", TextTransforms.slugify("Hello, World!"));
  }

  @Test
  void slugifyFoldsAccentsToAscii() {
    assertEquals("creme-brulee", TextTransforms.slugify("Crème brûlée"));
  }

  @Test
  void slugifyCollapsesSeparatorRuns() {
    assertEquals("already-slugged", TextTransforms.slugify("  --Already--Slugged--  "));
  }

  @Test
  void slugifyOfBlankIsEmpty() {
    assertEquals("", TextTransforms.slugify("   "));
  }

  @Test
  void truncateReturnsFittingTextUnchanged() {
    assertEquals("short", TextTransforms.truncate("short", 10));
  }

  @Test
  void truncateCutsIncludingTheEllipsis() {
    assertEquals("hello w…", TextTransforms.truncate("hello world", 8));
  }

  @Test
  void truncateRejectsNegativeLimit() {
    assertThrows(IllegalArgumentException.class, () -> TextTransforms.truncate("abc", -1));
  }
}
