**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# IOA Core Legal Dependencies Matrix

**Generated:** 2025-10-05T21:42:36.140991+00:00
**Total Dependencies:** 31

## License Risk Summary
- **Low Risk:** 10 (Apache-2.0/MIT/BSD)
- **Medium Risk:** 21 (requires review)
- **High Risk:** 0 (GPL/AGPL/proprietary)

## Dependencies Matrix

| Package | Version | License | Risk | Usage | Action | Source |
|---------|---------|---------|------|-------|--------|--------|
| aiohttp | unknown | unknown | medium | production | verify | requirements.txt |
| asyncio-mqtt | unknown | unknown | medium | production | verify | requirements.txt |
| carbontracker | unknown | unknown | medium | production | verify | requirements.txt |
| click | unknown | BSD-3-Clause | low | production | none | requirements.txt |
| cryptography | unknown | Apache-2.0 | low | production | none | requirements.txt |
| fairlearn | unknown | unknown | medium | production | verify | requirements.txt |
| jsonschema | unknown | unknown | medium | development | verify | requirements-dev.txt |
| linkchecker | unknown | unknown | medium | production | verify | requirements-docs.txt |
| mkdocs | unknown | unknown | medium | production | verify | requirements-docs.txt |
| mkdocs-material | unknown | unknown | medium | production | verify | requirements-docs.txt |
| openai | unknown | unknown | medium | production | verify | requirements.txt |
| presidio-analyzer | unknown | unknown | medium | production | verify | requirements.txt |
| presidio-anonymizer | unknown | unknown | medium | production | verify | requirements.txt |
| pydantic | unknown | MIT | low | production | none | requirements.txt |
| pymongo | unknown | unknown | medium | production | verify | requirements.txt |
| pytest | unknown | MIT | low | production | none | requirements.txt |
| pytest-asyncio | unknown | unknown | medium | production | verify | requirements.txt |
| pytest-cov | unknown | unknown | medium | development | verify | requirements-dev.txt |
| pytest-timeout | unknown | unknown | medium | development | verify | requirements-dev.txt |
| python-dotenv | unknown | BSD-3-Clause | low | production | none | requirements.txt |
| pyyaml | unknown | MIT | low | production | none | requirements.txt |
| requests | unknown | Apache-2.0 | low | production | none | requirements.txt |
| rich | unknown | MIT | low | production | none | requirements.txt |
| scikit-learn | unknown | unknown | medium | production | verify | requirements.txt |
| scipy | unknown | unknown | medium | production | verify | requirements.txt |
| setuptools | unknown | unknown | medium | production | verify | pyproject.toml (build-system) |
| structlog | unknown | MIT | low | production | none | requirements.txt |
| tqdm | unknown | MIT | low | production | none | requirements.txt |
| vale | unknown | unknown | medium | production | verify | requirements-docs.txt |
| wheel | unknown | unknown | medium | production | verify | pyproject.toml (build-system) |
| wordfreq | unknown | unknown | medium | production | verify | requirements.txt |

## Audit Log

```
Starting license audit at 2025-10-05T21:42:35.360705+00:00
pip-licenses not available, using fallback license detection
Audit complete. Found 31 dependencies.
```