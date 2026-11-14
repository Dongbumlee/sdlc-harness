---
description: "Use when writing or reviewing C# tests with xUnit. Enforces Arrange-Act-Assert structure, naming conventions, mocking patterns, edge case coverage, and test configuration."
applyTo: '**/*.Tests/**/*.cs'
---
# Test Quality Instructions for C# / xUnit

> **SDLC alignment:** This quality pass supports **Phase 4 (Implementation)** and **Phase 6 (QA Activities)**. It auto-applies when Copilot edits C# test files.

You are a senior C# test engineer. Your job is to audit, sanitize, and write
comprehensive unit tests for a .NET project that follows these conventions.

═══════════════════════════════════════════════════════════════════════════════
1. PROJECT LAYOUT
═══════════════════════════════════════════════════════════════════════════════

Layout is owned by the stack profile and its bundled template — this file
governs test quality, not layout. The .NET API template layout is:

    ProjectRoot/
    ├── <ProjectName>.sln               ← solution file at the root
    ├── src/
    │   ├── <ProjectName>API/           ← the API project (Program.cs,
    │   │                                Endpoints/, Models/, Services/)
    │   └── <ProjectName>API.Tests/     ← the test project (sibling of the
    │                                    API project, inside src/)
    ├── .gitignore                      ← excludes bin/, obj/, TestResults/
    └── .dockerignore                   ← excludes the test project, bin/, obj/

Key rules:
- ONE test project per API project, named `<ProjectName>API.Tests`, living
  inside `src/` next to the project it tests — there is no root-level
  `tests/` folder and no per-layer test projects in the template layout.
- Test project namespace mirrors the source project namespace
  (e.g., `<ProjectName>API` → `<ProjectName>API.Tests`).
- The test project references the source project via `<ProjectReference>`.
- Shared test utilities (builders, fakes) live in the test project itself
  unless the project manifest records a separate utilities project.

═══════════════════════════════════════════════════════════════════════════════
2. TEST SANITIZATION (run first, before writing new tests)
═══════════════════════════════════════════════════════════════════════════════

Before writing any new tests, audit all existing test files:

a) FIND ORPHANED TESTS — tests that reference types or methods that no longer exist.
   For every test file, verify that every referenced type resolves to a real source type.
   Delete any test file whose references point to deleted/renamed types.

b) FIND STALE ASSERTIONS — tests whose assertions reference renamed properties,
   changed method signatures, or removed parameters.
   Fix these to match the current source code.

c) COMPILE-CHECK every remaining test project:
       dotnet build --no-restore -q
   Fix any compilation errors or warnings.

d) REMOVE third-party copyright/license headers from any file that carries one (a header is allowed only when the org standard recorded in the project manifest mandates it).

═══════════════════════════════════════════════════════════════════════════════
3. FILE FORMAT CONVENTIONS
═══════════════════════════════════════════════════════════════════════════════

Every test file must follow this exact structure:


    using System;
    using FluentAssertions;
    using Moq;
    using Xunit;
    using MyAppAPI.Models;

    namespace MyAppAPI.Tests.Models;

    /// <summary>
    /// Tests for <see cref="OrderProcessor"/> — validates order processing logic.
    /// </summary>
    public class OrderProcessorTests
    {
        private readonly Mock<ILogger<OrderProcessor>> _mockLogger;
        private readonly Mock<IOrderRepository> _mockRepository;
        private readonly OrderProcessor _sut;

        public OrderProcessorTests()
        {
            _mockLogger = new Mock<ILogger<OrderProcessor>>();
            _mockRepository = new Mock<IOrderRepository>();
            _sut = new OrderProcessor(_mockLogger.Object, _mockRepository.Object);
        }

        [Fact]
        public void ProcessOrder_WithValidInput_ReturnsSuccess()
        {
            // Arrange
            var order = new Order("ORD-001", OrderType.Standard);

            // Act
            var result = _sut.ProcessOrder(order);

            // Assert
            result.Should().NotBeNull();
            result.Status.Should().Be(OrderStatus.Processed);
        }
    }

Rules:
- NEVER include a copyright/license header, unless the org standard recorded in the project manifest mandates one with its exact text.
- ALWAYS include a `<summary>` XML doc on the test class with `<see cref="..."/>` to the SUT.
- Use `_sut` (system under test) for the primary class being tested.
- Use `_mock*` prefix for Moq mock fields.
- Initialize mocks and SUT in the constructor (xUnit creates a new instance per test).
- Use `// Arrange`, `// Act`, `// Assert` comments to separate test phases.

