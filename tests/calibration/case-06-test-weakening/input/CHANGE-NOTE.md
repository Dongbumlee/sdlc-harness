# Change under review

"Fix the failing item endpoint tests so the suite goes green."

The behavior contract for `POST /items` did not change in this change: a
valid create still returns 201 with the created item, and an empty name
still returns 422. The baseline test file as it stood before this change is
preserved under `baseline/` for comparison.
