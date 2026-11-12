package com.example.{{PackageName}}.cli;

/**
 * Expected, user-facing failures, mapped to the contract's exit codes by Main's execution exception
 * handler.
 */

/** A failure while a command ran: message on stderr, exit 1. */
class CliFailureException extends RuntimeException {
  CliFailureException(String message) {
    super(message);
  }
}

/** A usage-class failure raised after parsing (a bad option value): exit 2. */
class CliUsageException extends RuntimeException {
  CliUsageException(String message) {
    super(message);
  }
}
