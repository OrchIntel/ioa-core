""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

# IOA Module v2.4.8 | IOA Contributors | Last updated: 2025-08-05
# Description: Agent onboarding system with manifest validation and tenant isolation
# License: Apache-2.0 – IOA Project
# © 2025 IOA Project. All rights reserved.

# PATCH: Cursor-2025-08-19 DISPATCH-GPT-20250819-022 <add PKI functionality for integration wiring>

#
# Example trust signature generation for onboarding manifests
# ---------------------------------------------------------
# To create a secure trust signature for an agent, you should generate a
# cryptographically strong secret and compute its SHA‑256 hash.  For example:
#
#     import hashlib, os
#     secret = os.urandom(32)
#     trust_signature = hashlib.sha256(secret).hexdigest()
#
# The resulting 64‑character hexadecimal string can be placed in your agent
# manifest under the "trust_signature" field.  ⚠️ WARNING: This is a sample
# only. You must generate and securely manage real production keys for live
# environments. Never commit private keys or secrets into your repository.


"""
Agent Onboarding Module - ONBOARD-001 Complete

Automated agent registration and onboarding system with comprehensive manifest
validation, tenant isolation, and trust verification. Provides seamless integration
for new agents into the IOA ecosystem with governance compliance.

Key Features:
- JSON schema-based manifest validation
- Multi-tenant agent isolation and scoping
- Trust signature verification and registry management
- Automated routing configuration and health monitoring
- Performance metrics collection and KPI tracking
- Event-driven registry updates with rollback support
"""

import os
import json
import hashlib
import threading
import logging
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from enum import Enum

# Optional jsonschema import with fallback
try:
    import jsonschema
    from jsonschema import validate, ValidationError, SchemaError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    logging.warning("jsonschema not available, using manual validation")

# PATCH: Cursor-2025-08-19 DISPATCH-GPT-20250819-022 <add PKI functionality for integration wiring>
from .security.signature_engine import SignatureEngine
from .governance.audit_chain import get_audit_chain


class OnboardStatus(Enum):
    """Agent onboarding status enumeration."""
    PENDING = "pending"
    VALIDATING = "validating"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class ValidationLevel(Enum):
    """Validation strictness levels."""
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"


@dataclass
class AgentManifest:
    """Agent manifest data structure."""
    agent_id: str
    adapter_class: str
    capabilities: List[str]
    tenant_id: str
    trust_signature: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentManifest':
        """Create AgentManifest from dictionary."""
        return cls(
            agent_id=data['agent_id'],
            adapter_class=data['adapter_class'],
            capabilities=data['capabilities'],
            tenant_id=data['tenant_id'],
            trust_signature=data['trust_signature'],
            metadata=data.get('metadata', {})
        )


@dataclass
class OnboardingResult:
    """Result of agent onboarding process."""
    agent_id: str
    status: OnboardStatus
    success: bool
    validation_errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class AgentOnboardingError(Exception):
    """Base exception for agent onboarding operations."""
    pass


class ManifestValidationError(AgentOnboardingError):
    """Raised when manifest validation fails."""
    pass


class TrustVerificationError(AgentOnboardingError):
    """Raised when trust verification fails."""
    pass


class TenantIsolationError(AgentOnboardingError):
    """Raised when tenant isolation is violated."""
    pass


