using System.Collections.Concurrent;
using {{ProjectName}}API.Models;

namespace {{ProjectName}}API.Services;

/// <summary>In-memory repository (sample slice).</summary>
public class InMemoryItemRepository : IItemRepository
{
    private readonly ConcurrentDictionary<int, Item> _items = new();
    private int _nextId;

    public Item Add(CreateItemRequest request)
    {
        var item = new Item(Interlocked.Increment(ref _nextId), request.Name!, request.Description);
        _items[item.Id] = item;
        return item;
    }

    public Item? Get(int id) => _items.TryGetValue(id, out var item) ? item : null;

    public IReadOnlyList<Item> List() => _items.Values.OrderBy(i => i.Id).ToList();
}
