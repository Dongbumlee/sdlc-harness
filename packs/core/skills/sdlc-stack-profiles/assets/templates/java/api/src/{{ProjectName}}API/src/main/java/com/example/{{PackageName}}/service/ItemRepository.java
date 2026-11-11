package com.example.{{PackageName}}.service;

import com.example.{{PackageName}}.model.Item;
import java.util.List;
import java.util.Optional;

/** Storage boundary for items. The service depends on this interface only. */
public interface ItemRepository {

  Item save(String name);

  Optional<Item> findById(long id);

  List<Item> findAll();
}
