using {{ProjectName}}Web.Configuration;
using {{ProjectName}}Web.Services;

var builder = WebApplication.CreateBuilder(args);

builder.Services.Configure<PublicOptions>(
    builder.Configuration.GetSection(PublicOptions.SectionName));
builder.Services.Configure<ServerOptions>(
    builder.Configuration.GetSection(ServerOptions.SectionName));
builder.Services.AddSingleton<ItemStore>();
builder.Services.AddRazorPages();

var app = builder.Build();

app.UseStaticFiles();
app.MapRazorPages();
app.MapGet("/health", () => Results.Json(new { status = "ok" }));

app.Run();

// Exposed for WebApplicationFactory-based integration tests.
public partial class Program { }
