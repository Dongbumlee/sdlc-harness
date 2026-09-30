---
description: "Use when writing or reviewing C# tests with xUnit. Enforces Arrange-Act-Assert structure, naming conventions, mocking patterns, edge case coverage, and test configuration."
applyTo: '**/*.Tests/**/*.cs'
---
# Test Quality Instructions for C# / xUnit

> **SDLC alignment:** This quality pass supports **Phase 4 (Implementation)** and **Phase 6 (QA Activities)**
> as defined in `.github/SDLC-with-Copilot-and-Azure.md`. It auto-applies when Copilot edits C# test files.

You are a senior C# test engineer. Your job is to audit, sanitize, and write
comprehensive unit tests for a .NET project that follows these conventions.

═══════════════════════════════════════════════════════════════════════════════
1. PROJECT LAYOUT
═══════════════════════════════════════════════════════════════════════════════

The solution uses a standard .NET structure with separate test projects:

    SolutionRoot/
    ├── src/                              ← production code only
    │   ├── MyApp.Domain/                 ← domain models, entities, value objects
    │   ├── MyApp.Application/            ← use cases, interfaces, DTOs
    │   ├── MyApp.Infrastructure/         ← data access, external services
    │   └── MyApp.Api/                    ← controllers, middleware, startup
    ├── tests/                            ← all test code lives here
    │   ├── MyApp.Domain.Tests/           ← unit tests for Domain
    │   ├── MyApp.Application.Tests/      ← unit tests for Application
    │   ├── MyApp.Infrastructure.Tests/   ← integration tests for Infrastructure
    │   └── MyApp.Api.Tests/              ← API integration tests
    ├── MySolution.sln                    ← solution file references all projects
    ├── Directory.Build.props             ← shared MSBuild properties
    ├── .gitignore                        ← excludes bin/, obj/, TestResults/
    └── .dockerignore                     ← excludes tests/, TestResults/, etc.

Key rules:
- One test project per source project, with `.Tests` suffix.
- Test project namespace mirrors the source project namespace
  (e.g., `MyApp.Domain` → `MyApp.Domain.Tests`).
- Test projects reference the corresponding source project via `<ProjectReference>`.
- Shared test utilities (builders, fakes) go in a `MyApp.TestUtilities` project.

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

d) ADD MISSING COPYRIGHT HEADERS to any file that lacks one.

═══════════════════════════════════════════════════════════════════════════════
3. FILE FORMAT CONVENTIONS
═══════════════════════════════════════════════════════════════════════════════

Every test file must follow this exact structure:

    // Copyright (c) Microsoft Corporation.
    // Licensed under the MIT License.

    using System;
    using FluentAssertions;
    using Moq;
    using Xunit;
    using MyApp.Domain.Models;

    namespace MyApp.Domain.Tests.Models;

    /// <summary>
    /// Tests for <see cref="ClaimProcessor"/> — validates claim processing logic.
    /// </summary>
    public class ClaimProcessorTests
    {
        private readonly Mock<ILogger<ClaimProcessor>> _mockLogger;
        private readonly Mock<IClaimRepository> _mockRepository;
        private readonly ClaimProcessor _sut;

        public ClaimProcessorTests()
        {
            _mockLogger = new Mock<ILogger<ClaimProcessor>>();
            _mockRepository = new Mock<IClaimRepository>();
            _sut = new ClaimProcessor(_mockLogger.Object, _mockRepository.Object);
        }

        [Fact]
        public void ProcessClaim_WithValidInput_ReturnsSuccess()
        {
            // Arrange
            var claim = new Claim("CLM-001", ClaimType.Medical);

            // Act
            var result = _sut.ProcessClaim(claim);

            // Assert
            result.Should().NotBeNull();
            result.Status.Should().Be(ClaimStatus.Processed);
        }
    }

