package com.example.{{PackageName}}.web;

import com.example.{{PackageName}}.model.Item;
import com.example.{{PackageName}}.model.ItemCreate;
import com.example.{{PackageName}}.service.ItemService;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

/** HTTP boundary for the sample items slice. Depends on the service interface only. */
@RestController
@RequestMapping("/items")
public class ItemController {

  private final ItemService service;

  public ItemController(ItemService service) {
    this.service = service;
  }

  @PostMapping
  @ResponseStatus(HttpStatus.CREATED)
  Item create(@Valid @RequestBody ItemCreate request) {
    return service.create(request.name());
  }

  @GetMapping("/{id}")
  Item get(@PathVariable long id) {
    return service
        .get(id)
        .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "item not found"));
  }

  @GetMapping
  List<Item> list() {
    return service.list();
  }
}
