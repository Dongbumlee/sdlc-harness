package com.example.{{PackageName}};

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
@ConfigurationPropertiesScan
public class {{ProjectName}}Application {

  public static void main(String[] args) {
    SpringApplication.run({{ProjectName}}Application.class, args);
  }
}
