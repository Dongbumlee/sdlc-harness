package com.example.{{PackageName}}.textkit;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

class TextKitTest {

  @ParameterizedTest
  @CsvSource({
    "'Hello, World!', hello-world",
    "'one   two--three', one-two-three",
    "'  padded  ', padded",
    "'Ünïcodé Chars', ünïcodé-chars",
    "'', ''",
  })
  void slugifyCases(String input, String want) {
    assertEquals(want, TextKit.slugify(input));
  }

  @ParameterizedTest
  @CsvSource({
    "'short', 40, short",
    "'a longer sentence', 6, 'a lon…'",
    "'exactly six', 6, 'exact…'",
    "'ab', 1, '…'",
    "'abc', 0, ''",
  })
  void truncateCases(String input, int max, String want) {
    assertEquals(want, TextKit.truncate(input, max));
  }

  @Test
  void truncateLengthNeverExceeds() {
    var result = TextKit.truncate("a longer sentence", 6);
    assertEquals(6, result.length());
  }
}
