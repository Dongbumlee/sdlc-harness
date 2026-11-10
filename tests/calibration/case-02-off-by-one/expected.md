# Expected verdict

- Seat: code-quality-reviewer
- Minimum severity: high
- Finding: `paginate` treats the page as 0-based (`start = page * page_size`)
  although the module contract says pages are 1-based — page 1 skips the
  first `page_size` items. A correctness defect, not a style note.
- False positive: `page_count` is correct and must not be flagged.
