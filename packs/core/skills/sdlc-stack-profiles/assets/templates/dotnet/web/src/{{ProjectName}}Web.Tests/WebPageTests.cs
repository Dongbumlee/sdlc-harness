using System.Net;
using System.Text.RegularExpressions;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.Configuration;
using Xunit;

namespace {{ProjectName}}Web.Tests;

/// <summary>
/// Page tests for the web template. These pin the web type's
/// contract through HTTP, the way the API templates pin theirs:
/// the page renders the sample slice, the markup floor holds
/// (landmarks, skip link, labelled control), the add-item journey
/// works end to end (antiforgery token and post/redirect/get
/// included), and a server-only secret never appears in any
/// response.
/// </summary>
public sealed class WebPageTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly WebApplicationFactory<Program> _factory;

    public WebPageTests(WebApplicationFactory<Program> factory) => _factory = factory;

    [Fact]
    public async Task IndexRendersItems()
    {
        var client = _factory.CreateClient();
        var body = await client.GetStringAsync("/");
        Assert.Contains("First item", body);
        Assert.Contains("Second item", body);
    }

    [Fact]
    public async Task MarkupFloorHolds()
    {
        var client = _factory.CreateClient();
        var body = await client.GetStringAsync("/");
        Assert.Contains("<html lang=\"en\">", body);
        Assert.Contains("<main id=\"main\">", body);
        Assert.Contains("Skip to main content", body);
        Assert.Contains("<label for=\"item-name\">", body);
        Assert.Contains("id=\"item-name\"", body);
    }

    [Fact]
    public async Task AddItemJourney()
    {
        var client = _factory.CreateClient();

        // Razor Pages protects posts with an antiforgery token:
        // fetch the form, take the token and its cookie, then post
        // like a browser would.
        var getResponse = await client.GetAsync("/");
        var html = await getResponse.Content.ReadAsStringAsync();
        var token = Regex.Match(html, "name=\"__RequestVerificationToken\"[^>]*value=\"([^\"]+)\"")
            .Groups[1].Value;
        Assert.NotEqual(string.Empty, token);
        var cookies = string.Join("; ", getResponse.Headers
            .GetValues("Set-Cookie").Select(c => c.Split(';')[0]));

        // The form posts back to the page itself ("/").
        var request = new HttpRequestMessage(HttpMethod.Post, "/");
        request.Headers.Add("Cookie", cookies);
        request.Content = new FormUrlEncodedContent(new Dictionary<string, string>
        {
            ["name"] = "Third item",
            ["__RequestVerificationToken"] = token,
        });
        var response = await client.SendAsync(request);
        var body = await response.Content.ReadAsStringAsync();
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.Contains("Third item", body);
    }

    [Fact]
    public async Task HealthAnswers()
    {
        var client = _factory.CreateClient();
        var body = await client.GetStringAsync("/health");
        Assert.Contains("\"status\":\"ok\"", body);
    }

    [Fact]
    public async Task StaticAssetsServed()
    {
        var client = _factory.CreateClient();
        var body = await client.GetStringAsync("/site.css");
        Assert.Contains("skip-link", body);
    }

    [Fact]
    public async Task PublicConfigRenderedAndSecretNeverLeaks()
    {
        const string sentinel = "sentinel-secret-12345";
        using var factory = _factory.WithWebHostBuilder(builder =>
        {
            builder.ConfigureAppConfiguration((_, config) =>
            {
                config.AddInMemoryCollection(new Dictionary<string, string?>
                {
                    ["Public:AppName"] = "Public Name",
                    ["Server:ApiKey"] = sentinel,
                });
            });
        });
        var client = factory.CreateClient();
        var index = await client.GetStringAsync("/");
        Assert.Contains("Public Name", index);
        foreach (var path in new[] { "/", "/health", "/site.css" })
        {
            var body = await client.GetStringAsync(path);
            Assert.DoesNotContain(sentinel, body);
        }
    }
}
