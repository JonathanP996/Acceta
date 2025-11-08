"""
Phoneme Deviation Model
PyTorch model or heuristic to compute deviation scores from target accent
"""

import os
import logging
from typing import Dict, List, Any
import numpy as np

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    nn = None  # Set to None if not available
    logger.warning("PyTorch not available, using heuristic deviation scoring")


if TORCH_AVAILABLE:
    class PhonemeDeviationModel(nn.Module):
        """Simple neural network for phoneme deviation scoring"""
        
        def __init__(self, input_dim: int = 18, hidden_dim: int = 64):
            super().__init__()
            self.fc1 = nn.Linear(input_dim, hidden_dim)
            self.fc2 = nn.Linear(hidden_dim, hidden_dim // 2)
            self.fc3 = nn.Linear(hidden_dim // 2, 1)
            self.relu = nn.ReLU()
            self.sigmoid = nn.Sigmoid()
        
        def forward(self, x):
            x = self.relu(self.fc1(x))
            x = self.relu(self.fc2(x))
            x = self.sigmoid(self.fc3(x))
            return x
else:
    # Dummy class if PyTorch not available
    class PhonemeDeviationModel:
        def __init__(self, *args, **kwargs):
            pass


# Global model instance (will be loaded if available)
_model = None
_device = "cpu"


def load_model(model_path: str = None):
    """Load pre-trained deviation model"""
    global _model, _device
    
    if not TORCH_AVAILABLE:
        logger.warning("PyTorch not available, model not loaded")
        return
    
    try:
        if model_path and os.path.exists(model_path):
            _model = PhonemeDeviationModel()
            _model.load_state_dict(torch.load(model_path, map_location=_device))
            _model.eval()
            logger.info(f"Loaded deviation model from {model_path}")
        else:
            # Initialize untrained model (for MVP)
            _model = PhonemeDeviationModel()
            _model.eval()
            logger.info("Using untrained deviation model (heuristic mode)")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        _model = None


async def compute_phoneme_deviations(
    acoustic_features: Dict[str, Any],
    target_accent: str = "american",
    phoneme_segments: List[Dict[str, Any]] = None
) -> Dict[str, float]:
    """
    Compute deviation scores for each phoneme
    
    Args:
        acoustic_features: Extracted acoustic features
        target_accent: Target accent name
        phoneme_segments: List of phoneme segments
    
    Returns:
        Dictionary mapping phoneme -> deviation_score (0.0 to 1.0)
    """
    if TORCH_AVAILABLE and _model is not None:
        return await _compute_with_model(acoustic_features, phoneme_segments)
    else:
        return _compute_heuristic(acoustic_features, target_accent, phoneme_segments)


async def _compute_with_model(
    acoustic_features: Dict[str, Any],
    phoneme_segments: List[Dict[str, Any]]
) -> Dict[str, float]:
    """Compute deviations using PyTorch model"""
    deviations = {}
    
    per_phoneme = acoustic_features.get("per_phoneme_features", [])
    
    for i, phoneme_data in enumerate(phoneme_segments):
        phoneme = phoneme_data["phoneme"]
        
        # Get features for this phoneme
        if i < len(per_phoneme):
            features = per_phoneme[i]
            # Create feature vector: MFCCs + pitch + duration + intensity
            feature_vec = (
                features.get("mfcc_mean", [0.0] * 5)[:5] +
                [features.get("pitch", 200.0) / 500.0,  # Normalize
                 features.get("duration", 0.1) * 10,  # Normalize
                 features.get("intensity", 0.5)]
            )
            
            # Pad or truncate to 18 features
            while len(feature_vec) < 18:
                feature_vec.append(0.0)
            feature_vec = feature_vec[:18]
            
            # Predict deviation
            with torch.no_grad():
                x = torch.tensor([feature_vec], dtype=torch.float32)
                score = _model(x).item()
                deviations[phoneme] = float(score)
        else:
            # Default deviation if no features
            deviations[phoneme] = 0.5
    
    return deviations


def _compute_heuristic(
    acoustic_features: Dict[str, Any],
    target_accent: str,
    phoneme_segments: List[Dict[str, Any]]
) -> Dict[str, float]:
    """
    Heuristic deviation scoring (fallback when model not available)
    Uses simple distance metrics from "ideal" feature values
    """
    deviations = {}
    
    # Target feature values (simplified - would be learned from training data)
    target_pitch = 200.0  # Hz
    target_intensity = 0.5
    
    per_phoneme = acoustic_features.get("per_phoneme_features", [])
    
    for i, segment in enumerate(phoneme_segments):
        phoneme = segment["phoneme"]
        
        if i < len(per_phoneme):
            features = per_phoneme[i]
            pitch = features.get("pitch", target_pitch)
            intensity = features.get("intensity", target_intensity)
            
            # Simple deviation: distance from target
            pitch_dev = abs(pitch - target_pitch) / target_pitch
            intensity_dev = abs(intensity - target_intensity) / target_intensity
            
            # Combined deviation score (0-1)
            deviation = min(1.0, (pitch_dev + intensity_dev) / 2.0)
            deviations[phoneme] = float(deviation)
        else:
            # Default moderate deviation
            deviations[phoneme] = 0.5
    
    # If no per-phoneme features, assign random deviations
    if not deviations:
        for segment in phoneme_segments:
            deviations[segment["phoneme"]] = np.random.uniform(0.2, 0.8)
    
    logger.info(f"Computed {len(deviations)} phoneme deviations (heuristic)")
    return deviations


# Initialize model on import (if available)
if TORCH_AVAILABLE:
    load_model()

