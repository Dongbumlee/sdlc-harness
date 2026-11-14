using {{ProjectName}}API.Models;

namespace {{ProjectName}}API.Services;

/// <summary>Service contract used by the endpoints.</summary>
public interface IItemService
{
    Item Create(CreateItemRequest request);
    Item? GetById(int id);
    IReadOnlyList<Item> List();
}
