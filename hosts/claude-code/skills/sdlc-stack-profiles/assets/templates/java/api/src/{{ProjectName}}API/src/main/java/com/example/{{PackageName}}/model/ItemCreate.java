package com.example.{{PackageName}}.model;

import jakarta.validation.constraints.NotBlank;

/** Request body for creating an item. */
public record ItemCreate(@NotBlank String name) {}
