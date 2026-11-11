package com.example.{{PackageName}};

import com.example.{{PackageName}}.service.DefaultItemService;
import com.example.{{PackageName}}.service.InMemoryItemRepository;
import com.example.{{PackageName}}.service.ItemRepository;
import com.example.{{PackageName}}.service.ItemService;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

/**
 * Composition root. This class is the only place implementations are wired together: the web layer
 * depends on the {@link ItemService} interface, the service depends on the {@link ItemRepository}
 * interface, and neither knows the other's implementation.
 */
@SpringBootApplication
public class {{ProjectName}}Application {

  public static void main(String[] args) {
    SpringApplication.run({{ProjectName}}Application.class, args);
  }

  @Bean
  ItemRepository itemRepository() {
    return new InMemoryItemRepository();
  }

  @Bean
  ItemService itemService(ItemRepository itemRepository) {
    return new DefaultItemService(itemRepository);
  }
}
