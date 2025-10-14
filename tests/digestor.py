"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

# PATCH: Cursor-2024-12-19 Fix digestor import for tests
from src.digestor import (
    create_digestor,
    DigestorConfig,
    DigestorCore,
    DigestResult,
    DigestorError,
    PatternMatchingError,
    VariableExtractionError,
    SentimentAnalysisError,
    SchemaValidationError,
    ProcessingStage,
    validate_digestor_patterns,
    validate_production_deployment
)

__all__ = [
    'create_digestor',
    'DigestorConfig', 
    'DigestorCore',
    'DigestResult',
    'DigestorError',
    'PatternMatchingError',
    'VariableExtractionError',
    'SentimentAnalysisError',
    'SchemaValidationError',
    'ProcessingStage',
    'validate_digestor_patterns',
    'validate_production_deployment'
]
