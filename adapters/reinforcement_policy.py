"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.


"""
IOA Reinforcement Policy: Bayesian Trust Scoring System

Provides Bayesian trust scoring for agent reliability assessment with
persistent storage, configurable learning rates, comprehensive audit logging,
and drift detection using Gini coefficient analysis.

ENHANCED FEATURES (v2.5.0):
- Persistent trust scores saved to agent_trust_registry.json
- Configurable update factor for different learning rates
- Comprehensive audit logging for all trust score changes
- Beta distribution parameters properly documented and validated
- Enhanced error handling and recovery mechanisms
- Integration with AuditChain for governance compliance
- PATCH: Cursor-2025-09-05 - Added drift detection using Gini coefficient

PATCH: Gemini-2025-08-11 - Made update_factor configurable
REFACTOR: Claude-2025-08-12 - Added persistence and audit logging
PATCH: Cursor-2025-08-19 - Added AuditChain integration
PATCH: Cursor-2025-09-05 - Added drift detection with Gini coefficient

Beta Distribution Parameters:
- Alpha (α): Represents successful interactions + prior positive belief
- Beta (β): Represents failed interactions + prior negative belief
- Trust Score: Mean of Beta(α, β) = α / (α + β)
- Confidence: Precision increases with α + β (more interactions)
"""

from scipy.stats import beta
import json
import logging
import math
from pathlib import Path
from typing import Dict, Tuple, Optional, Any, List
from datetime import datetime
from audit_logger import AuditLogger  # REFACTOR: Claude-2025-08-12
# PATCH: Cursor-2025-08-19 DISPATCH-GPT-20250819-022 <add audit hooks for integration wiring>
from .governance.audit_chain import get_audit_chain

# REFACTOR: Claude-2025-08-12 - Standardized logging setup
logger = logging.getLogger(__name__)
audit_logger = AuditLogger()

