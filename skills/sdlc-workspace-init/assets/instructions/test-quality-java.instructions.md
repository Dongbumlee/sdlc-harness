---
description: "Use when writing or reviewing Java tests with JUnit 5. Enforces Arrange-Act-Assert structure, naming conventions, mocking patterns, edge case coverage, and test configuration."
applyTo: '**/src/test/**/*.java'
---
# Test Quality Instructions for Java

> **SDLC alignment:** This quality pass supports **Phase 4 (Implementation)** and **Phase 6 (QA Activities)**
> as defined in `.github/SDLC-with-Copilot-and-Azure.md`. It auto-applies when Copilot edits Java test files.

You are a senior Java test engineer. Your job is to audit, sanitize, and write
comprehensive unit tests for a Java project that follows these conventions.

═══════════════════════════════════════════════════════════════════════════════
1. PROJECT LAYOUT
═══════════════════════════════════════════════════════════════════════════════

The project uses the Maven/Gradle standard directory structure:

    ProjectRoot/
    ├── src/
    │   ├── main/
    │   │   ├── java/              ← production code
    │   │   │   └── com/example/
    │   │   │       ├── controller/
    │   │   │       ├── service/
    │   │   │       ├── repository/
    │   │   │       ├── model/
    │   │   │       ├── config/
    │   │   │       └── util/
    │   │   └── resources/         ← application.yml, SQL migrations, etc.
    │   └── test/
    │       ├── java/              ← all test code lives here
    │       │   └── com/example/
    │       │       ├── controller/
    │       │       ├── service/
    │       │       ├── repository/
    │       │       ├── model/
    │       │       └── util/
    │       └── resources/         ← test-specific config (application-test.yml)
    ├── pom.xml / build.gradle     ← build config + test dependencies
    ├── .gitignore
    └── .dockerignore

Key rules:
- Test package structure mirrors production code exactly
  (e.g., `com.example.service.UserService` → `com.example.service.UserServiceTest`).
- Test resources go in `src/test/resources/`, not alongside production resources.
- Integration tests may live in a separate `src/integration-test/` source set or be annotated with `@Tag("integration")`.

═══════════════════════════════════════════════════════════════════════════════
2. TEST SANITIZATION (run first, before writing new tests)
═══════════════════════════════════════════════════════════════════════════════

Before writing any new tests, audit all existing test files:

a) FIND ORPHANED TESTS — tests that reference classes or methods that no longer exist.
   For every test file, verify that every import resolves to a real source class.
   Delete any test file whose imports reference deleted/renamed classes.

b) FIND STALE ASSERTIONS — tests whose assertions reference renamed fields,
   changed method signatures, or removed parameters.
   Fix these to match the current source code.

c) COMPILE-CHECK every remaining test file:
   - **Maven:** `mvn compile test-compile -q`
   - **Gradle:** `./gradlew compileTestJava --quiet`
   Fix any compilation errors or import failures.

d) ADD MISSING COPYRIGHT HEADERS to any file that lacks one.

═══════════════════════════════════════════════════════════════════════════════
3. FILE FORMAT CONVENTIONS
═══════════════════════════════════════════════════════════════════════════════

Every test file must follow this exact structure:

    /*
     * Copyright (c) Microsoft Corporation.
     * Licensed under the MIT License.
     */

    package com.example.service;

    // ── JUnit 5 imports ────────────────────────────────────────────────
    import org.junit.jupiter.api.BeforeEach;
    import org.junit.jupiter.api.DisplayName;
    import org.junit.jupiter.api.Nested;
    import org.junit.jupiter.api.Test;
    import org.junit.jupiter.params.ParameterizedTest;
    import org.junit.jupiter.params.provider.CsvSource;

    // ── Mockito imports ────────────────────────────────────────────────
    import org.mockito.InjectMocks;
    import org.mockito.Mock;
    import org.mockito.junit.jupiter.MockitoExtension;
    import static org.mockito.Mockito.*;

    // ── AssertJ imports ────────────────────────────────────────────────
    import static org.assertj.core.api.Assertions.*;

    // ── Application imports ────────────────────────────────────────────
    import com.example.service.UserService;
    import com.example.model.User;

    @ExtendWith(MockitoExtension.class)
    class UserServiceTest {

        @Mock
        private UserRepository userRepository;

        @InjectMocks
        private UserService userService;

        @Test
        @DisplayName("should return user when valid ID is provided")
        void shouldReturnUserWhenValidIdProvided() {
            // Arrange
            // Act
            // Assert
        }
    }

