package com.example.{{PackageName}}.service;

import com.example.{{PackageName}}.model.Item;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

/** In-memory {@link ItemRepository} shipped with the template's sample slice. */
public class InMemoryItemRepository implements ItemRepository {

  private final ConcurrentHashMap<Long, Item> store = new ConcurrentHashMap<>();
  private final AtomicLong sequence = new AtomicLong();

  @Override
  public Item save(String name) {
    long id = sequence.incrementAndGet();
    Item item = new Item(id, name);
    store.put(id, item);
    return item;
  }

  @Override
  public Optional<Item> findById(long id) {
    return Optional.ofNullable(store.get(id));
  }

  @Override
  public List<Item> findAll() {
    return store.values().stream().sorted((a, b) -> Long.compare(a.id(), b.id())).toList();
  }
}
