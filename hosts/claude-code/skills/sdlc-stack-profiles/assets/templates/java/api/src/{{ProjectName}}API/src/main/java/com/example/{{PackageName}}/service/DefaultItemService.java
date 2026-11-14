package com.example.{{PackageName}}.service;

import com.example.{{PackageName}}.model.Item;
import java.util.List;
import java.util.Optional;

/** Default {@link ItemService} backed by an {@link ItemRepository}. */
public class DefaultItemService implements ItemService {

  private final ItemRepository repository;

  public DefaultItemService(ItemRepository repository) {
    this.repository = repository;
  }

  @Override
  public Item create(String name) {
    return repository.save(name);
  }

  @Override
  public Optional<Item> get(long id) {
    return repository.findById(id);
  }

  @Override
  public List<Item> list() {
    return repository.findAll();
  }
}