Rules:
- ALWAYS include the 2-line copyright header.
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
| Test file        | `<ClassName>Tests.cs`                      | `ClaimProcessorTests.cs`                 |
| Test class       | `<ClassName>Tests`                         | `ClaimProcessorTests`                    |
| Test method      | `MethodName_Scenario_ExpectedResult`       | `ProcessClaim_WithNullInput_ThrowsArgumentNull` |
| Alternative      | `Should_ExpectedBehavior_When_Condition`   | `Should_ReturnSuccess_When_ClaimIsValid` |
| Helper method    | PascalCase with descriptive name           | `CreateValidClaim`, `BuildTestOptions`   |
| Fixture class    | `<Name>Fixture`                            | `DatabaseFixture`, `WebAppFixture`       |

File naming must mirror the source type:
  `src/MyApp.Domain/Models/Claim.cs` → `tests/MyApp.Domain.Tests/Models/ClaimTests.cs`
  `src/MyApp.Application/Services/ClaimService.cs` → `tests/MyApp.Application.Tests/Services/ClaimServiceTests.cs`

Test attribute usage:
- `[Fact]` — single test case with no parameters.
- `[Theory]` — parameterized test with data provided by `[InlineData]`, `[MemberData]`, or `[ClassData]`.
  ```csharp
  [Theory]
  [InlineData("", false)]
  [InlineData("CLM-001", true)]
  [InlineData(null, false)]
  public void IsValid_WithVariousInputs_ReturnsExpected(string? claimId, bool expected)
  {
      var claim = new Claim(claimId);
      claim.IsValid.Should().Be(expected);
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
       var mockRepo = new Mock<IClaimRepository>();
       mockRepo
           .Setup(r => r.GetByIdAsync(It.IsAny<string>(), It.IsAny<CancellationToken>()))
           .ReturnsAsync(new Claim("CLM-001"));

       // Verify interactions
       mockRepo.Verify(r => r.SaveAsync(It.IsAny<Claim>(), default), Times.Once);

b) NSubstitute (alternative, if project uses it):
       var repo = Substitute.For<IClaimRepository>();
       repo.GetByIdAsync(Arg.Any<string>(), Arg.Any<CancellationToken>())
           .Returns(new Claim("CLM-001"));

       // Verify interactions
       await repo.Received(1).SaveAsync(Arg.Any<Claim>(), default);

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
                       services.AddSingleton<IClaimRepository>(new FakeClaimRepository());
                   });
               }).CreateClient();
           }

           [Fact]
           public async Task GetClaim_WithValidId_ReturnsOk()
           {
               var response = await _client.GetAsync("/api/claims/CLM-001");
               response.StatusCode.Should().Be(HttpStatusCode.OK);
           }
       }

e) Async test methods — return `Task` directly:
       [Fact]
       public async Task ProcessAsync_WithValidClaim_ReturnsProcessed()
       {
           // Arrange
           var claim = new Claim("CLM-001");

           // Act
           var result = await _sut.ProcessAsync(claim);

           // Assert
           result.Status.Should().Be(ClaimStatus.Processed);
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
    message.Should().Contain("claim");
    message.Should().StartWith("Error:");
    message.Should().MatchRegex(@"CLM-\d+");

    // Booleans
    result.IsValid.Should().BeTrue();
    result.HasErrors.Should().BeFalse();

    // Types
    result.Should().BeOfType<SuccessResult>();
    result.Should().BeAssignableTo<IResult>();

For expected exceptions (synchronous):
    var act = () => _sut.ProcessClaim(null!);
    act.Should().Throw<ArgumentNullException>()
       .WithParameterName("claim");

For expected exceptions (asynchronous):
    var act = async () => await _sut.ProcessAsync(null!);
    await act.Should().ThrowAsync<ArgumentNullException>()
       .WithParameterName("claim");

xUnit assertions as fallback (when FluentAssertions is not available):
    Assert.Equal(expected, result);
    Assert.NotNull(result);
    Assert.Throws<ArgumentNullException>(() => _sut.ProcessClaim(null!));
    await Assert.ThrowsAsync<ArgumentNullException>(() => _sut.ProcessAsync(null!));

═══════════════════════════════════════════════════════════════════════════════
8. COVERAGE CONFIGURATION
═══════════════════════════════════════════════════════════════════════════════

Test projects must include Coverlet for code coverage. Add to each test `.csproj`:

    <ItemGroup>
      <PackageReference Include="coverlet.collector" Version="6.*">
        <PrivateAssets>all</PrivateAssets>
        <IncludeAssets>runtime; build; native; contentfiles; analyzers</IncludeAssets>
      </PackageReference>
    </ItemGroup>

Or use `Directory.Build.props` in the `tests/` folder to apply to all test projects:

    <Project>
      <PropertyGroup>
        <IsPackable>false</IsPackable>
        <CollectCoverage>true</CollectCoverage>
        <CoverletOutputFormat>cobertura</CoverletOutputFormat>
      </PropertyGroup>
      <ItemGroup>
        <PackageReference Include="xunit" Version="2.*" />
        <PackageReference Include="xunit.runner.visualstudio" Version="2.*" />
        <PackageReference Include="coverlet.collector" Version="6.*" />
        <PackageReference Include="FluentAssertions" Version="7.*" />
        <PackageReference Include="Moq" Version="4.*" />
        <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.*" />
      </ItemGroup>
    </Project>

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

.dockerignore must exclude tests AND artifacts from the build context:
    tests/
    TestResults/
    bin/
    obj/
    *.user
    *.suo
    .vs/
    **/*.Tests/

═══════════════════════════════════════════════════════════════════════════════
10. WORKFLOW CHECKLIST
═══════════════════════════════════════════════════════════════════════════════

Follow this order:

□ Phase 1 — Sanitize
  1. List all test files across all `.Tests` projects
  2. For each: verify type references resolve to existing source types
  3. Delete orphaned test files (references point to deleted/renamed types)
  4. Fix stale tests (wrong property names, changed signatures, renamed parameters)
  5. Add missing copyright headers
  6. Compile-check all remaining test projects: `dotnet build --no-restore -q`

□ Phase 2 — Identify gaps
  7. List all source types under `src/` (excluding generated code, `obj/`, `bin/`)
  8. List all existing test files under `tests/`
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
  17. Ensure tests/ is separate from src/ (not inside a source project)
  18. Ensure each test project has Coverlet and xUnit packages configured
  19. Ensure .gitignore excludes test artifacts
  20. Ensure .dockerignore excludes tests/ and all test artifacts

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

    public class ClaimRepositoryTests : IClassFixture<DatabaseFixture>
    {
        private readonly DatabaseFixture _fixture;

        public ClaimRepositoryTests(DatabaseFixture fixture)
        {
            _fixture = fixture;
        }
    }

Use `ICollectionFixture<T>` for setup shared across multiple test classes:
    [CollectionDefinition("Database")]
    public class DatabaseCollection : ICollectionFixture<DatabaseFixture> { }

    [Collection("Database")]
    public class ClaimRepositoryTests { ... }

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
    public static IEnumerable<object[]> InvalidClaims => new List<object[]>
    {
        new object[] { new Claim("", ClaimType.Medical), "ClaimId is required" },
        new object[] { new Claim("CLM-001", (ClaimType)999), "Invalid ClaimType" },
    };

    [Theory]
    [MemberData(nameof(InvalidClaims))]
    public void Validate_WithInvalidClaim_ReturnsError(Claim claim, string expectedError) { ... }

`[ClassData]` for reusable test data generators:
    public class InvalidClaimData : TheoryData<Claim, string>
    {
        public InvalidClaimData()
        {
            Add(new Claim("", ClaimType.Medical), "ClaimId is required");
            Add(new Claim("CLM-001", (ClaimType)999), "Invalid ClaimType");
        }
    }

    [Theory]
    [ClassData(typeof(InvalidClaimData))]
    public void Validate_WithInvalidClaim_ReturnsError(Claim claim, string expectedError) { ... }

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