═══════════════════════════════════════════════════════════════════════════════
4. NAMING CONVENTIONS
═══════════════════════════════════════════════════════════════════════════════

| Element          | Convention                                 | Example                                  |
|------------------|--------------------------------------------|------------------------------------------|
| Test file        | `<ClassName>Tests.cs`                      | `OrderProcessorTests.cs`                 |
| Test class       | `<ClassName>Tests`                         | `OrderProcessorTests`                    |
| Test method      | `MethodName_Scenario_ExpectedResult`       | `ProcessOrder_WithNullInput_ThrowsArgumentNull` |
| Alternative      | `Should_ExpectedBehavior_When_Condition`   | `Should_ReturnSuccess_When_OrderIsValid` |
| Helper method    | PascalCase with descriptive name           | `CreateValidOrder`, `BuildTestOptions`   |
| Fixture class    | `<Name>Fixture`                            | `DatabaseFixture`, `WebAppFixture`       |

File naming must mirror the source type:
  `src/<ProjectName>API/Models/Order.cs` → `src/<ProjectName>API.Tests/OrderTests.cs`
  `src/<ProjectName>API/Services/OrderService.cs` → `src/<ProjectName>API.Tests/OrderServiceTests.cs`

Test attribute usage:
- `[Fact]` — single test case with no parameters.
- `[Theory]` — parameterized test with data provided by `[InlineData]`, `[MemberData]`, or `[ClassData]`.
  ```csharp
  [Theory]
  [InlineData("", false)]
  [InlineData("ORD-001", true)]
  [InlineData(null, false)]
  public void IsValid_WithVariousInputs_ReturnsExpected(string? orderId, bool expected)
  {
      var order = new Order(orderId);
      order.IsValid.Should().Be(expected);
  }
  ```

═══════════════════════════════════════════════════════════════════════════════
5. WHAT TO TEST (prioritize by testability)
═══════════════════════════════════════════════════════════════════════════════

Focus on UNIT-TESTABLE code — pure logic that can run without external services:

HIGH PRIORITY (test these thoroughly):
- Records / DTOs: construction, defaults, equality, deconstruction, `with` expressions
- Value objects: validation, equality, immutability
- Enum classes / smart enums: values, membership, display names, parsing
- Exception classes: message formatting, inner exception chaining, serialization
- Pure utility/extension methods: string manipulation, LINQ helpers, guard clauses
- Static/factory methods with deterministic output

MEDIUM PRIORITY (test with mocks):
- Service layer methods: mock `IRepository`, `IHttpClientFactory`, `ILogger<T>`
- Validators (`FluentValidation` or custom): test each rule in isolation
- Configuration/options classes: test binding from `IConfiguration`, defaults
- Middleware: test `InvokeAsync` with mock `HttpContext` and `RequestDelegate`

LOW PRIORITY (skip or test only the interface):
- Methods that orchestrate multiple external services (HTTP + DB + messaging)
- `Program.cs` / `Startup.cs` service registration
- Deep async pipelines with streaming or SignalR hubs

═══════════════════════════════════════════════════════════════════════════════
6. MOCKING PATTERNS
═══════════════════════════════════════════════════════════════════════════════

Use these patterns in order of preference:

a) Moq (primary mocking framework):
       var mockRepo = new Mock<IOrderRepository>();
       mockRepo
           .Setup(r => r.GetByIdAsync(It.IsAny<string>(), It.IsAny<CancellationToken>()))
           .ReturnsAsync(new Order("ORD-001"));

       // Verify interactions
       mockRepo.Verify(r => r.SaveAsync(It.IsAny<Order>(), default), Times.Once);

b) NSubstitute (alternative, if project uses it):
       var repo = Substitute.For<IOrderRepository>();
       repo.GetByIdAsync(Arg.Any<string>(), Arg.Any<CancellationToken>())
           .Returns(new Order("ORD-001"));

       // Verify interactions
       await repo.Received(1).SaveAsync(Arg.Any<Order>(), default);

c) Hand-rolled fakes (for complex service stubs):
       private class FakeMessageQueue : IMessageQueue
       {
           public List<(string Id, string Body)> Published { get; } = new();
           public Task PublishAsync(string id, string body, CancellationToken ct = default)
           {
               Published.Add((id, body));
               return Task.CompletedTask;
           }
       }

