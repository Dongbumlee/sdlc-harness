package com.example.{{PackageName}}.web;

import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.not;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;

/**
 * The web type's signature test: with a public name and a sentinel server secret configured, the
 * public value renders and the secret appears in no response — page, health, or static asset.
 */
@SpringBootTest(
    properties = {"app.public.app-name=Public Name", "app.server.api-key=sentinel-secret-12345"})
@AutoConfigureMockMvc
class SecretLeakTest {

  @Autowired private MockMvc mvc;

  @Test
  void publicNameRendersAndSecretNeverLeaks() throws Exception {
    mvc.perform(get("/"))
        .andExpect(status().isOk())
        .andExpect(content().string(containsString("Public Name")));
    for (String path : new String[] {"/", "/health", "/site.css"}) {
      mvc.perform(get(path))
          .andExpect(status().isOk())
          .andExpect(content().string(not(containsString("sentinel-secret-12345"))));
    }
  }
}
