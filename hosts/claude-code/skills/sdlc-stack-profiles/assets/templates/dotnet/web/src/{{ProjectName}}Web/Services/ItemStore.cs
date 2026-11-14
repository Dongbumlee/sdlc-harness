using {{ProjectName}}Web.Models;

namespace {{ProjectName}}Web.Services;

/// <summary>
/// The sample vertical slice: a tiny in-memory items store.
/// Replace with the real data layer; the page, form, and tests
/// around it are the template. Items are the same sample resource
/// the API templates use, here rendered server-side instead of
/// serialized.
/// </summary>
public sealed class ItemStore
{
    private readonly Lock _gate = new();
    private readonly List<Item> _items = [];
    private int _nextId = 1;

    public ItemStore()
    {
        Add("First item");
        Add("Second item");
    }

    public IReadOnlyList<Item> List()
    {
        lock (_gate)
        {
            return [.. _items];
        }
    }

    public int Add(string name)
    {
        lock (_gate)
        {
            var id = _nextId++;
            _items.Add(new Item(id, name));
            return id;
        }
    }
}
