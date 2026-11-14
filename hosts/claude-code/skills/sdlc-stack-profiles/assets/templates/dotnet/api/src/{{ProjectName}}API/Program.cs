using {{ProjectName}}API.Endpoints;
using {{ProjectName}}API.Services;

var builder = WebApplication.CreateBuilder(args);

// Health checks — every API exposes /health (see the dotnet stack profile).
builder.Services.AddHealthChecks();

// Dependency injection: interface-first registrations, mirroring the
// harness's Protocol convention in the python profile.
builder.Services.AddSingleton<IItemRepository, InMemoryItemRepository>();
builder.Services.AddScoped<IItemService, ItemService>();

var app = builder.Build();

app.MapHealthChecks("/health");
app.MapItemEndpoints();

app.Run();

// Exposed for WebApplicationFactory-based integration tests.
public partial class Program { }
