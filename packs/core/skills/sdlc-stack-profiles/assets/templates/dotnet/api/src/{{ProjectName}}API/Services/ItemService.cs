using {{ProjectName}}API.Models;

namespace {{ProjectName}}API.Services;

public class ItemService(IItemRepository repository) : IItemService
{
    public Item Create(CreateItemRequest request) => repository.Add(request);

    public Item? GetById(int id) => repository.GetById(id);

    public IReadOnlyList<Item> List() => repository.List();
}
