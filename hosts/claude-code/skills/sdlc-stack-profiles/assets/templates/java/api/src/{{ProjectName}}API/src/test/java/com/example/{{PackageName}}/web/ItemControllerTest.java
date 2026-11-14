package com.example.{{PackageName}}.web;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest
@AutoConfigureMockMvc
class ItemControllerTest {

  @Autowired private MockMvc mockMvc;

  @Test
  void healthReportsHealthy() throws Exception {
    mockMvc
        .perform(get("/health"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.status").value("healthy"));
  }

  @Test
  void readinessReportsReady() throws Exception {
    mockMvc
        .perform(get("/health/ready"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.status").value("ready"));
  }

  @Test
  void createThenGetRoundTrips() throws Exception {
    mockMvc
        .perform(
            post("/items").contentType(MediaType.APPLICATION_JSON).content("{\"name\": \"first\"}"))
        .andExpect(status().isCreated())
        .andExpect(jsonPath("$.name").value("first"));

    mockMvc
        .perform(get("/items/1"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.name").value("first"));
  }

  @Test
  void getMissingReturns404() throws Exception {
    mockMvc.perform(get("/items/999999")).andExpect(status().isNotFound());
  }

  @Test
  void createWithBlankNameReturns400() throws Exception {
    mockMvc
        .perform(
            post("/items").contentType(MediaType.APPLICATION_JSON).content("{\"name\": \"  \"}"))
        .andExpect(status().isBadRequest());
  }
}