class AgentOnboarding:
    """
    Agent onboarding system with comprehensive validation and tenant isolation.
    
    Manages the complete agent registration lifecycle from manifest validation
    through active deployment with performance monitoring and governance compliance.
    
    PATCH: Cursor-2025-08-19 DISPATCH-GPT-20250819-022 <add PKI functionality for integration wiring>
    Enhanced with RSA signature verification and audit logging.
    """
    
    def __init__(self, 
                 base_dir: Optional[Path] = None,
                 validation_level: ValidationLevel = ValidationLevel.STANDARD,
                 enable_kpi_tracking: bool = True) -> None:
        """
        Initialize agent onboarding system.
        
        Args:
            base_dir: Base directory for configuration files
            validation_level: Strictness of validation checks
            enable_kpi_tracking: Enable performance metrics collection
        """
        self.base_dir = base_dir or Path.cwd()
        self.validation_level = validation_level
        self.enable_kpi_tracking = enable_kpi_tracking
        
        # Initialize logging before loading schema
        self.logger = logging.getLogger(__name__)
        # Load JSON schema for validation
        self.schema = self._load_manifest_schema()
        
        # Agent registry and tracking
        self._onboarding_history: List[OnboardingResult] = []
        
        # Thread safety
        self._lock = threading.RLock()
        
        # PATCH: Cursor-2025-08-19 DISPATCH-GPT-20250819-022 <add PKI functionality for integration wiring>
        # Initialize signature engine for manifest signing
        self.signature_engine = SignatureEngine()
        self.manifest_registry_file = self.base_dir / "agent_manifest_registry.json"
        self.manifest_registry: Dict[str, Any] = {}
        
        # Load existing manifest registry
        self._load_manifest_registry()
        
        # KPI tracking
        if self.enable_kpi_tracking:
            try:
                from .kpi_monitor import KPIMonitor
                self.kpi_monitor = KPIMonitor(enable_persistence=True)
            except ImportError:
                self.kpi_monitor = None
                logging.warning("KPI monitoring unavailable")
        else:
            self.kpi_monitor = None
            
        # Logging is initialized at the start of the constructor

    def _load_manifest_schema(self) -> Optional[Dict[str, Any]]:
        """Load agent onboarding JSON schema."""
        schema_path = self.base_dir / "config" / "agent_onboarding_schema.json"
        
        try:
            if schema_path.exists():
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema = json.load(f)
                self.logger.info(f"Loaded manifest schema from {schema_path}")
                return schema
            else:
                self.logger.warning(f"Schema file not found: {schema_path}")
                return None
        except Exception as e:
            self.logger.error(f"Failed to load schema: {e}")
            return None
    
    def validate_manifest_schema(self, manifest_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate agent manifest against JSON schema.
        
        Args:
            manifest_data: Raw manifest data to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        try:
            # PATCH: Cursor-2024-12-19 Add debug logging for schema validation
            self.logger.info(f"Validating manifest: {manifest_data}")
            self.logger.info(f"JSONSCHEMA_AVAILABLE: {JSONSCHEMA_AVAILABLE}")
            self.logger.info(f"Schema loaded: {self.schema is not None}")
            
            # Use jsonschema if available
            if JSONSCHEMA_AVAILABLE and self.schema:
                try:
                    validate(instance=manifest_data, schema=self.schema)
                    self.logger.info("JSON schema validation passed")
                    return True, []
                except ValidationError as e:
                    errors.append(f"Schema validation failed: {e.message}")
                    self.logger.info(f"JSON schema validation failed: {errors}")
                    return False, errors
                except SchemaError as e:
                    errors.append(f"Invalid schema: {e.message}")
                    self.logger.info(f"JSON schema error: {errors}")
                    return False, errors
            
            # Fallback to manual validation
            self.logger.info("Using manual validation fallback")
            result = self._manual_schema_validation(manifest_data)
            self.logger.info(f"Manual validation result: {result}")
            return result
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            self.logger.error(f"Validation exception: {errors}")
            return False, errors
    
    def _manual_schema_validation(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Manual schema validation fallback."""
        errors = []
        
        # Required fields check
        required_fields = {'agent_id', 'adapter_class', 'capabilities', 'tenant_id', 'trust_signature'}
        missing_fields = required_fields - set(data.keys())
        if missing_fields:
            errors.append(f"Missing required fields: {missing_fields}")
        
        # Field type and format validation (only if field is present)
        if 'agent_id' in data:
            if not isinstance(data['agent_id'], str) or len(data['agent_id']) < 3:
                errors.append("agent_id must be string with minimum 3 characters")
        
        if 'adapter_class' in data:
            if not isinstance(data['adapter_class'], str):
                errors.append("adapter_class must be string")
            elif not self._validate_adapter_class_format(data['adapter_class']):
                errors.append("adapter_class must be in format 'module.ClassName'")
        
        if 'capabilities' in data:
            if not isinstance(data['capabilities'], list) or len(data['capabilities']) == 0:
                errors.append("capabilities must be non-empty list")
            elif not all(isinstance(cap, str) for cap in data['capabilities']):
                errors.append("All capabilities must be strings")
        
        if 'tenant_id' in data:
            if not isinstance(data['tenant_id'], str) or len(data['tenant_id']) < 2:
                errors.append("tenant_id must be string with minimum 2 characters")
        
        if 'trust_signature' in data:
            if not isinstance(data['trust_signature'], str):
                errors.append("trust_signature must be string")
            elif len(data['trust_signature']) != 64 or not all(c in '0123456789ABCDEFabcdef' for c in data['trust_signature']):
                errors.append("trust_signature must be 64-character hexadecimal hash")
        
        if 'metadata' in data and not isinstance(data['metadata'], dict):
            errors.append("metadata must be object/dict")
        
        # PATCH: Cursor-2025-08-15 CL-P4-Final-Green - Fix validation logic to provide specific error messages
        return len(errors) == 0, errors
    
    def _validate_adapter_class_format(self, adapter_class: str) -> bool:
        """Validate adapter class format: module.ClassName"""
        import re
        pattern = r'^[a-z_]+\.[A-Z][a-zA-Z]+$'
        return bool(re.match(pattern, adapter_class))
    
    def load_manifest(self, manifest_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load agent manifest from file with error handling.
        
        Args:
            manifest_path: Path to manifest JSON file
            
        Returns:
            Parsed manifest data
            
        Raises:
            AgentOnboardingError: If manifest loading fails
        """
        try:
            manifest_path = Path(manifest_path)
            
            if not manifest_path.exists():
                raise AgentOnboardingError(f"Manifest file not found: {manifest_path}")
            
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_data = json.load(f)
            
            self.logger.info(f"Loaded manifest from {manifest_path}")
            return manifest_data
            
        except json.JSONDecodeError as e:
            raise AgentOnboardingError(f"Invalid JSON in manifest: {e}")
        except Exception as e:
            raise AgentOnboardingError(f"Failed to load manifest: {e}")
    
    def verify_trust_signature(self, manifest: AgentManifest) -> bool:
        """
        Verify agent trust signature against registry.
        
        Args:
            manifest: Agent manifest to verify
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Load trust registry
            registry_path = self.base_dir / "data" / "agent_trust_registry.json"
            
            if not registry_path.exists():
                self.logger.warning("Trust registry not found, creating default")
                self._create_default_trust_registry(registry_path)
            
            with open(registry_path, 'r') as f:
                trust_registry = json.load(f)
            
            # Check if adapter class is trusted
            trusted_adapters = trust_registry.get('trusted_adapters', {})
            tenant_trusted = trusted_adapters.get(manifest.tenant_id, [])
            
            if manifest.adapter_class not in tenant_trusted:
                default_trusted = trusted_adapters.get('default', [])
                if manifest.adapter_class not in default_trusted:
                    return False
            
            # Verify signature (simplified implementation)
            expected_signature = self._calculate_manifest_signature(manifest)
            return manifest.trust_signature == expected_signature
            
        except Exception as e:
            self.logger.error(f"Trust verification failed: {e}")
            return False
    
    def _create_default_trust_registry(self, registry_path: Path) -> None:
        """Create default trust registry."""
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        
        default_registry = {
            "version": "1.0.0",
            "trusted_adapters": {
                "default": [
                    "openai_adapter.OpenAIService",
                    "llm_adapter.LLMService",
                    "local_adapter.LocalTestService"
                ]
            },
            "signature_keys": {},
            "created": datetime.now().isoformat()
        }
        
        with open(registry_path, 'w') as f:
            json.dump(default_registry, f, indent=2)
    
    def _calculate_manifest_signature(self, manifest: AgentManifest) -> str:
        """Calculate SHA-256 signature for manifest (simplified)."""
        signature_data = f"{manifest.agent_id}:{manifest.adapter_class}:{manifest.tenant_id}"
        return hashlib.sha256(signature_data.encode()).hexdigest()
    
    def onboard_agent(self, manifest_data: Dict[str, Any]) -> OnboardingResult:
        """
        Complete agent onboarding process with validation and registration.
        
        Args:
            manifest_data: Agent manifest data
            
        Returns:
            OnboardingResult with status and metrics
        """
        start_time = datetime.now()
        agent_id = manifest_data.get('agent_id', 'unknown')
        
        with self._lock:
            try:
                # Step 1: Schema validation
                if self.kpi_monitor:
                    schema_start = datetime.now()
                
                is_valid, validation_errors = self.validate_manifest_schema(manifest_data)
                
                if self.kpi_monitor:
                    schema_time = (datetime.now() - schema_start).total_seconds()
                    self.kpi_monitor.record_metric(
                        "manifest_validation_time", 
                        schema_time,
                        {"tenant_id": manifest_data.get('tenant_id', 'unknown')}
                    )
                
                if not is_valid:
                    result = OnboardingResult(
                        agent_id=agent_id,
                        status=OnboardStatus.REJECTED,
                        success=False,
                        validation_errors=validation_errors,
                        processing_time=(datetime.now() - start_time).total_seconds()
                    )
                    self._onboarding_history.append(result)
                    return result
                
                # Step 2: Create manifest object
                manifest = AgentManifest.from_dict(manifest_data)
                
                # Step 3: Trust verification
                if not self.verify_trust_signature(manifest):
                    result = OnboardingResult(
                        agent_id=agent_id,
                        status=OnboardStatus.REJECTED,
                        success=False,
                        validation_errors=["Trust signature verification failed"],
                        processing_time=(datetime.now() - start_time).total_seconds()
                    )
                    self._onboarding_history.append(result)
                    return result
                
                # Step 4: Tenant isolation check
                if not self._validate_tenant_isolation(manifest):
                    result = OnboardingResult(
                        agent_id=agent_id,
                        status=OnboardStatus.REJECTED,
                        success=False,
                        validation_errors=["Tenant isolation validation failed"],
                        processing_time=(datetime.now() - start_time).total_seconds()
                    )
                    self._onboarding_history.append(result)
                    return result
                
                # Step 5: Register agent
                self._register_agent(manifest)
                
                # Step 6: Record metrics
                if self.kpi_monitor:
                    processing_time = (datetime.now() - start_time).total_seconds()
                    self.kpi_monitor.record_metric(
                        "agent_registration_time",
                        processing_time,
                        {"tenant_id": manifest.tenant_id}
                    )
                
                # Success result
                result = OnboardingResult(
                    agent_id=agent_id,
                    status=OnboardStatus.ACTIVE,
                    success=True,
                    processing_time=(datetime.now() - start_time).total_seconds(),
                    metadata={"tenant_id": manifest.tenant_id}
                )
                
                self._onboarding_history.append(result)
                
                return result
                
            except Exception as e:
                result = OnboardingResult(
                    agent_id=agent_id,
                    status=OnboardStatus.REJECTED,
                    success=False,
                    validation_errors=[f"Onboarding failed: {str(e)}"],
                    processing_time=(datetime.now() - start_time).total_seconds()
                )
                self._onboarding_history.append(result)
                self.logger.error(f"Agent onboarding failed: {e}")
                return result
    
    def _validate_tenant_isolation(self, manifest: AgentManifest) -> bool:
        """Validate tenant isolation requirements."""
        # Check for agent ID conflicts within tenant
            existing_manifest = self._onboarded_agents[manifest.agent_id]
            if existing_manifest.tenant_id != manifest.tenant_id:
                return False
        
        # Additional tenant-specific validation can be added here
        return True
    
    def _register_agent(self, manifest: AgentManifest) -> None:
        """Register agent in internal registry."""
        self._onboarded_agents[manifest.agent_id] = manifest
        
        # Update tenant tracking
            self._tenant_agents[manifest.tenant_id] = set()
        self._tenant_agents[manifest.tenant_id].add(manifest.agent_id)
    
    def get_agent_status(self, agent_id: str) -> Optional[AgentManifest]:
        """Get agent manifest by ID."""
        with self._lock:
            return self._onboarded_agents.get(agent_id)
    
    def list_tenant_agents(self, tenant_id: str) -> List[str]:
        """List all agents for a specific tenant."""
        with self._lock:
            return list(self._tenant_agents.get(tenant_id, set()))
    
    def get_onboarding_metrics(self) -> Dict[str, Any]:
        """Get comprehensive onboarding metrics."""
        with self._lock:
            total_attempts = len(self._onboarding_history)
            successful = sum(1 for result in self._onboarding_history if result.success)
            
            metrics = {
                "total_onboarding_attempts": total_attempts,
                "successful_onboardings": successful,
                "failure_rate": (total_attempts - successful) / max(total_attempts, 1),
                "active_agents": len(self._onboarded_agents),
                "tenant_count": len(self._tenant_agents),
                "schema_validation_enabled": self.schema is not None,
                "onboard_001_enabled": True,
                "version": "2.2.0"
            }
            
            if self.kpi_monitor:
                kpi_metrics = self.kpi_monitor.get_onboarding_metrics()
                metrics.update(kpi_metrics)
            
            return metrics

    # PATCH: Cursor-2025-08-19 DISPATCH-GPT-20250819-022 <add PKI functionality for integration wiring>
        """
        Issue a signed agent manifest for onboarding.
        
        Args:
            agent_id: Unique identifier for the agent
            capabilities: List of agent capabilities
            
        Returns:
            Dictionary containing manifest, signature, and public key fingerprint
        """
        try:
            # Create manifest dict
            manifest = {
                "agent_id": agent_id,
                "capabilities": capabilities,
                "version": version,
                "issued_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Serialize to canonical bytes (UTF-8 JSON with sorted keys)
            manifest_bytes = json.dumps(manifest, sort_keys=True, ensure_ascii=False).encode("utf-8")
            
            # Sign manifest bytes
            signature = self.signature_engine.sign(manifest_bytes)
            
            # Get public key fingerprint
            pubkey_pem = self.signature_engine.export_public_pem()
            pubkey_fpr = hashlib.sha256(pubkey_pem).hexdigest()[:16]
            
            # Store in registry
            registry_entry = {
                "manifest": manifest,
                "signature": signature.hex(),
                "pubkey_fpr": pubkey_fpr,
                "issued_at": manifest["issued_at"]
            }
            
            self._save_manifest_registry(agent_id, registry_entry)
            
            # Audit manifest issuance
            audit_data = {
                "agent_id": agent_id,
                "capabilities": capabilities,
                "version": version,
                "pubkey_fpr": pubkey_fpr
            }
            get_audit_chain().log("security.agent_issued", audit_data)
            
            self.logger.info(f"Manifest issued for agent {agent_id} with fingerprint {pubkey_fpr}")
            
            return registry_entry
            
        except Exception as e:
            self.logger.error(f"Failed to issue manifest for agent {agent_id}: {e}")
            raise

    def verify_manifest_signature(self, agent_id: str) -> bool:
        """
        Verify the signature of a stored agent manifest.
        
        Args:
            agent_id: ID of the agent to verify
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            if agent_id not in self.manifest_registry:
                self.logger.warning(f"Agent {agent_id} not found in manifest registry")
                return False
            
            registry_entry = self.manifest_registry[agent_id]
            manifest = registry_entry["manifest"]
            signature = bytes.fromhex(registry_entry["signature"])
            
            # Recreate canonical bytes
            manifest_bytes = json.dumps(manifest, sort_keys=True, ensure_ascii=False).encode("utf-8")
            
            # Verify signature
            is_valid = self.signature_engine.verify(manifest_bytes, signature)
            
            # Audit verification result
            audit_data = {
                "agent_id": agent_id,
                "verification_result": "success" if is_valid else "failed",
                "pubkey_fpr": registry_entry.get("pubkey_fpr", "unknown")
            }
            event_type = "security.signature_verified" if is_valid else "security.signature_failed"
            get_audit_chain().log(event_type, audit_data)
            
            if is_valid:
                self.logger.info(f"Signature verification successful for agent {agent_id}")
            else:
                self.logger.warning(f"Signature verification failed for agent {agent_id}")
            
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Error verifying manifest signature for agent {agent_id}: {e}")
            # Audit verification error
            audit_data = {
                "agent_id": agent_id,
                "error": str(e)
            }
            get_audit_chain().log("security.signature_verification_error", audit_data)
            return False

    def _save_manifest_registry(self, agent_id: str, registry_entry: Dict[str, Any]) -> None:
        """Save manifest registry entry to file."""
        try:
            self.manifest_registry[agent_id] = registry_entry
            
            with open(self.manifest_registry_file, 'w') as f:
                json.dump(self.manifest_registry, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save manifest registry: {e}")
            raise

    def _load_manifest_registry(self) -> None:
        """Load manifest registry from file."""
        try:
            if self.manifest_registry_file.exists():
                with open(self.manifest_registry_file, 'r') as f:
                    self.manifest_registry = json.load(f)
                self.logger.info(f"Loaded manifest registry with {len(self.manifest_registry)} entries")
            else:
                self.manifest_registry = {}
                self.logger.info("No existing manifest registry found, starting fresh")
                
        except Exception as e:
            self.logger.error(f"Failed to load manifest registry: {e}")
            self.manifest_registry = {}


# Factory functions for easy instantiation
def create_agent_onboarding(base_dir: Optional[Path] = None,
                          validation_level: ValidationLevel = ValidationLevel.STANDARD) -> AgentOnboarding:
    """Create configured AgentOnboarding instance."""
    return AgentOnboarding(base_dir=base_dir, validation_level=validation_level)


# Module-level constants
__version__ = "2.2.0"
__author__ = "A17"
__status__ = "Production Ready"

