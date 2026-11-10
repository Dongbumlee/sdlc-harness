"""Calibration fixtures are review inputs, not runnable tests.

The input trees deliberately contain realistic test files (including, in
case-06, a weakened one). They must never be collected by this repo's own
pytest run.
"""

collect_ignore_glob = ["*/input/*", "*/input/**/*"]
