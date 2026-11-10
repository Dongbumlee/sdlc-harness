# Sprint Contract — Record export (Implementer Step 0)

| # | Criterion | Verification |
|---|---|---|
| 1 | POST /export returns 200 and a CSV containing every record | API test `test_export_all_records` |
| 2 | With more than 10,000 records, the response lists numbered part files, each a parseable CSV | API test `test_export_splits_at_cap` |
| 3 | An empty record set returns 200 and a header-only CSV | API test `test_export_empty_set` |
