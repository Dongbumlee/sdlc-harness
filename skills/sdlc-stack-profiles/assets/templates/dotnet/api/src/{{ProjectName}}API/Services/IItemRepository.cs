using {{ProjectName}}API.Models;

namespace {{ProjectName}}API.Services;

/// <summary>
/// Storage contract for items. Replace the in-memory implementation with a
/// database-backed one without touching the service or endpoints.
/// </summary>
public interface IItemRepository
{
    Item Add(CreateItemRequest request);
    Item? Get(int id);
    IReadOnlyList<Item> List();
}
