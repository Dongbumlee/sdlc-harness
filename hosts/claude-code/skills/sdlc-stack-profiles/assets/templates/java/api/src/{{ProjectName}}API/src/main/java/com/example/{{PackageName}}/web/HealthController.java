package com.example.{{PackageName}}.web;

import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

/** Liveness and readiness probes, mirroring the other bundled templates. */
@RestController
public class HealthController {

  @GetMapping("/health")
  Map<String, String> health() {
    return Map.of("status", "healthy");
  }

  @GetMapping("/health/ready")
  Map<String, String> ready() {
    return Map.of("status", "ready");
  }
}
