package com.example.{{PackageName}}.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

/** Server-only configuration: never rendered, never sent to a client. */
@ConfigurationProperties(prefix = "app.server")
public record ServerProperties(String apiKey) {

  public ServerProperties {
    if (apiKey == null) {
      apiKey = "";
    }
  }
}
