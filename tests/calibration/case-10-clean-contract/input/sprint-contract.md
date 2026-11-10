# Sprint Contract — Notification preferences (Implementer Step 0)

| # | Criterion | Verification |
|---|---|---|
| 1 | GET /preferences returns the stored preferences for the user | API test `test_get_preferences` |
| 2 | PUT /preferences with valid channels returns 200 and persists the change | API test `test_update_preferences` |
| 3 | PUT with an unknown channel returns 422 and changes nothing | API test `test_update_unknown_channel_422` |
| 4 | With the store down, GET returns 200 with the documented defaults and `degraded: true` | API test with the store stubbed unavailable, `test_get_preferences_degraded` |
| 5 | With the store down, PUT returns 503 and no change is recorded | API test `test_update_store_down_503` |