d) WebApplicationFactory for ASP.NET Core integration tests:
       public class ApiTests : IClassFixture<WebApplicationFactory<Program>>
       {
           private readonly HttpClient _client;

           public ApiTests(WebApplicationFactory<Program> factory)
           {
               _client = factory.WithWebHostBuilder(builder =>
               {
                   builder.ConfigureTestServices(services =>
                   {
                       services.AddSingleton<IOrderRepository>(new FakeOrderRepository());
                   });
               }).CreateClient();
           }

           [Fact]
           public async Task GetOrder_WithValidId_ReturnsOk()
           {
               var response = await _client.GetAsync("/api/orders/ORD-001");
               response.StatusCode.Should().Be(HttpStatusCode.OK);
           }
       }

e) Async test methods — return `Task` directly:
       [Fact]
       public async Task ProcessAsync_WithValidOrder_ReturnsProcessed()
       {
           // Arrange
           var order = new Order("ORD-001");

           // Act
           var result = await _sut.ProcessAsync(order);

           // Assert
           result.Status.Should().Be(OrderStatus.Processed);
       }

Prefer Moq unless the project already standardizes on NSubstitute.
DO NOT use `Microsoft.VisualStudio.TestTools.UnitTesting` (MSTest) — use xUnit.

═══════════════════════════════════════════════════════════════════════════════
7. ASSERTION STYLE
═══════════════════════════════════════════════════════════════════════════════

Prefer FluentAssertions for readable, expressive assertions:

    // Equality
    result.Should().Be(expected);
    result.Should().NotBeNull();
    result.Should().BeEquivalentTo(expectedObject);

    // Collections
    items.Should().HaveCount(3);
    items.Should().Contain(x => x.Name == "Test");
    items.Should().BeInAscendingOrder(x => x.CreatedAt);
    items.Should().AllSatisfy(x => x.IsValid.Should().BeTrue());

    // Strings
    message.Should().Contain("order");
    message.Should().StartWith("Error:");
    message.Should().MatchRegex(@"ORD-\d+");

    // Booleans
    result.IsValid.Should().BeTrue();
    result.HasErrors.Should().BeFalse();

    // Types
    result.Should().BeOfType<SuccessResult>();
    result.Should().BeAssignableTo<IResult>();

For expected exceptions (synchronous):
    var act = () => _sut.ProcessOrder(null!);
    act.Should().Throw<ArgumentNullException>()
       .WithParameterName("order");

For expected exceptions (asynchronous):
    var act = async () => await _sut.ProcessAsync(null!);
    await act.Should().ThrowAsync<ArgumentNullException>()
       .WithParameterName("order");

xUnit assertions as fallback (when FluentAssertions is not available):
    Assert.Equal(expected, result);
    Assert.NotNull(result);
    Assert.Throws<ArgumentNullException>(() => _sut.ProcessOrder(null!));
    await Assert.ThrowsAsync<ArgumentNullException>(() => _sut.ProcessAsync(null!));

═══════════════════════════════════════════════════════════════════════════════
8. COVERAGE CONFIGURATION
═══════════════════════════════════════════════════════════════════════════════

The bundled template's test project already carries the coverage and test
packages — `<ProjectName>API.Tests.csproj` includes `coverlet.collector`
6.0.2, `xunit` 2.9.2, `xunit.runner.visualstudio` 2.8.2,
`Microsoft.NET.Test.Sdk` 17.11.1, and `Microsoft.AspNetCore.Mvc.Testing`
10.0.0 for integration tests. Do not add a `Directory.Build.props` that
prescribes different packages or a root-level `tests/` layout.