Rules:
- ALWAYS include the copyright block comment header.
- ALWAYS include the package declaration matching the class under test.
- Organize imports in sections: JUnit 5, Mockito, AssertJ, application.
- Use `@ExtendWith(MockitoExtension.class)` instead of the deprecated `@RunWith`.
- Import only what you use — no wildcard imports except for static assertion/mock methods.

═══════════════════════════════════════════════════════════════════════════════
4. NAMING CONVENTIONS
═══════════════════════════════════════════════════════════════════════════════

| Element            | Convention                                    | Example                                        |
|--------------------|-----------------------------------------------|------------------------------------------------|
| Test file          | `<ClassName>Test.java`                        | `UserServiceTest.java`                         |
| Test class         | PascalCase + `Test` suffix                    | `UserServiceTest`                              |
| Test method        | camelCase descriptive name                    | `shouldReturnUserWhenValidIdProvided()`         |
| Test method (alt)  | `test_<method>_<scenario>_<expected>`         | `test_findById_nullId_throwsException()`       |
| Nested class       | `@Nested` + describes scenario group          | `class WhenUserExists { ... }`                 |
| Helper method      | `_prefixed` or `create`/`build` prefix        | `createSampleUser()`, `buildRequest()`         |
| Display name       | Sentence describing behavior                  | `@DisplayName("should throw when ID is null")` |

File naming must mirror the source class:
  `src/main/java/com/example/service/UserService.java` →
  `src/test/java/com/example/service/UserServiceTest.java`

Use `@DisplayName` on every test method for readable test reports.

═══════════════════════════════════════════════════════════════════════════════
5. WHAT TO TEST (prioritize by testability)
═══════════════════════════════════════════════════════════════════════════════

Focus on UNIT-TESTABLE code — pure logic that can run without external services:

HIGH PRIORITY (test these thoroughly):
- Records, DTOs, and POJOs: construction, defaults, `equals()`/`hashCode()`, serialization
- Enum classes: values, `valueOf()`, custom methods, display names
- Exception classes: message formatting, cause chaining, custom fields
- Pure utility functions: string manipulation, date parsing, validation helpers
- Static factory methods and builders with deterministic output
- Mapper/converter classes (MapStruct, manual mapping)

MEDIUM PRIORITY (test with mocks):
- Service-layer methods: mock repositories and external clients
- Repository custom queries: use `@DataJpaTest` with embedded H2/Testcontainers
- Controller endpoints: use `@WebMvcTest` with `MockMvc`
- Configuration classes: verify bean creation and property binding
- Event listeners and async handlers: mock event publishers, verify invocations

LOW PRIORITY (skip or test only the interface):
- Methods that orchestrate multiple external services (HTTP + DB + messaging)
- Main application class (`@SpringBootApplication`)
- Deep async orchestration with reactive streams

═══════════════════════════════════════════════════════════════════════════════
6. MOCKING PATTERNS
═══════════════════════════════════════════════════════════════════════════════

Use these patterns in order of preference:

a) Mockito annotations (for unit tests):
       @Mock
       private UserRepository userRepository;

       @InjectMocks
       private UserService userService;

       @Test
       void shouldFindUser() {
           when(userRepository.findById(1L)).thenReturn(Optional.of(sampleUser));

           User result = userService.findById(1L);

           assertThat(result).isEqualTo(sampleUser);
           verify(userRepository).findById(1L);
       }

b) ArgumentCaptor (for verifying complex arguments):
       @Captor
       private ArgumentCaptor<User> userCaptor;

       @Test
       void shouldSaveUserWithCorrectFields() {
           userService.createUser("Alice", "alice@example.com");

           verify(userRepository).save(userCaptor.capture());
           User saved = userCaptor.getValue();
           assertThat(saved.getName()).isEqualTo("Alice");
           assertThat(saved.getEmail()).isEqualTo("alice@example.com");
       }

c) @MockBean (for Spring Boot integration tests):
       @WebMvcTest(UserController.class)
       class UserControllerTest {

           @Autowired
           private MockMvc mockMvc;

           @MockBean
           private UserService userService;

           @Test
           void shouldReturnUser() throws Exception {
               when(userService.findById(1L)).thenReturn(sampleUser);

               mockMvc.perform(get("/api/users/1"))
                   .andExpect(status().isOk())
                   .andExpect(jsonPath("$.name").value("Alice"));
           }
       }

d) Hand-rolled fakes (for complex collaborators):
       class FakeEmailSender implements EmailSender {
           private final List<Email> sent = new ArrayList<>();

           @Override
           public void send(Email email) {
               sent.add(email);
           }

           public List<Email> getSentEmails() {
               return Collections.unmodifiableList(sent);
           }
       }

