"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ModelFactor(Enum):
    """Energy consumption factors for different AI models."""
    # PATCH: Cursor-2025-01-06 DISPATCH-GOV-20250906-SUSTAINABILITY
    # Model factors based on approximate energy consumption per 100k tokens
    GPT_4 = 0.0025  # kWh per 100k tokens
    GPT_3_5_TURBO = 0.0015
    CLAUDE_3_OPUS = 0.0030
    CLAUDE_3_SONNET = 0.0020
    CLAUDE_3_HAIKU = 0.0010
    GEMINI_PRO = 0.0020
    LLAMA_2_70B = 0.0040
    LLAMA_2_13B = 0.0020
    LLAMA_2_7B = 0.0010
    MISTRAL_7B = 0.0012
    DEFAULT = 0.0020  # Conservative default


@dataclass
class EnergyEstimate:
    """Energy consumption estimate for an operation."""
    tokens_processed: int
    model_factor: float
    energy_kwh: float
    carbon_kg_co2: float = 0.0
    region: str = "global"
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class EnergyCalculator:
    """Calculator for AI model energy consumption and carbon footprint."""
    
    # PATCH: Cursor-2025-01-06 DISPATCH-GOV-20250906-SUSTAINABILITY
    # Carbon intensity factors by region (kg CO2 per kWh)
    CARBON_INTENSITY = {
        "global": 0.475,  # Global average
        "US": 0.410,      # US average
        "EU": 0.275,      # EU average (more renewable)
        "CA": 0.120,      # Canada (mostly hydro/nuclear)
        "AU": 0.820,      # Australia (coal-heavy)
        "CN": 0.680,      # China (coal-heavy)
        "IN": 0.820,      # India (coal-heavy)
    }
    
    def __init__(self, default_region: str = "global", model_factors: dict = None):
        self.default_region = default_region
        # PATCH: Cursor-2025-09-15 DISPATCH-GOV-20250915-SUSTAINABILITY-PACK-V0
        # Use provided model factors or fallback to enum values
        if model_factors:
            self._model_factors = model_factors
        else:
            self._model_factors = {factor.name: factor.value for factor in ModelFactor}
    
    def calculate_energy(self, 
                        tokens: int, 
                        model_name: str = "DEFAULT",
                        region: Optional[str] = None) -> EnergyEstimate:
        """
        Calculate energy consumption for token processing.
        
        Args:
            tokens: Number of tokens processed
            model_name: Name of the AI model
            region: Geographic region for carbon intensity
            
        Returns:
            EnergyEstimate with consumption details
        """
        region = region or self.default_region
        
        # Get model factor
        model_factor = self._get_model_factor(model_name)
        
        # Calculate energy (tokens / 100k * factor)
        energy_kwh = (tokens / 100_000) * model_factor
        
        # Calculate carbon footprint
        carbon_intensity = self.CARBON_INTENSITY.get(region, self.CARBON_INTENSITY["global"])
        carbon_kg_co2 = energy_kwh * carbon_intensity
        
        estimate = EnergyEstimate(
            tokens_processed=tokens,
            model_factor=model_factor,
            energy_kwh=energy_kwh,
            carbon_kg_co2=carbon_kg_co2,
            region=region,
            metadata={
                "model_name": model_name,
                "carbon_intensity": carbon_intensity,
                "calculation_method": "tokens_per_100k_factor"
            }
        )
        
        logger.debug(f"Energy calculated: {tokens} tokens -> {energy_kwh:.6f} kWh "
                    f"({carbon_kg_co2:.6f} kg CO2) in {region}")
        
        return estimate
    
    def _get_model_factor(self, model_name: str) -> float:
        """Get energy factor for a model by name."""
        # Try exact match first
        if model_name in self._model_factors:
            return self._model_factors[model_name]
        
        # Try partial matching for common patterns
        model_lower = model_name.lower()
        
        if "gpt-4" in model_lower:
            return ModelFactor.GPT_4.value
        elif "gpt-3.5" in model_lower or "gpt-3" in model_lower:
            return ModelFactor.GPT_3_5_TURBO.value
        elif "claude-3-opus" in model_lower:
            return ModelFactor.CLAUDE_3_OPUS.value
        elif "claude-3-sonnet" in model_lower:
            return ModelFactor.CLAUDE_3_SONNET.value
        elif "claude-3-haiku" in model_lower:
            return ModelFactor.CLAUDE_3_HAIKU.value
        elif "gemini-pro" in model_lower:
            return ModelFactor.GEMINI_PRO.value
        elif "llama-2-70b" in model_lower:
            return ModelFactor.LLAMA_2_70B.value
        elif "llama-2-13b" in model_lower:
            return ModelFactor.LLAMA_2_13B.value
        elif "llama-2-7b" in model_lower:
            return ModelFactor.LLAMA_2_7B.value
        elif "mistral-7b" in model_lower:
            return ModelFactor.MISTRAL_7B.value
        else:
            logger.warning(f"Unknown model '{model_name}', using default factor")
            return ModelFactor.DEFAULT.value
    
    def estimate_tokens_from_text(self, text: str) -> int:
        """
        Rough estimation of token count from text.
        
        This is a simplified estimation. In production, use the actual
        tokenizer for the specific model.
        """
        # Rough approximation: 1 token ≈ 4 characters for English text
        return len(text) // 4
    
    def get_region_carbon_intensity(self, region: str) -> float:
        """Get carbon intensity for a specific region."""
        return self.CARBON_INTENSITY.get(region, self.CARBON_INTENSITY["global"])
    
    def calculate_batch_energy(self, 
                              operations: list,
                              region: Optional[str] = None) -> EnergyEstimate:
        """
        Calculate total energy for a batch of operations.
        
        Args:
            operations: List of dicts with 'tokens' and 'model' keys
            region: Geographic region for carbon intensity
            
        Returns:
            Combined EnergyEstimate for all operations
        """
        total_tokens = 0
        total_energy = 0.0
        total_carbon = 0.0
        region = region or self.default_region
        
        for op in operations:
            tokens = op.get("tokens", 0)
            model = op.get("model", "DEFAULT")
            
            estimate = self.calculate_energy(tokens, model, region)
            total_tokens += estimate.tokens_processed
            total_energy += estimate.energy_kwh
            total_carbon += estimate.carbon_kg_co2
        
        return EnergyEstimate(
            tokens_processed=total_tokens,
            model_factor=0.0,  # Mixed models
            energy_kwh=total_energy,
            carbon_kg_co2=total_carbon,
            region=region,
            metadata={
                "operation_count": len(operations),
                "calculation_method": "batch_aggregation"
            }
        )
