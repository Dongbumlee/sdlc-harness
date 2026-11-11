package com.example.{{PackageName}}.service;

import com.example.{{PackageName}}.model.Item;
import java.util.List;
import java.util.Optional;

/** Item operations the web layer depends on. */
public interface ItemService {

  Item create(String name);

  Optional<Item> get(long id);

  List<Item> list();
}
