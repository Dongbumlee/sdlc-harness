package com.example.{{PackageName}}.service;

import com.example.{{PackageName}}.model.Item;
import java.util.ArrayList;
import java.util.List;
import org.springframework.stereotype.Service;

/**
 * The sample vertical slice: a tiny in-memory items store. Replace with the real data layer; the
 * page, form, and tests around it are the template. Items are the same sample resource the API
 * templates use, here rendered server-side instead of serialized.
 */
@Service
public class ItemStore {

  private final List<Item> items = new ArrayList<>();
  private long nextId = 1;

  public ItemStore() {
    add("First item");
    add("Second item");
  }

  public synchronized List<Item> list() {
    return List.copyOf(items);
  }

  public synchronized long add(String name) {
    long id = nextId++;
    items.add(new Item(id, name));
    return id;
  }
}