e) Spy (when you need partial mocking — use sparingly):
       @Spy
       private UserService userService;

DO NOT use PowerMock or mock static methods unless absolutely unavoidable.
Prefer refactoring to inject dependencies over mocking static calls.

═══════════════════════════════════════════════════════════════════════════════
7. ASSERTION STYLE
═══════════════════════════════════════════════════════════════════════════════

Prefer AssertJ for fluent, readable assertions:

    // Equality
    assertThat(result).isEqualTo(expected);
    assertThat(result).isNotNull();

    // Collections
    assertThat(users).hasSize(3);
    assertThat(users).extracting(User::getName).containsExactly("Alice", "Bob", "Carol");
    assertThat(users).isEmpty();

    // Strings
    assertThat(message).contains("error");
    assertThat(message).startsWith("Failed to");

    // Exceptions
    assertThatThrownBy(() -> service.findById(null))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessageContaining("must not be null");

    // Soft assertions (multiple checks without short-circuiting)
    SoftAssertions.assertSoftly(softly -> {
        softly.assertThat(user.getName()).isEqualTo("Alice");
        softly.assertThat(user.getEmail()).isEqualTo("alice@example.com");
        softly.assertThat(user.isActive()).isTrue();
    });

JUnit 5 assertions as fallback (when AssertJ is not available):

    assertEquals(expected, result);
    assertNotNull(result);
    assertTrue(condition);
    assertThrows(IllegalArgumentException.class, () -> service.findById(null));

═══════════════════════════════════════════════════════════════════════════════
8. COVERAGE CONFIGURATION
═══════════════════════════════════════════════════════════════════════════════

**Maven (JaCoCo plugin in `pom.xml`):**

    <plugin>
        <groupId>org.jacoco</groupId>
        <artifactId>jacoco-maven-plugin</artifactId>
        <version>${jacoco.version}</version>
        <executions>
            <execution>
                <goals>
                    <goal>prepare-agent</goal>
                </goals>
            </execution>
            <execution>
                <id>report</id>
                <phase>test</phase>
                <goals>
                    <goal>report</goal>
                </goals>
            </execution>
        </executions>
        <configuration>
            <excludes>
                <exclude>**/config/**</exclude>
                <exclude>**/model/dto/**</exclude>
                <exclude>**/*Application.*</exclude>
            </excludes>
        </configuration>
    </plugin>

Run with: `mvn test jacoco:report`

**Gradle (JaCoCo in `build.gradle`):**

    plugins {
        id 'jacoco'
    }

    jacocoTestReport {
        dependsOn test
        reports {
            xml.required = true
            html.required = true
        }
        afterEvaluate {
            classDirectories.setFrom(files(classDirectories.files.collect {
                fileTree(dir: it, exclude: [
                    '**/config/**',
                    '**/model/dto/**',
                    '**/*Application*'
                ])
            }))
        }
    }

    test {
        useJUnitPlatform()
        finalizedBy jacocoTestReport
    }

Run with: `./gradlew test jacocoTestReport`

═══════════════════════════════════════════════════════════════════════════════
9. DOCKER / GIT EXCLUSIONS
═══════════════════════════════════════════════════════════════════════════════

.gitignore must exclude build artifacts (NOT the test source code itself):
    target/
    build/
    .gradle/
    *.class
    *.jar
    *.war
    jacoco.exec
    .idea/
    *.iml

.dockerignore must exclude tests AND build artifacts from the build context:
    src/test/
    target/
    build/
    .gradle/
    *.class
    jacoco.exec
    .idea/
    *.iml
    .git/

═══════════════════════════════════════════════════════════════════════════════
10. WORKFLOW CHECKLIST
═══════════════════════════════════════════════════════════════════════════════

Follow this order:

□ Phase 1 — Sanitize
  1. List all test files under `src/test/java/`
  2. For each: verify imports resolve to existing source classes
  3. Delete orphaned test files (imports reference deleted/renamed classes)
  4. Fix stale tests (wrong field names, changed signatures, removed methods)
  5. Add missing copyright headers
  6. Compile-check all remaining tests:
     - Maven: `mvn test-compile -q`
     - Gradle: `./gradlew compileTestJava --quiet`

□ Phase 2 — Identify gaps
  7. List all source classes under `src/main/java/` (excluding config, DTOs if trivial)
  8. List all existing test files under `src/test/java/`
  9. Produce a gap matrix: source class → has test? → coverage gaps

