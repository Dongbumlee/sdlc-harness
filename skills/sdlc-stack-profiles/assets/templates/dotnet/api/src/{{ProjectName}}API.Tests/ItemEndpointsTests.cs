using System.Net;
using System.Net.Http.Json;
using Microsoft.AspNetCore.Mvc.Testing;
using Xunit;
using {{ProjectName}}API.Models;

namespace {{ProjectName}}API.Tests;

public class ItemEndpointsTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly HttpClient _client;

    public ItemEndpointsTests(WebApplicationFactory<Program> factory)
    {
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task Health_Returns200()
    {
        var response = await _client.GetAsync("/health");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
    }

    [Fact]
    public async Task Create_ThenGet_ReturnsItem()
    {
        var created = await _client.PostAsJsonAsync("/items", new CreateItemRequest("first", "sample"));
        Assert.Equal(HttpStatusCode.Created, created.StatusCode);
        var item = await created.Content.ReadFromJsonAsync<Item>();
        Assert.NotNull(item);
        Assert.Equal("first", item!.Name);

        var fetched = await _client.GetAsync($"/items/{item.Id}");
        Assert.Equal(HttpStatusCode.OK, fetched.StatusCode);
    }

    [Fact]
    public async Task Get_Unknown_Returns404()
    {
        var response = await _client.GetAsync("/items/999999");
        Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
    }

    [Fact]
    public async Task Create_EmptyName_Returns400()
    {
        var response = await _client.PostAsJsonAsync("/items", new CreateItemRequest("", null));
        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
    }
}
