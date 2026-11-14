package com.example.{{PackageName}};

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import org.junit.jupiter.api.Test;

// The declared public surface, checked mechanically: adding or
// removing a public method without updating this expectation fails
// the build, so every surface change is a conscious act. Evolution
// against the last RELEASED version is checked separately in CI
// (japicmp job in .github/workflows/ci.yml).
class PublicApiSurfaceTest {

  @Test
  void publicSurfaceIsExactlyTheDeclaredApi() {
    Set<String> methods =
        Stream.of(TextTransforms.class.getDeclaredMethods())
            .filter(m -> Modifier.isPublic(m.getModifiers()))
            .map(PublicApiSurfaceTest::signature)
            .collect(Collectors.toSet());
    assertEquals(Set.of("slugify/1", "truncate/2", "truncate/3"), methods);
  }

  private static String signature(Method method) {
    return method.getName() + "/" + method.getParameterCount();
  }
}
