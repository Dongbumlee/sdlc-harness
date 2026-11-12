package com.example.{{PackageName}}.cli;

/** Thin entry point: everything testable lives behind {@link CliApp}. */
public final class Main {

  private Main() {}

  public static void main(String[] args) {
    System.exit(CliApp.create().execute(args));
  }
}