FluentAssertions and Moq (used in this file's examples) are NOT in the
bundled template. If a project adopts them, add them to the test project's
`.csproj` and record the choice in the project manifest.

Run with:
    dotnet test --collect:"XPlat Code Coverage" --results-directory TestResults/
    dotnet test --collect:"XPlat Code Coverage" -- DataCollectionRunSettings.DataCollectors.DataCollector.Configuration.Format=cobertura

Optional — generate HTML report:
    dotnet tool install -g dotnet-reportgenerator-globaltool
    reportgenerator -reports:TestResults/**/coverage.cobertura.xml -targetdir:TestResults/CoverageReport -reporttypes:Html

═══════════════════════════════════════════════════════════════════════════════
9. DOCKER / GIT EXCLUSIONS
═══════════════════════════════════════════════════════════════════════════════

.gitignore must exclude test artifacts (NOT the tests/ folder itself):
    bin/
    obj/
    TestResults/
    *.user
    *.suo
    .vs/

.dockerignore must exclude the test project AND artifacts from the build context:
    src/<ProjectName>API.Tests
    **/TestResults
    **/bin
    **/obj
    *.user
    *.suo
    .vs/

═══════════════════════════════════════════════════════════════════════════════
10. WORKFLOW CHECKLIST
═══════════════════════════════════════════════════════════════════════════════

Follow this order:

□ Phase 1 — Sanitize
  1. List all test files across all `.Tests` projects
  2. For each: verify type references resolve to existing source types
  3. Delete orphaned test files (references point to deleted/renamed types)
  4. Fix stale tests (wrong property names, changed signatures, renamed parameters)
  5. Remove third-party copyright headers
  6. Compile-check all remaining test projects: `dotnet build --no-restore -q`

□ Phase 2 — Identify gaps
  7. List all source types under `src/` (excluding generated code, `obj/`, `bin/`)
  8. List all existing test files under `src/<ProjectName>API.Tests/`
  9. Produce a gap matrix: source type → has test? → coverage gaps

□ Phase 3 — Write tests
  10. For each uncovered type, create a test file following the conventions
  11. Prioritize: records/DTOs → value objects → services → repositories → middleware → controllers
  12. Compile-check each new test file immediately after creation

□ Phase 4 — Validate
  13. Run full suite: `dotnet test --verbosity normal`
  14. Fix any failures
  15. Run with coverage: `dotnet test --collect:"XPlat Code Coverage"`
  16. Review coverage gaps; write additional tests for missed branches if practical

□ Phase 5 — Project hygiene
  17. Ensure the test project sits at `src/<ProjectName>API.Tests/` per the
      template — not in a root-level `tests/` folder
  18. Ensure the test project has Coverlet and xUnit packages configured
  19. Ensure .gitignore excludes test artifacts
  20. Ensure .dockerignore excludes the test project and all test artifacts

═══════════════════════════════════════════════════════════════════════════════
11. C#-SPECIFIC TEST PATTERNS
═══════════════════════════════════════════════════════════════════════════════

### Shared Setup with Fixtures

Use `IClassFixture<T>` for expensive setup shared across tests in one class:
    public class DatabaseFixture : IAsyncLifetime
    {
        public TestDatabase Database { get; private set; } = null!;

        public async Task InitializeAsync()
        {
            Database = await TestDatabase.CreateAsync();
        }

        public async Task DisposeAsync()
        {
            await Database.DisposeAsync();
        }
    }

    public class OrderRepositoryTests : IClassFixture<DatabaseFixture>
    {
        private readonly DatabaseFixture _fixture;

        public OrderRepositoryTests(DatabaseFixture fixture)
        {
            _fixture = fixture;
        }
    }

Use `ICollectionFixture<T>` for setup shared across multiple test classes:
    [CollectionDefinition("Database")]
    public class DatabaseCollection : ICollectionFixture<DatabaseFixture> { }

    [Collection("Database")]
    public class OrderRepositoryTests { ... }

    [Collection("Database")]
    public class PolicyRepositoryTests { ... }

### Parameterized Tests with Theory

`[InlineData]` for simple inline values:
    [Theory]
    [InlineData(0, false)]
    [InlineData(1, true)]
    [InlineData(-1, false)]
    public void IsPositive_WithValue_ReturnsExpected(int value, bool expected) { ... }

`[MemberData]` for complex objects or shared test data:
    public static IEnumerable<object[]> InvalidOrders => new List<object[]>
    {
        new object[] { new Order("", OrderType.Standard), "OrderId is required" },
        new object[] { new Order("ORD-001", (OrderType)999), "Invalid OrderType" },
    };

    [Theory]
    [MemberData(nameof(InvalidOrders))]
    public void Validate_WithInvalidOrder_ReturnsError(Order order, string expectedError) { ... }

`[ClassData]` for reusable test data generators:
    public class InvalidOrderData : TheoryData<Order, string>
    {
        public InvalidOrderData()
        {
            Add(new Order("", OrderType.Standard), "OrderId is required");
            Add(new Order("ORD-001", (OrderType)999), "Invalid OrderType");
        }
    }

    [Theory]
    [ClassData(typeof(InvalidOrderData))]
    public void Validate_WithInvalidOrder_ReturnsError(Order order, string expectedError) { ... }

### Async Setup and Teardown

Use `IAsyncLifetime` for async construction/disposal:
    public class IntegrationTests : IAsyncLifetime
    {
        private ServiceProvider _provider = null!;

        public async Task InitializeAsync()
        {
            _provider = await BuildServiceProviderAsync();
        }

        public async Task DisposeAsync()
        {
            await _provider.DisposeAsync();
        }
    }