□ Phase 3 — Write tests
  10. For each uncovered class, create a test file following the conventions
  11. Prioritize: models/records → utils → services → repositories → controllers
  12. Compile-check each new test file immediately after creation

□ Phase 4 — Validate
  13. Run full suite:
      - Maven: `mvn test -q`
      - Gradle: `./gradlew test --quiet`
  14. Fix any failures
  15. Run with coverage:
      - Maven: `mvn test jacoco:report`
      - Gradle: `./gradlew test jacocoTestReport`
  16. Review coverage gaps; write additional tests for missed branches if practical

□ Phase 5 — Project hygiene
  17. Ensure test package structure mirrors `src/main/java/` package structure
  18. Ensure `pom.xml` / `build.gradle` has JaCoCo and JUnit 5 dependencies
  19. Ensure `.gitignore` excludes `target/`, `build/`, `*.class`, `jacoco.exec`
  20. Ensure `.dockerignore` excludes `src/test/`, `target/`, `build/`, and all build artifacts

## Java-Specific Test Patterns

### Spring Boot Test Slices

Use the narrowest test slice that covers the behavior under test:

| Annotation         | What it loads                        | Use for                              |
|--------------------|--------------------------------------|--------------------------------------|
| `@WebMvcTest`      | Controllers, filters, advice         | REST endpoint tests                  |
| `@DataJpaTest`     | JPA repositories, EntityManager      | Repository / query tests             |
| `@JsonTest`        | Jackson ObjectMapper                 | JSON serialization/deserialization   |
| `@SpringBootTest`  | Full application context             | Integration tests (use sparingly)    |

Prefer `@WebMvcTest` + `@MockBean` over `@SpringBootTest` for controller tests.

### Parameterized Tests

Use `@ParameterizedTest` to avoid duplicating test logic across inputs:

    @ParameterizedTest
    @DisplayName("should validate email format")
    @ValueSource(strings = {"invalid", "no-at-sign", "@missing-local", "spaces in@email.com"})
    void shouldRejectInvalidEmails(String email) {
        assertThatThrownBy(() -> validator.validate(email))
            .isInstanceOf(ValidationException.class);
    }

    @ParameterizedTest
    @DisplayName("should calculate discount correctly")
    @CsvSource({
        "100.00, 10, 90.00",
        "50.00, 25, 37.50",
        "200.00, 0, 200.00"
    })
    void shouldCalculateDiscount(BigDecimal price, int percent, BigDecimal expected) {
        assertThat(calculator.applyDiscount(price, percent)).isEqualByComparingTo(expected);
    }

    @ParameterizedTest
    @DisplayName("should parse date strings")
    @MethodSource("dateProvider")
    void shouldParseDates(String input, LocalDate expected) {
        assertThat(parser.parse(input)).isEqualTo(expected);
    }

    static Stream<Arguments> dateProvider() {
        return Stream.of(
            Arguments.of("2024-01-15", LocalDate.of(2024, 1, 15)),
            Arguments.of("2024-12-31", LocalDate.of(2024, 12, 31))
        );
    }

### Nested Test Classes

Use `@Nested` to group related tests and improve readability:

    @ExtendWith(MockitoExtension.class)
    @DisplayName("UserService")
    class UserServiceTest {

        @Nested
        @DisplayName("when user exists")
        class WhenUserExists {

            @BeforeEach
            void setUp() {
                when(userRepository.findById(1L)).thenReturn(Optional.of(sampleUser));
            }

            @Test
            @DisplayName("should return the user")
            void shouldReturnUser() { ... }

            @Test
            @DisplayName("should not call external API")
            void shouldNotCallExternalApi() { ... }
        }

        @Nested
        @DisplayName("when user does not exist")
        class WhenUserDoesNotExist {

            @Test
            @DisplayName("should throw NotFoundException")
            void shouldThrowNotFoundException() { ... }
        }
    }

### Async Testing

For testing `@Async` methods and `CompletableFuture` results:

    @Test
    @DisplayName("should complete async operation within timeout")
    void shouldCompleteAsyncOperation() throws Exception {
        CompletableFuture<Result> future = asyncService.process(input);

        Result result = future.get(5, TimeUnit.SECONDS);

        assertThat(result).isNotNull();
        assertThat(result.getStatus()).isEqualTo(Status.COMPLETED);
    }

    @Test
    @DisplayName("should handle async failure gracefully")
    void shouldHandleAsyncFailure() {
        CompletableFuture<Result> future = asyncService.processInvalid(badInput);

        assertThatThrownBy(() -> future.get(5, TimeUnit.SECONDS))
            .hasCauseInstanceOf(ProcessingException.class);
    }
