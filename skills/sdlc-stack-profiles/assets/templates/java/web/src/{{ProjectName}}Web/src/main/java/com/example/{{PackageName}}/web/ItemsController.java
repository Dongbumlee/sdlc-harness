package com.example.{{PackageName}}.web;

import com.example.{{PackageName}}.config.PublicProperties;
import com.example.{{PackageName}}.config.ServerProperties;
import com.example.{{PackageName}}.service.ItemStore;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;

/**
 * The items page, server-rendered. Only {@link PublicProperties} ever enters the model — see the
 * config package for the split. The {@link ServerProperties} dependency exists to make the boundary
 * explicit: it is held for server-side calls and never rendered.
 */
@Controller
public class ItemsController {

  private final ItemStore store;
  private final PublicProperties publicProperties;

  @SuppressWarnings("unused")
  private final ServerProperties serverProperties;

  public ItemsController(
      ItemStore store, PublicProperties publicProperties, ServerProperties serverProperties) {
    this.store = store;
    this.publicProperties = publicProperties;
    this.serverProperties = serverProperties;
  }

  @GetMapping("/")
  public String index(Model model) {
    model.addAttribute("appName", publicProperties.appName());
    model.addAttribute("items", store.list());
    return "index";
  }

  /** Post/redirect/get: the post answers with a redirect, so a refresh never resubmits. */
  @PostMapping("/items")
  public String addItem(@RequestParam String name) {
    if (!name.isBlank()) {
      store.add(name.trim());
    }
    return "redirect:/";
  }
}
