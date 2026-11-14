namespace {{ProjectName}}API.Models;

public record CreateItemRequest(string? Name, string? Description);

public record Item(int Id, string Name, string? Description);
