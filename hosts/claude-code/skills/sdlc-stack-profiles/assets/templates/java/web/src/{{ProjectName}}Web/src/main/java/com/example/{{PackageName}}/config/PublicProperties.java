package com.example.{{PackageName}}.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * Application configuration, split the way the web type requires.
 *
 * <p>The split is structural, not a naming habit. Values a browser may see live in {@link
 * PublicProperties} and are the only ones a controller ever puts in the model. Server-only values
 * live in {@link ServerProperties}, are read from the environment at startup, and must never be
 * rendered, logged, or sent to a client — leaking one into a page is this type's signature security
 * defect, and the test suite pins a sentinel secret out of every response.
 *
 * <p>Binding follows Spring Boot's relaxed rules: {@code app.public.app-name} binds from the
 * environment variable {@code APP_PUBLIC_APPNAME}, {@code app.server.api-key} from {@code
 * APP_SERVER_APIKEY}.
 */
@ConfigurationProperties(prefix = "app.public")
public record PublicProperties(String appName) {

  public PublicProperties {
    if (appName == null || appName.isBlank()) {
      appName = "{{ProjectName}}";
    }
  }
}
