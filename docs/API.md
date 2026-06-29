# API Documentation

`GET /health` returns service health.

`GET /stats` returns generated portfolio statistics.

`GET /problems` returns all solved problem metadata.

`GET /analytics` returns dashboard analytics including topic distribution, pattern
distribution, runtime buckets, and submission heatmap data.

`GET /sync/status` returns recent sync events and retry queue depth.

`POST /sync/recent` accepts `{ "username": "...", "limit": 20 }`.

`POST /sync/submission` accepts `{ "title_slug": "two-sum", "submission_id": "123" }`.
