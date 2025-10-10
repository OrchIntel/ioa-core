# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

#!/usr/bin/env bash
set -euo pipefail
export PYTHONWARNINGS=error IOA_NON_INTERACTIVE=1
pytest -q -v --tb=short
# String scan to guard accidental warning slippage
if pytest -q -v --tb=short 2>&1 | grep -i warning; then
  echo "Warnings detected"
  exit 1
fi