class ReinforcementPolicy:
    """
    Bayesian trust scoring system for agent reliability assessment.
    
    ENHANCED FEATURES (v2.5.0):
    - Persistent trust scores saved to agent_trust_registry.json
    - Configurable update factor for different learning rates
    - Comprehensive audit logging for all trust score changes
    - Beta distribution parameters properly documented and validated
    - Enhanced error handling and recovery mechanisms
    - PATCH: Cursor-2025-09-05 - Added drift detection using Gini coefficient
    
    PATCH: Gemini-2025-08-11 - Made update_factor configurable
    REFACTOR: Claude-2025-08-12 - Added persistence and audit logging
    PATCH: Cursor-2025-09-05 - Added drift detection with Gini coefficient
    
    Beta Distribution Parameters:
    - Alpha (α): Represents successful interactions + prior positive belief
    - Beta (β): Represents failed interactions + prior negative belief
    - Trust Score: Mean of Beta(α, β) = α / (α + β)
    - Confidence: Precision increases with α + β (more interactions)
    """
    
    def __init__(self, update_factor: float = 10, registry_path: str = "agent_trust_registry.json"):
        """
        Initialize reinforcement policy with configurable parameters.
        
        Args:
            update_factor: Scaling factor for Bayesian updates (higher = faster learning)
            registry_path: Path to persist trust scores
        """
        self.update_factor = update_factor  # PATCH: Gemini-2025-08-11 - Configurable
        self.registry_path = Path(registry_path)
        self.trust_scores: Dict[str, Tuple[float, float]] = {}
        
        # PATCH: Cursor-2025-09-05 DISPATCH-EXEC-20250905-CONNECTOR-10K-TEST-&-PATCHES
        # Drift detection parameters
        self.drift_threshold = 0.3  # Gini coefficient threshold for drift detection
        self.drift_history: List[Dict[str, Any]] = []
        self.last_drift_check = None
        
        # REFACTOR: Claude-2025-08-12 - Load persistent trust scores
        self._load_trust_scores()
        
        logger.info(f"ReinforcementPolicy v2.5.0 initialized with update_factor={update_factor} and drift detection")
        logger.info(f"Loaded {len(self.trust_scores)} existing trust scores from {registry_path}")
        
        audit_logger.log_system_event("reinforcement_policy_init", {
            "update_factor": update_factor,
            "registry_path": str(registry_path),
            "loaded_agents": len(self.trust_scores),
            "drift_threshold": self.drift_threshold
        })

    def _load_trust_scores(self):
        """
        Load trust scores from persistent storage.
        
        REFACTOR: Claude-2025-08-12 - Added persistence for trust_scores
        """
        try:
            if self.registry_path.exists():
                with open(self.registry_path, 'r') as f:
                    data = json.load(f)
                    
                    # Convert loaded data back to tuple format
                    for agent_id, params in data.get('trust_scores', {}).items():
                        if isinstance(params, list) and len(params) == 2:
                            self.trust_scores[agent_id] = (float(params[0]), float(params[1]))
                        else:
                            logger.warning(f"Invalid trust score format for agent {agent_id}: {params}")
                    
                    logger.info(f"Loaded trust scores for {len(self.trust_scores)} agents")
            else:
                logger.info(f"No existing trust registry found at {self.registry_path}")
                
        except Exception as e:
            logger.error(f"Failed to load trust scores from {self.registry_path}: {e}")
            audit_logger.log_error("trust_scores_load_failure", {
                "registry_path": str(self.registry_path),
                "error": str(e)
            })
            # Continue with empty trust scores on load failure

    def _save_trust_scores(self):
        """
        Save trust scores to persistent storage.
        
        REFACTOR: Claude-2025-08-12 - Persistence implementation
        """
        try:
            # Ensure directory exists
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert tuple format to JSON-serializable format
            data = {
                'trust_scores': {
                    agent_id: [float(params[0]), float(params[1])]
                    for agent_id, params in self.trust_scores.items()
                },
                'metadata': {
                    'update_factor': self.update_factor,
                    'last_saved': datetime.now().isoformat(),
                    'version': '2.5.0',
                    'total_agents': len(self.trust_scores),
                    'drift_threshold': self.drift_threshold
                }
            }
            
            with open(self.registry_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved trust scores for {len(self.trust_scores)} agents")
            
        except Exception as e:
            logger.error(f"Failed to save trust scores to {self.registry_path}: {e}")
            audit_logger.log_error("trust_scores_save_failure", {
                "registry_path": str(self.registry_path),
                "error": str(e)
            })

    def calculate_gini_coefficient(self, values: List[float]) -> float:
        """
        Calculate Gini coefficient for drift detection.
        
        PATCH: Cursor-2025-09-05 DISPATCH-EXEC-20250905-CONNECTOR-10K-TEST-&-PATCHES
        Gini coefficient measures inequality in distribution (0 = perfect equality, 1 = perfect inequality).
        
        Args:
            values: List of numeric values to analyze
            
        Returns:
            Gini coefficient between 0.0 and 1.0
        """
        if not values or len(values) < 2:
            return 0.0
        
        try:
            # Sort values in ascending order
            sorted_values = sorted(values)
            n = len(sorted_values)
            
            # Calculate Gini coefficient using the formula:
            # G = (2 * sum(i * x_i) - (n + 1) * sum(x_i)) / (n * sum(x_i))
            # where x_i are the sorted values and i is the index (1-based)
            
            sum_ix = sum((i + 1) * x for i, x in enumerate(sorted_values))
            sum_x = sum(sorted_values)
            
            if sum_x == 0:
                return 0.0
            
            gini = (2 * sum_ix - (n + 1) * sum_x) / (n * sum_x)
            
            # Ensure result is in valid range [0, 1]
            return max(0.0, min(1.0, gini))
            
        except Exception as e:
            logger.error(f"Error calculating Gini coefficient: {e}")
            return 0.0

    def detect_drift(self) -> Dict[str, Any]:
        """
        Detect drift in trust score distribution using Gini coefficient.
        
        PATCH: Cursor-2025-09-05 DISPATCH-EXEC-20250905-CONNECTOR-10K-TEST-&-PATCHES
        Analyzes trust score distribution to detect anomalies and potential system drift.
        
        Returns:
            Dictionary containing drift analysis results
        """
        try:
            if len(self.trust_scores) < 3:
                return {
                    "drift_detected": False,
                    "reason": "Insufficient agents for drift detection",
                    "gini_coefficient": 0.0,
                    "threshold": self.drift_threshold,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Extract trust scores
            trust_scores = [self.get_trust_score(agent_id) for agent_id in self.trust_scores.keys()]
            
            # Calculate Gini coefficient
            gini_coefficient = self.calculate_gini_coefficient(trust_scores)
            
            # Determine if drift is detected
            drift_detected = gini_coefficient > self.drift_threshold
            
            # Calculate additional statistics
            mean_trust = sum(trust_scores) / len(trust_scores)
            variance = sum((x - mean_trust) ** 2 for x in trust_scores) / len(trust_scores)
            std_dev = math.sqrt(variance)
            
            drift_result = {
                "drift_detected": drift_detected,
                "gini_coefficient": gini_coefficient,
                "threshold": self.drift_threshold,
                "statistics": {
                    "mean_trust": mean_trust,
                    "variance": variance,
                    "std_dev": std_dev,
                    "min_trust": min(trust_scores),
                    "max_trust": max(trust_scores),
                    "agent_count": len(trust_scores)
                },
                "timestamp": datetime.now().isoformat()
            }
            
            if drift_detected:
                drift_result["severity"] = "high" if gini_coefficient > 0.7 else "medium"
                drift_result["recommendation"] = "Review agent trust scores and investigate anomalies"
                
                logger.warning(f"Drift detected! Gini coefficient: {gini_coefficient:.3f} > {self.drift_threshold}")
                
                # Log drift detection for audit
                audit_logger.log_system_event("drift_detected", drift_result)
                
                # Audit via AuditChain
                try:
                    get_audit_chain().log("governance.drift_detection", drift_result)
                except Exception as e:
                    logger.warning(f"Failed to log drift detection to AuditChain: {e}")
            else:
                logger.info(f"No drift detected. Gini coefficient: {gini_coefficient:.3f} <= {self.drift_threshold}")
            
            # Store drift history
            self.drift_history.append(drift_result)
            self.last_drift_check = datetime.now()
            
            # Keep only last 100 drift checks to prevent memory bloat
            if len(self.drift_history) > 100:
                self.drift_history = self.drift_history[-100:]
            
            return drift_result
            
        except Exception as e:
            logger.error(f"Error in drift detection: {e}")
            return {
                "drift_detected": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def get_drift_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get drift detection history.
        
        PATCH: Cursor-2025-09-05 DISPATCH-EXEC-20250905-CONNECTOR-10K-TEST-&-PATCHES
        
        Args:
            limit: Maximum number of historical drift checks to return
            
        Returns:
            List of drift detection results
        """
        return self.drift_history[-limit:] if self.drift_history else []

    def set_drift_threshold(self, threshold: float):
        """
        Set drift detection threshold.
        
        PATCH: Cursor-2025-09-05 DISPATCH-EXEC-20250905-CONNECTOR-10K-TEST-&-PATCHES
        
        Args:
            threshold: New Gini coefficient threshold (0.0 to 1.0)
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"Drift threshold must be between 0.0 and 1.0, got {threshold}")
        
        old_threshold = self.drift_threshold
        self.drift_threshold = threshold
        
        logger.info(f"Drift threshold updated: {old_threshold} -> {threshold}")
        
        audit_logger.log_system_event("drift_threshold_updated", {
            "old_threshold": old_threshold,
            "new_threshold": threshold,
            "timestamp": datetime.now().isoformat()
        })

    def process_reward(self, agent_id: str, confidence: float):
        """
        Update trust score with reward using beta distribution.
        
        PATCH: Gemini-2025-08-11 - Use configurable update_factor
        REFACTOR: Claude-2025-08-12 - Enhanced logging and validation
        PATCH: Cursor-2025-09-05 - Added drift detection after updates
        
        Args:
            agent_id: Unique identifier for the agent
            confidence: Reward confidence level (0.0 to 1.0)
            
        Raises:
            ValueError: If confidence is not in valid range
        """
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {confidence}")
        
        try:
            # Get current parameters (default to uniform prior: α=1, β=1)
            prior_alpha, prior_beta = self.trust_scores.get(agent_id, (1.0, 1.0))
            
            # Bayesian update: add evidence weighted by confidence and update factor
            posterior_alpha = prior_alpha + (confidence * self.update_factor)
            posterior_beta = prior_beta + ((1 - confidence) * self.update_factor)
            
            # Store updated parameters
            self.trust_scores[agent_id] = (posterior_alpha, posterior_beta)
            
            # Calculate current trust score for logging
            trust_score = posterior_alpha / (posterior_alpha + posterior_beta)
            
            logger.info(f"Processed reward for {agent_id}: confidence={confidence:.3f}, "
                       f"trust_score={trust_score:.3f}, params=({posterior_alpha:.2f}, {posterior_beta:.2f})")
            
            # REFACTOR: Claude-2025-08-12 - Audit logging
            audit_logger.log_trust_update("reward", {
                "agent_id": agent_id,
                "confidence": confidence,
                "prior_params": [prior_alpha, prior_beta],
                "posterior_params": [posterior_alpha, posterior_beta],
                "trust_score": trust_score,
                "update_factor": self.update_factor
            })
            
            # PATCH: Cursor-2025-08-19 DISPATCH-GPT-20250819-022 <add audit hooks for integration wiring>
            # Audit trust update via AuditChain
            audit_data = {
                "agent_id": agent_id,
                "old_alpha": prior_alpha,
                "old_beta": prior_beta,
                "new_alpha": posterior_alpha,
                "new_beta": posterior_beta,
                "rationale": f"reward_confidence_{confidence:.3f}",
                "update_factor": self.update_factor,
                "trust_score": trust_score
            }
            get_audit_chain().log("governance.trust_update", audit_data)
            
            # PATCH: Cursor-2025-09-05 DISPATCH-EXEC-20250905-CONNECTOR-10K-TEST-&-PATCHES
            # Check for drift after trust score update
            if len(self.trust_scores) >= 3:
                drift_result = self.detect_drift()
                if drift_result.get("drift_detected"):
                    logger.warning(f"Drift detected after reward update for {agent_id}: {drift_result}")
            
            # Save to persistent storage
            self._save_trust_scores()
            
        except Exception as e:
            logger.error(f"Failed to process reward for agent {agent_id}: {e}")
            audit_logger.log_error("reward_processing_failure", {
                "agent_id": agent_id,
                "confidence": confidence,
                "error": str(e)
            })
            raise

    def process_punishment(self, agent_id: str, severity: float):
        """
        Update trust score with punishment using beta distribution.
        
        PATCH: Gemini-2025-08-11 - Use configurable update_factor
        REFACTOR: Claude-2025-08-12 - Enhanced logging and validation
        PATCH: Cursor-2025-09-05 - Added drift detection after updates
        
        Args:
            agent_id: Unique identifier for the agent
            severity: Punishment severity level (0.0 to 1.0)
            
        Raises:
            ValueError: If severity is not in valid range
        """
        if not 0.0 <= severity <= 1.0:
            raise ValueError(f"Severity must be between 0.0 and 1.0, got {severity}")
        
        try:
            # Get current parameters (default to uniform prior: α=1, β=1)
            prior_alpha, prior_beta = self.trust_scores.get(agent_id, (1.0, 1.0))
            
            # Bayesian update: punishment reduces alpha, increases beta
            posterior_alpha = prior_alpha + ((1 - severity) * self.update_factor)
            posterior_beta = prior_beta + (severity * self.update_factor)
            
            # Store updated parameters
            self.trust_scores[agent_id] = (posterior_alpha, posterior_beta)
            
            # Calculate current trust score for logging
            trust_score = posterior_alpha / (posterior_alpha + posterior_beta)
            
            logger.info(f"Processed punishment for {agent_id}: confidence={severity:.3f}, "
                       f"trust_score={trust_score:.3f}, params=({posterior_alpha:.2f}, {posterior_beta:.2f})")
            
            # REFACTOR: Claude-2025-08-12 - Audit logging
            audit_logger.log_trust_update("punishment", {
                "agent_id": agent_id,
                "severity": severity,
                "prior_params": [prior_alpha, prior_beta],
                "posterior_params": [posterior_alpha, posterior_beta],
                "trust_score": trust_score,
                "update_factor": self.update_factor
            })
            
            # PATCH: Cursor-2025-08-19 DISPATCH-GPT-20250819-022 <add audit hooks for integration wiring>
            # Audit trust update via AuditChain
            audit_data = {
                "agent_id": agent_id,
                "old_alpha": prior_alpha,
                "old_beta": prior_beta,
                "new_alpha": posterior_alpha,
                "new_beta": posterior_beta,
                "rationale": f"punishment_severity_{severity:.3f}",
                "update_factor": self.update_factor,
                "trust_score": trust_score
            }
            get_audit_chain().log("governance.trust_update", audit_data)
            
            # PATCH: Cursor-2025-09-05 DISPATCH-EXEC-20250905-CONNECTOR-10K-TEST-&-PATCHES
            # Check for drift after trust score update
            if len(self.trust_scores) >= 3:
                drift_result = self.detect_drift()
                if drift_result.get("drift_detected"):
                    logger.warning(f"Drift detected after punishment update for {agent_id}: {drift_result}")
            
            # Save to persistent storage
            self._save_trust_scores()
            
        except Exception as e:
            logger.error(f"Failed to process punishment for agent {agent_id}: {e}")
            audit_logger.log_error("punishment_processing_failure", {
                "agent_id": agent_id,
                "severity": severity,
                "error": str(e)
            })
            raise

    def get_trust_score(self, agent_id: str) -> float:
        """
        Get current trust score for an agent.
        
        REFACTOR: Claude-2025-08-12 - Added trust score retrieval method
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            Trust score between 0.0 and 1.0 (mean of beta distribution)
        """
        try:
            alpha, beta_param = self.trust_scores.get(agent_id, (1.0, 1.0))
            trust_score = alpha / (alpha + beta_param)
            
            logger.debug(f"Trust score for {agent_id}: {trust_score:.3f}")
            return trust_score
            
        except Exception as e:
            logger.error(f"Failed to calculate trust score for agent {agent_id}: {e}")
            return 0.5  # Return neutral score on error

    def get_trust_confidence(self, agent_id: str) -> float:
        """
        Get confidence level in the trust score (based on interaction count).
        
        REFACTOR: Claude-2025-08-12 - Added confidence calculation
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            Confidence level between 0.0 and 1.0
        """
        try:
            alpha, beta_param = self.trust_scores.get(agent_id, (1.0, 1.0))
            
            # Confidence based on total evidence (higher α + β = more confident)
            total_evidence = alpha + beta_param - 2.0  # Subtract priors
            
            # Normalize to 0-1 range (assuming max ~100 interactions for full confidence)
            confidence = min(total_evidence / 100.0, 1.0)
            
            return confidence
            
        except Exception as e:
            logger.error(f"Failed to calculate trust confidence for agent {agent_id}: {e}")
            return 0.0

    def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        """
        Get comprehensive statistics for an agent.
        
        REFACTOR: Claude-2025-08-12 - Added comprehensive agent statistics
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            Dict with trust score, confidence, parameters, and derived metrics
        """
        try:
            alpha, beta_param = self.trust_scores.get(agent_id, (1.0, 1.0))
            
            trust_score = alpha / (alpha + beta_param)
            total_evidence = alpha + beta_param - 2.0
            confidence = min(total_evidence / 100.0, 1.0)
            
            # Calculate variance (uncertainty in trust score)
            variance = (alpha * beta_param) / ((alpha + beta_param) ** 2 * (alpha + beta_param + 1))
            
            return {
                "agent_id": agent_id,
                "trust_score": trust_score,
                "confidence": confidence,
                "uncertainty": variance,
                "parameters": {"alpha": alpha, "beta": beta_param},
                "total_interactions": total_evidence,
                "update_factor": self.update_factor
            }
            
        except Exception as e:
            logger.error(f"Failed to get agent stats for {agent_id}: {e}")
            return {"agent_id": agent_id, "error": str(e)}

    def list_all_agents(self) -> List[Dict[str, Any]]:
        """
        Get statistics for all tracked agents.
        
        REFACTOR: Claude-2025-08-12 - Added bulk agent statistics
        
        Returns:
            List of agent statistics dictionaries
        """
        try:
            return [self.get_agent_stats(agent_id) for agent_id in self.trust_scores.keys()]
        except Exception as e:
            return []

    def reset_agent_score(self, agent_id: str, reason: str = "manual_reset"):
        """
        Reset an agent's trust score to neutral (uniform prior).
        
        REFACTOR: Claude-2025-08-12 - Added agent score reset capability
        
        Args:
            agent_id: Agent to reset
            reason: Reason for reset (for audit logging)
        """
        try:
            old_params = self.trust_scores.get(agent_id, (1.0, 1.0))
            self.trust_scores[agent_id] = (1.0, 1.0)
            
            logger.info(f"Reset trust score for {agent_id} (reason: {reason})")
            
            audit_logger.log_trust_update("reset", {
                "agent_id": agent_id,
                "reason": reason,
                "old_params": list(old_params),
                "new_params": [1.0, 1.0]
            })
            
            self._save_trust_scores()
            
        except Exception as e:
            logger.error(f"Failed to reset agent score for {agent_id}: {e}")
            raise

    def export_trust_data(self, export_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Export all trust data for backup or analysis.
        
        REFACTOR: Claude-2025-08-12 - Added data export capability
        
        Args:
            export_path: Optional path to save export file
            
        Returns:
            Complete trust data export
        """
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "version": "2.5.0",
                "update_factor": self.update_factor,
                "agent_count": len(self.trust_scores),
                "agents": [self.get_agent_stats(agent_id) for agent_id in self.trust_scores.keys()],
                "drift_threshold": self.drift_threshold,
                "drift_history": self.get_drift_history(limit=100)
            }
            
            if export_path:
                export_file = Path(export_path)
                export_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(export_file, 'w') as f:
                    json.dump(export_data, f, indent=2)
                
                logger.info(f"Exported trust data to {export_path}")
            
            return export_data
            
        except Exception as e:
            logger.error(f"Failed to export trust data: {e}")
            audit_logger.log_error("trust_export_failure", {"error": str(e)})
            raise