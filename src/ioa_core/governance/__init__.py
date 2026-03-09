"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

from .manifest import SystemLaws, load_manifest, verify_signature, get_laws
from .policy_engine import PolicyEngine, ActionContext, ValidationResult
from .system_laws import SystemLawsError
from .cross_domain import IdentityEntity, DomainContext, GovernanceIncidentEvent
from .healthcare_taxonomy import (
    CLINICAL_RISK_CLASSES,
    CONSENT_REQUIRED_RISK_CLASSES,
    FHIR_RESOURCE_RISK_DEFAULTS,
    normalize_risk_class,
    infer_risk_from_text,
    infer_risk_from_resource_type,
    resolve_effective_risk_class,
    consent_required_for_risk,
)

__all__ = [
    'SystemLaws',
    'load_manifest', 
    'verify_signature',
    'get_laws',
    'PolicyEngine',
    'ActionContext',
    'ValidationResult',
    'SystemLawsError',
    'IdentityEntity',
    'DomainContext',
    'GovernanceIncidentEvent',
    'CLINICAL_RISK_CLASSES',
    'CONSENT_REQUIRED_RISK_CLASSES',
    'FHIR_RESOURCE_RISK_DEFAULTS',
    'normalize_risk_class',
    'infer_risk_from_text',
    'infer_risk_from_resource_type',
    'resolve_effective_risk_class',
    'consent_required_for_risk',
]
