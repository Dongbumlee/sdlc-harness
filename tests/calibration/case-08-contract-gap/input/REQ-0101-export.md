# REQ-0101 — Record export (excerpt, approved)

- **FR-1.** Export all records as one CSV download.
- **FR-2.** If the export exceeds 10,000 rows, it is split into numbered
  parts, each a valid CSV.
- **FR-3.** A record that fails serialization is skipped, the export
  still completes, and the response reports how many records were
  skipped.
