using {{ProjectName}}API.Models;
using {{ProjectName}}API.Services;

namespace {{ProjectName}}API.Endpoints;

public static class ItemEndpoints
{
    public static IEndpointRouteBuilder MapItemEndpoints(this IEndpointRouteBuilder routes)
    {
        var group = routes.MapGroup("/items");

        group.MapPost("/", (CreateItemRequest request, IItemService service) =>
        {
            if (string.IsNullOrWhiteSpace(request.Name))
            {
                return Results.BadRequest(new { error = "Name is required." });
            }
            var item = service.Create(request);
            return Results.Created($"/items/{item.Id}", item);
        });

        group.MapGet("/", (IItemService service) => Results.Ok(service.List()));

        group.MapGet("/{id:int}", (int id, IItemService service) =>
        {
            var item = service.Get(id);
            return item is null ? Results.NotFound() : Results.Ok(item);
        });

        return routes;
    }
}
