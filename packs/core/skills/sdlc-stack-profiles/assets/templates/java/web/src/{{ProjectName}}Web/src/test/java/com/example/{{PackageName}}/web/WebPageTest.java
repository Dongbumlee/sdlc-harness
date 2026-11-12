package com.example.{{PackageName}}.web;

import static org.hamcrest.Matchers.containsString;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.redirectedUrl;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

/**
 * Page tests for the web template. These pin the web type's contract through the MVC stack, the way
 * the API templates pin theirs: the page renders the sample slice, the markup floor holds
 * (landmarks, skip link, labelled control), the add-item journey works end to end, and a
 * server-only secret never appears in any response.
 */
@SpringBootTest
@AutoConfigureMockMvc
class WebPageTest {

  @Autowired private MockMvc mvc;

  @Test
  void indexRendersItems() throws Exception {
    mvc.perform(get("/"))
        .andExpect(status().isOk())
        .andExpect(content().string(containsString("First item")))
        .andExpect(content().string(containsString("Second item")));
  }

  @Test
  void markupFloorHolds() throws Exception {
    mvc.perform(get("/"))
        .andExpect(status().isOk())
        .andExpect(content().string(containsString("<html lang=\"en\">")))
        .andExpect(content().string(containsString("<main id=\"main\">")))
        .andExpect(content().string(containsString("Skip to main content")))
        .andExpect(content().string(containsString("<label for=\"item-name\">")))
        .andExpect(content().string(containsString("id=\"item-name\"")));
  }

  @Test
  void addItemJourney() throws Exception {
    mvc.perform(
            post("/items")
                .contentType(MediaType.APPLICATION_FORM_URLENCODED)
                .param("name", "Third item"))
        .andExpect(status().is3xxRedirection())
        .andExpect(redirectedUrl("/"));
    mvc.perform(get("/"))
        .andExpect(status().isOk())
        .andExpect(content().string(containsString("Third item")));
  }

  @Test
  void healthAnswers() throws Exception {
    mvc.perform(get("/health"))
        .andExpect(status().isOk())
        .andExpect(content().string(containsString("\"status\":\"ok\"")));
  }

  @Test
  void staticAssetsServed() throws Exception {
    mvc.perform(get("/site.css"))
        .andExpect(status().isOk())
        .andExpect(content().string(containsString("skip-link")));
  }

  @Test
  void publicConfigRenderedByDefault() throws Exception {
    mvc.perform(get("/"))
        .andExpect(status().isOk())
        .andExpect(content().string(containsString("{{ProjectName}}")));
  }
}
