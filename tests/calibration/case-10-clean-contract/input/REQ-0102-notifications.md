# REQ-0102 — Notification preferences (excerpt, approved)

- **FR-1.** A user can read their notification preferences.
- **FR-2.** A user can update their preferences; an unknown channel name
  is rejected with 422.
- **FR-3.** When the preference store is unavailable, reads serve the
  documented defaults and the response is marked `degraded: true`;
  updates fail with 503 rather than pretending to save.
