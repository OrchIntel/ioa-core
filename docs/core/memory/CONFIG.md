**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->


### Profiles

- `MEMORY_ENGINE_PROFILE=local` (default): SQLite hot store only.
- `MEMORY_ENGINE_PROFILE=hybrid`: SQLite hot + S3 cold.
- `MEMORY_ENGINE_PROFILE=cloud`: S3 cold only.

### Hot Store

- `APP_HOT_DB_PATH` — SQLite path (e.g., `/tmp/ioa_hot.db`). Default `:memory:`.

### Cold Store (S3/MinIO)

- `IOA_S3_BUCKET` — required to enable.
- `IOA_S3_REGION`, `IOA_S3_ENDPOINT` — optional.
- `IOA_S3_ACCESS_KEY`, `IOA_S3_SECRET_KEY` — optional if not using instance/profile auth.
- `IOA_S3_PREFIX` — default `memory/`.

### Vector Index

- `IOA_VECTOR_SEARCH` — `on|off` (default off). When off, a stub adapter returns NotConfigured gracefully.

### Compliance

- `IOA_REDACTION` — `on|off` (default on).
- `IOA_RETENTION_DAYS` — integer; 0 disables retention pruning.


