"""
Phoneme Deviation Model
PyTorch model or heuristic to compute deviation scores from target accent
"""

import os
import logging
from typing import Dict, List, Any, Optional
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Ensure INFO level logging

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
    phoneme_segments: List[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    reference_audio_path: Optional[str] = None,  # NEW: Path to reference audio (ElevenLabs TTS)
    reference_phoneme_segments: Optional[List[Dict[str, Any]]] = None,  # NEW: Reference phoneme alignment
    language: Optional[str] = None  # NEW: Language for baseline lookup
) -> Dict[str, Any]:
    """
    Compute deviation scores for each phoneme using probabilistic modeling
    
    Args:
        acoustic_features: Extracted acoustic features
        target_accent: Target accent name
        phoneme_segments: List of phoneme segments
        user_id: Optional user ID for personalized baseline
    
    Returns:
        Dict with:
        - deviations: Dict[str, float] - phoneme -> deviation_score (0.0 to 1.0, where 0.0 = perfect match)
        - scoring_details: Dict with detailed breakdown of scoring
    """
    # Get personalized voice baseline FIRST (needed for proper normalization)
    personalized_baseline = None
    if user_id and language:
        personalized_baseline = await _get_personalized_baseline(user_id, language, target_accent)
        if personalized_baseline:
            logger.info(f"✅ Using personalized benchmarks for user {user_id}")
            logger.info(f"   Baseline pitch: {personalized_baseline.get('baseline_pitch_mean', 0):.1f}Hz")
            logger.info(f"   Baseline rhythm CV: {personalized_baseline.get('baseline_rhythm_cv', 0):.3f}")
        else:
            logger.info(f"⚠️  No personalized baseline found - using estimated reference values")
    
    # Normalize features - use baseline for normalization if available (TEST MODE)
    normalized_features = _normalize_acoustic_features(acoustic_features, personalized_baseline)
    
    # Get user baseline if available (for adaptation from past sessions)
    user_baseline = None
    if user_id:
        user_baseline = await _get_user_baseline(user_id, target_accent)
    
    if TORCH_AVAILABLE and _model is not None:
        return await _compute_with_model(normalized_features, phoneme_segments, user_baseline)
    else:
        return _compute_probabilistic_heuristic(
            normalized_features, 
            target_accent, 
            phoneme_segments, 
            user_baseline,
            personalized_baseline  # Pass personalized baseline
        )


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


def _normalize_acoustic_features(acoustic_features: Dict[str, Any], personalized_baseline: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Normalize acoustic features
    
    TEST MODE: If personalized_baseline is provided, normalize relative to user's baseline
    Otherwise: Normalize relative to current recording's mean (removes personal characteristics)
    
    Normalizes:
    - Pitch (relative to user's baseline if available, else current recording's mean)
    - Speaking rate (relative to average)
    - Intensity (relative to speaker's range)
    """
    logger.info("\n🔄 NORMALIZING ACOUSTIC FEATURES:")
    normalized = acoustic_features.copy()
    
    # Get pitch contour
    pitch_contour = acoustic_features.get("pitch_contour", [200.0])
    if pitch_contour and len(pitch_contour) > 0:
        # TEST MODE: Use user's baseline pitch for normalization if available
        if personalized_baseline and "baseline_pitch_mean" in personalized_baseline:
            baseline_pitch_mean = personalized_baseline.get("baseline_pitch_mean", 200.0)
            logger.info(f"   Pitch normalization (TEST MODE - using YOUR baseline):")
            logger.info(f"      Raw pitch contour: {len(pitch_contour)} samples")
            logger.info(f"      YOUR baseline pitch: {baseline_pitch_mean:.1f} Hz")
            logger.info(f"      Current recording mean: {np.mean([p for p in pitch_contour if p > 0]):.1f} Hz")
            normalized["pitch_contour_normalized"] = [(p - baseline_pitch_mean) / baseline_pitch_mean if baseline_pitch_mean > 0 else 0.0 for p in pitch_contour]
            normalized["pitch_baseline"] = baseline_pitch_mean
            logger.info(f"      ✅ Normalized pitch contour (relative to YOUR baseline)")
        else:
            # Default: normalize relative to current recording's mean
            mean_pitch = np.mean([p for p in pitch_contour if p > 0])
            logger.info(f"   Pitch normalization (default - using current recording mean):")
            logger.info(f"      Raw pitch contour: {len(pitch_contour)} samples")
            logger.info(f"      Mean pitch (baseline): {mean_pitch:.1f} Hz")
            if mean_pitch > 0:
                normalized["pitch_contour_normalized"] = [(p - mean_pitch) / mean_pitch if mean_pitch > 0 else 0.0 for p in pitch_contour]
                normalized["pitch_baseline"] = mean_pitch
                logger.info(f"      ✅ Normalized pitch contour (relative to current recording)")
            else:
                normalized["pitch_contour_normalized"] = [0.0] * len(pitch_contour)
                normalized["pitch_baseline"] = 200.0
                logger.warning(f"      ⚠️  No valid pitch - using default baseline 200.0 Hz")
    
    # Normalize intensity (relative to speaker's range)
    intensity = acoustic_features.get("intensity", 0.5)
    logger.info(f"   Intensity normalization:")
    logger.info(f"      Raw intensity: {intensity:.6f}")
    # FIXED: Use a more lenient normalization that handles low but valid intensities
    # Map intensity range [0.0001, 1.0] to [0.0, 1.0] (much more lenient)
    # This prevents valid low-intensity speech from normalizing to 0
    if intensity > 0.0001:
        # Normalize: map [0.0001, 1.0] to [0.0, 1.0]
        normalized_intensity = max(0.0, min(1.0, (intensity - 0.0001) / 0.9999))
        normalized["intensity_normalized"] = normalized_intensity
        logger.info(f"      Formula: ({intensity:.6f} - 0.0001) / 0.9999 = {normalized_intensity:.6f}")
        logger.info(f"      ✅ Normalized intensity: {normalized_intensity:.6f}")
    elif intensity > 0:
        # Very low but non-zero: give it a minimum normalized value
        normalized_intensity = 0.1  # Minimum 0.1 for any non-zero intensity
        normalized["intensity_normalized"] = normalized_intensity
        logger.info(f"      Very low intensity ({intensity:.6f}) - using minimum normalized: 0.1")
    else:
        normalized["intensity_normalized"] = 0.3  # Default moderate if zero
        logger.warning(f"      ⚠️  Zero intensity - using default 0.3")
    
    # Normalize per-phoneme features
    per_phoneme = acoustic_features.get("per_phoneme_features", [])
    if per_phoneme:
        logger.info(f"   Per-phoneme normalization ({len(per_phoneme)} phonemes):")
        pitch_baseline = normalized.get("pitch_baseline", 200.0)
        # Normalize pitch for each phoneme (relative to baseline - user's baseline in TEST MODE)
        for i, feature in enumerate(per_phoneme):
            phoneme_pitch = feature.get("pitch", 200.0)
            if pitch_baseline > 0:
                pitch_normalized = (phoneme_pitch - pitch_baseline) / pitch_baseline
                feature["pitch_normalized"] = pitch_normalized
            else:
                feature["pitch_normalized"] = 0.0
            
            # Normalize intensity (more lenient - FIXED to handle low intensities)
            phoneme_intensity = feature.get("intensity", 0.5)
            if phoneme_intensity > 0.0001:
                # Normalize: map [0.0001, 1.0] to [0.0, 1.0]
                intensity_normalized = max(0.0, min(1.0, (phoneme_intensity - 0.0001) / 0.9999))
                feature["intensity_normalized"] = intensity_normalized
            elif phoneme_intensity > 0:
                # Very low but non-zero: give it minimum normalized value
                feature["intensity_normalized"] = 0.1  # Minimum 0.1 for any non-zero intensity
            else:
                feature["intensity_normalized"] = 0.3  # Default moderate if zero
            
            if i < 3:  # Log first 3 for brevity
                logger.info(f"      [{i+1}] '{feature.get('phoneme', '?')}': pitch={phoneme_pitch:.1f}Hz→{feature['pitch_normalized']:.4f}, intensity={phoneme_intensity:.6f}→{feature['intensity_normalized']:.6f}")
        
        normalized["per_phoneme_features"] = per_phoneme
        logger.info(f"      ... ({len(per_phoneme)} total phonemes normalized)")
    
    return normalized


async def _get_personalized_baseline(user_id: str, language: str, target_accent: str) -> Optional[Dict[str, Any]]:
    """
    Get personalized voice baseline from onboarding
    
    Returns:
        Dict with predicted benchmarks, or None if not found
    """
    try:
        from db import Database
        
        baselines_collection = Database.get_collection("voice_baselines")
        baseline = await baselines_collection.find_one({
            "user_id": user_id,
            "language": language,
            "target_accent": target_accent
        })
        
        if baseline:
            # Remove MongoDB _id field
            baseline.pop("_id", None)
            return baseline
        return None
    except Exception as e:
        logger.warning(f"Failed to get personalized baseline: {e}")
        return None


def _create_personalized_reference_distribution(
    personalized_baseline: Dict[str, Any],
    target_accent: str
) -> Dict[str, Dict[str, Any]]:
    """
    Convert personalized baseline to reference distribution format
    
    Uses user's ACTUAL voice as the reference (TEST MODE)
    Normal voice = 100%, different accents = lower scores
    """
    # Get base reference for intensity, formants, duration (these are less personalized)
    base_ref = _get_reference_distribution(target_accent)
    
    # Use personalized pitch predictions (user's actual pitch)
    predicted_pitch_mean = personalized_baseline.get("predicted_pitch_mean", base_ref["pitch"]["mean"])
    predicted_pitch_std = personalized_baseline.get("predicted_pitch_std", base_ref["pitch"]["std"])
    predicted_pitch_range = personalized_baseline.get("predicted_pitch_range", (base_ref["pitch"]["min"], base_ref["pitch"]["max"]))
    
    # Extract MFCC magnitude from baseline (for comparison)
    predicted_mfcc_magnitude = personalized_baseline.get("predicted_mfcc_magnitude", 350.0)
    
    # Create personalized reference distribution
    personalized_ref = {
        "pitch": {
            "mean": float(predicted_pitch_mean),
            "std": float(predicted_pitch_std),
            "min": float(predicted_pitch_range[0]) if isinstance(predicted_pitch_range, (list, tuple)) else float(predicted_pitch_range[0]),
            "max": float(predicted_pitch_range[1]) if isinstance(predicted_pitch_range, (list, tuple)) else float(predicted_pitch_range[1]),
            "normalized_mean": 0.0,
            "normalized_std": 0.15
        },
        "intensity": base_ref["intensity"],  # Keep base intensity (less personalized)
        "formants": base_ref["formants"],  # Keep base formants
        "vowel_duration": base_ref["vowel_duration"],  # Keep base duration
        "consonant_duration": base_ref["consonant_duration"],
        # Add personalized rhythm predictions (user's actual rhythm)
        "predicted_rhythm_cv": personalized_baseline.get("predicted_rhythm_cv", 0.5),
        "predicted_vc_ratio": personalized_baseline.get("predicted_vc_ratio", 1.75),
        "predicted_mfcc_profile": personalized_baseline.get("predicted_mfcc_profile", [0.0] * 13),
        "predicted_mfcc_magnitude": float(predicted_mfcc_magnitude)  # Store for MFCC comparison
    }
    
    return personalized_ref


def _get_reference_distribution(target_accent: str) -> Dict[str, Dict[str, Any]]:
    """
    Get reference distribution for target accent from multiple native speakers
    Returns statistical distributions (mean, std, min, max) for each feature
    """
    accent_lower = target_accent.lower()
    
    # Reference distributions based on multiple native speakers
    # These represent the natural variation in the accent
    reference_distributions = {
        "american": {
            "pitch": {
                "mean": 180.0,
                "std": 30.0,  # Standard deviation across speakers
                "min": 120.0,
                "max": 280.0,
                "normalized_mean": 0.0,  # Normalized pitch mean
                "normalized_std": 0.15  # Normalized pitch variation
            },
            "intensity": {
                "mean": 0.6,
                "std": 0.2,
                "min": 0.2,
                "max": 1.0,
                "normalized_mean": 0.5,
                "normalized_std": 0.25
            },
            "formants": {
                "mean": [0.6, 1.2, 1.8],
                "std": [0.15, 0.25, 0.3],  # Variation in formants
                "tolerance": 0.4
            },
            "vowel_duration": {
                "mean": 0.15,
                "std": 0.05,
                "min": 0.08,
                "max": 0.25
            },
            "consonant_duration": {
                "mean": 0.08,
                "std": 0.03,
                "min": 0.05,
                "max": 0.15
            }
        },
        "british": {
            "pitch": {
                "mean": 200.0,
                "std": 35.0,
                "min": 140.0,
                "max": 300.0,
                "normalized_mean": 0.0,
                "normalized_std": 0.18
            },
            "intensity": {
                "mean": 0.55,
                "std": 0.2,
                "min": 0.2,
                "max": 1.0,
                "normalized_mean": 0.5,
                "normalized_std": 0.25
            },
            "formants": {
                "mean": [0.65, 1.3, 1.9],
                "std": [0.18, 0.28, 0.35],
                "tolerance": 0.4
            },
            "vowel_duration": {
                "mean": 0.18,
                "std": 0.06,
                "min": 0.09,
                "max": 0.28
            },
            "consonant_duration": {
                "mean": 0.08,
                "std": 0.03,
                "min": 0.05,
                "max": 0.15
            }
        },
        "australian": {
            "pitch": {
                "mean": 190.0,
                "std": 32.0,
                "min": 130.0,
                "max": 290.0,
                "normalized_mean": 0.0,
                "normalized_std": 0.17
            },
            "intensity": {
                "mean": 0.58,
                "std": 0.2,
                "min": 0.2,
                "max": 1.0,
                "normalized_mean": 0.5,
                "normalized_std": 0.25
            },
            "formants": {
                "mean": [0.62, 1.25, 1.85],
                "std": [0.16, 0.26, 0.32],
                "tolerance": 0.4
            },
            "vowel_duration": {
                "mean": 0.17,
                "std": 0.055,
                "min": 0.08,
                "max": 0.27
            },
            "consonant_duration": {
                "mean": 0.08,
                "std": 0.03,
                "min": 0.05,
                "max": 0.15
            }
        },
        "canadian": {
            "pitch": {
                "mean": 185.0,
                "std": 31.0,
                "min": 125.0,
                "max": 285.0,
                "normalized_mean": 0.0,
                "normalized_std": 0.17
            },
            "intensity": {
                "mean": 0.59,
                "std": 0.2,
                "min": 0.2,
                "max": 1.0,
                "normalized_mean": 0.5,
                "normalized_std": 0.25
            },
            "formants": {
                "mean": [0.61, 1.22, 1.82],
                "std": [0.155, 0.255, 0.31],
                "tolerance": 0.4
            },
            "vowel_duration": {
                "mean": 0.16,
                "std": 0.052,
                "min": 0.08,
                "max": 0.26
            },
            "consonant_duration": {
                "mean": 0.08,
                "std": 0.03,
                "min": 0.05,
                "max": 0.15
            }
        }
    }
    
    return reference_distributions.get(accent_lower, reference_distributions["american"])


def _serialize_reference_distribution(ref_dist: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert reference distribution to JSON-serializable format
    Ensures all numpy types and nested structures are converted to native Python types
    """
    serialized = {}
    for key, value in ref_dist.items():
        if isinstance(value, dict):
            serialized[key] = _serialize_reference_distribution(value)
        elif isinstance(value, (list, tuple)):
            serialized[key] = [float(v) if isinstance(v, (np.integer, np.floating)) else v for v in value]
        elif isinstance(value, (np.integer, np.floating)):
            serialized[key] = float(value)
        elif isinstance(value, tuple):
            serialized[key] = tuple(float(v) if isinstance(v, (np.integer, np.floating)) else v for v in value)
        else:
            serialized[key] = value
    return serialized


def _get_target_features_for_accent(target_accent: str) -> Dict[str, Any]:
    """
    Get target acoustic features for a specific accent
    These are reference values based on accent characteristics
    """
    accent_lower = target_accent.lower()
    
    # Target feature profiles for different accents
    # These are based on linguistic research on accent characteristics
    accent_profiles = {
        "american": {
            "avg_pitch": 180.0,  # Hz - American English tends to be lower
            "pitch_range": (120.0, 280.0),  # Much wider range for natural variation
            "intensity": 0.6,
            "intensity_range": (0.2, 1.0),  # Wide range for natural speech
            "vowel_length": 0.15,  # seconds
            "vowel_length_range": (0.08, 0.25),  # Wide range
            "formant_ratios": [0.6, 1.2, 1.8],
            "formant_tolerance": 0.4  # 40% tolerance for formants
        },
        "british": {
            "avg_pitch": 200.0,  # Hz - British English tends to be higher
            "pitch_range": (140.0, 300.0),  # Much wider range
            "intensity": 0.55,
            "intensity_range": (0.2, 1.0),
            "vowel_length": 0.18,
            "vowel_length_range": (0.09, 0.28),
            "formant_ratios": [0.65, 1.3, 1.9],
            "formant_tolerance": 0.4
        },
        "australian": {
            "avg_pitch": 190.0,
            "pitch_range": (130.0, 290.0),
            "intensity": 0.58,
            "intensity_range": (0.2, 1.0),
            "vowel_length": 0.17,
            "vowel_length_range": (0.08, 0.27),
            "formant_ratios": [0.62, 1.25, 1.85],
            "formant_tolerance": 0.4
        },
        "canadian": {
            "avg_pitch": 185.0,
            "pitch_range": (125.0, 285.0),
            "intensity": 0.59,
            "intensity_range": (0.2, 1.0),
            "vowel_length": 0.16,
            "vowel_length_range": (0.08, 0.26),
            "formant_ratios": [0.61, 1.22, 1.82],
            "formant_tolerance": 0.4
        }
    }
    
    # Default to American if accent not found
    return accent_profiles.get(accent_lower, accent_profiles["american"])


def _compute_probabilistic_heuristic(
    acoustic_features: Dict[str, Any],
    target_accent: str,
    phoneme_segments: List[Dict[str, Any]],
    user_baseline: Optional[Dict[str, Any]] = None,
    personalized_baseline: Optional[Dict[str, Any]] = None  # NEW: Personalized benchmarks from onboarding
) -> Dict[str, Any]:
    """
    Compute deviation scores using probabilistic modeling
    Compares normalized features to reference distribution from multiple native speakers
    
    Returns:
        Dict with:
        - deviations: Dict[str, float] - phoneme -> deviation_score
        - scoring_details: Dict with detailed breakdown of how scores were calculated
    """
    # Force print to console (in addition to logger)
    print("\n" + "=" * 80)
    print("🎯 STARTING PROBABILISTIC SCORING CALCULATION")
    print("=" * 80)
    print(f"Target accent: {target_accent}")
    print(f"Total phonemes to analyze: {len(phoneme_segments)}")
    
    logger.info("=" * 80)
    logger.info("🎯 STARTING PROBABILISTIC SCORING CALCULATION")
    logger.info("=" * 80)
    logger.info(f"Target accent: {target_accent}")
    logger.info(f"Total phonemes to analyze: {len(phoneme_segments)}")
    
    # Get reference distribution - use personalized baseline if available, otherwise use estimated
    if personalized_baseline:
        # Use personalized benchmarks (from onboarding) - TEST MODE: user's actual voice
        ref_dist = _create_personalized_reference_distribution(personalized_baseline, target_accent)
        logger.info(f"📊 REFERENCE BENCHMARK (TEST MODE - Your Actual Voice):")
        logger.info(f"   ✅ Using YOUR actual voice as baseline (from onboarding)")
        logger.info(f"   Your pitch: mean={ref_dist['pitch']['mean']:.1f}Hz, range={ref_dist['pitch']['min']:.0f}-{ref_dist['pitch']['max']:.0f}Hz")
        logger.info(f"   Your rhythm CV: {personalized_baseline.get('predicted_rhythm_cv', 0.5):.3f}")
        logger.info(f"   Your MFCC magnitude: {ref_dist.get('predicted_mfcc_magnitude', 350.0):.1f}")
        print(f"\n📊 REFERENCE BENCHMARK (TEST MODE):")
        print(f"   Target accent: {target_accent}")
        print(f"   ✅ Using YOUR actual voice as baseline")
        print(f"   Your pitch: {ref_dist['pitch']['mean']:.1f}Hz (range: {ref_dist['pitch']['min']:.0f}-{ref_dist['pitch']['max']:.0f}Hz)")
        print(f"   → Normal voice = 100%, Different accent = lower score")
    else:
        # Use estimated reference values (fallback)
        ref_dist = _get_reference_distribution(target_accent)
        logger.info(f"📊 REFERENCE BENCHMARK (Estimated values for {target_accent} accent):")
        logger.info(f"   ⚠️  WARNING: Using hardcoded estimates, not personalized benchmarks")
        logger.info(f"   💡 TIP: Complete onboarding to get personalized benchmarks!")
        logger.info(f"   Pitch: mean={ref_dist['pitch']['mean']:.1f}Hz, range={ref_dist['pitch']['min']:.0f}-{ref_dist['pitch']['max']:.0f}Hz")
        logger.info(f"   Intensity: mean={ref_dist['intensity']['mean']:.3f}, range={ref_dist['intensity']['min']:.3f}-{ref_dist['intensity']['max']:.3f}")
        logger.info(f"   Vowel duration: mean={ref_dist['vowel_duration']['mean']:.3f}s, range={ref_dist['vowel_duration']['min']:.3f}-{ref_dist['vowel_duration']['max']:.3f}s")
        logger.info(f"   Consonant duration: mean={ref_dist['consonant_duration']['mean']:.3f}s, range={ref_dist['consonant_duration']['min']:.3f}-{ref_dist['consonant_duration']['max']:.3f}s")
        print(f"\n📊 REFERENCE BENCHMARK:")
        print(f"   Target accent: {target_accent}")
        print(f"   Pitch reference: {ref_dist['pitch']['mean']:.1f}Hz (range: {ref_dist['pitch']['min']:.0f}-{ref_dist['pitch']['max']:.0f}Hz)")
        print(f"   ⚠️  NOTE: These are estimated values, not personalized benchmarks")
        print(f"   💡 TIP: Complete onboarding to get personalized benchmarks based on YOUR voice!")
    
    deviations = {}
    scoring_details = {
        "speaking_rate": None,
        "global_features": {},
        "per_phoneme_details": [],
        "reference_distribution": _serialize_reference_distribution(ref_dist)  # Make JSON-serializable
    }
    
    # Calculate speaking rate (words per second, phonemes per second)
    if phoneme_segments:
        total_duration = max([seg.get("end", 0) for seg in phoneme_segments]) if phoneme_segments else 1.0
        phonemes_per_second = len(phoneme_segments) / total_duration if total_duration > 0 else 0
        # Estimate words (roughly 5 phonemes per word on average)
        estimated_words = len(phoneme_segments) / 5.0
        words_per_second = estimated_words / total_duration if total_duration > 0 else 0
        
        scoring_details["speaking_rate"] = {
            "phonemes_per_second": round(float(phonemes_per_second), 2),
            "words_per_second": round(float(words_per_second), 2),
            "total_duration": round(float(total_duration), 2),
            "total_phonemes": int(len(phoneme_segments))
        }
        
        # Normal speaking rate: 2-4 words/second, 10-20 phonemes/second
        # If too fast or too slow, it might affect pronunciation
        if words_per_second > 5.0:
            logger.warning(f"Very fast speaking rate: {words_per_second:.2f} words/sec")
        elif words_per_second < 1.0:
            logger.warning(f"Very slow speaking rate: {words_per_second:.2f} words/sec")
    
    # Get normalized features
    normalized_pitch_contour = acoustic_features.get("pitch_contour_normalized", [])
    normalized_intensity = acoustic_features.get("intensity_normalized", 0.5)
    actual_formants = acoustic_features.get("formant_ratios", [0.5, 1.0, 1.5])
    
    logger.info("\n📈 GLOBAL FEATURE EXTRACTION:")
    logger.info(f"   Normalized intensity: {normalized_intensity:.6f}")
    logger.info(f"   Formant ratios: {actual_formants}")
    logger.info(f"   Normalized pitch contour length: {len(normalized_pitch_contour)}")
    
    # Validate we have real data
    actual_intensity = acoustic_features.get("intensity", 0.5)
    logger.info(f"   Raw intensity: {actual_intensity:.6f}")
    # MUCH MORE LENIENT: Only reject if intensity is truly zero or extremely low
    # Normal speech can have intensity as low as 0.0001, so we only reject < 0.00001
    if actual_intensity < 0.00001:
        logger.warning(f"⚠️  Extremely low intensity detected ({actual_intensity:.9f}) - may be silence")
        for segment in phoneme_segments:
            deviations[segment["phoneme"]] = 0.9
        scoring_details["error"] = "Extremely low intensity - may be silence"
        return {"deviations": deviations, "scoring_details": scoring_details}
    else:
        logger.info(f"   ✅ Intensity is valid (>= 0.00001), continuing with scoring")
    
    # Filter valid pitches (much more lenient - allow wider range)
    pitch_contour = acoustic_features.get("pitch_contour", [200.0])
    # Allow wider range: 20-5000 Hz (covers F0, harmonics, formants, consonants)
    valid_pitches = [p for p in pitch_contour if p > 20 and p < 5000]
    logger.info(f"   Pitch contour: {len(pitch_contour)} samples, {len(valid_pitches)} valid (range: 20-5000 Hz)")
    if not valid_pitches:
        logger.warning("⚠️  No valid pitch detected - may be silence or noise")
        for segment in phoneme_segments:
            deviations[segment["phoneme"]] = 0.85
        scoring_details["error"] = "No valid pitch detected"
        return {"deviations": deviations, "scoring_details": scoring_details}
    
    actual_avg_pitch = np.mean(valid_pitches)
    logger.info(f"   Average pitch: {actual_avg_pitch:.1f} Hz")
    
    # Store global features for transparency (ensure JSON-serializable)
    scoring_details["global_features"] = {
        "avg_pitch_hz": round(float(actual_avg_pitch), 1),
        "pitch_baseline": round(float(acoustic_features.get("pitch_baseline", 200.0)), 1),
        "intensity": round(float(actual_intensity), 4),
        "intensity_normalized": round(float(normalized_intensity), 4),
        "formants": [round(float(f), 3) for f in actual_formants]
    }
    
    # Probabilistic scoring for global features
    pitch_ref = ref_dist["pitch"]
    print(f"\n🎵 GLOBAL PITCH ANALYSIS:")
    print(f"   Your pitch: {actual_avg_pitch:.1f} Hz")
    print(f"   Reference mean: {pitch_ref['mean']:.1f} Hz")
    print(f"   Reference range: {pitch_ref['min']:.0f}-{pitch_ref['max']:.0f} Hz")
    print(f"   Reference std: {pitch_ref['std']:.1f} Hz")
    
    logger.info(f"\n🎵 GLOBAL PITCH ANALYSIS:")
    logger.info(f"   Your pitch: {actual_avg_pitch:.1f} Hz")
    logger.info(f"   Reference mean: {pitch_ref['mean']:.1f} Hz")
    logger.info(f"   Reference range: {pitch_ref['min']:.0f}-{pitch_ref['max']:.0f} Hz")
    logger.info(f"   Reference std: {pitch_ref['std']:.1f} Hz")
    
    # Always calculate z-score for display purposes
    pitch_z_score = abs(actual_avg_pitch - pitch_ref["mean"]) / pitch_ref["std"] if pitch_ref["std"] > 0 else 0
    logger.info(f"   Z-score: {pitch_z_score:.2f}")
    
    # Check if pitch is within acceptable range FIRST (more lenient)
    pitch_min, pitch_max = pitch_ref["min"], pitch_ref["max"]
    within_range = pitch_min <= actual_avg_pitch <= pitch_max
    logger.info(f"   Within range: {within_range}")
    
    if within_range:
        # Within range = high probability (0.8-1.0 based on distance from mean)
        distance_from_mean = abs(actual_avg_pitch - pitch_ref["mean"])
        max_distance = pitch_ref["std"] * 2.0  # 2 standard deviations
        logger.info(f"   Distance from mean: {distance_from_mean:.1f} Hz")
        logger.info(f"   Max distance (2*std): {max_distance:.1f} Hz")
        if max_distance > 0:
            # Closer to mean = higher probability
            pitch_match_prob = max(0.8, 1.0 - (distance_from_mean / max_distance) * 0.2)
            logger.info(f"   Calculation: max(0.8, 1.0 - ({distance_from_mean:.1f} / {max_distance:.1f}) * 0.2)")
        else:
            pitch_match_prob = 0.9  # Default high if within range
            logger.info(f"   Using default: 0.9 (within range, no std)")
    else:
        # Outside range - use z-score to penalize
        pitch_match_prob = max(0.0, 1.0 - min(1.0, pitch_z_score / 2.0))
        logger.info(f"   Outside range - using z-score penalty: max(0.0, 1.0 - min(1.0, {pitch_z_score:.2f} / 2.0))")
    
    logger.info(f"   ✅ Global pitch match probability: {pitch_match_prob:.4f}")
    
    # Store pitch analysis details (ensure JSON-serializable)
    scoring_details["global_features"]["pitch_analysis"] = {
        "your_pitch_hz": round(float(actual_avg_pitch), 1),
        "reference_mean_hz": round(float(pitch_ref["mean"]), 1),
        "reference_std": round(float(pitch_ref["std"]), 1),
        "reference_range": f"{float(pitch_ref['min']):.0f}-{float(pitch_ref['max']):.0f} Hz",
        "z_score": round(float(pitch_z_score), 2),
        "match_probability": round(float(pitch_match_prob), 3),
        "within_range": bool(within_range)  # Explicit bool conversion
    }
    
    # Formant probabilistic scoring
    formant_ref = ref_dist["formants"]
    logger.info(f"\n🔊 GLOBAL FORMANT ANALYSIS:")
    logger.info(f"   Your formants: {actual_formants}")
    logger.info(f"   Reference formants: {formant_ref['mean']}")
    formant_match_prob = 1.0
    formant_details = []
    for i in range(min(len(actual_formants), len(formant_ref["mean"]))):
        diff = abs(actual_formants[i] - formant_ref["mean"][i])
        std = formant_ref["std"][i] if i < len(formant_ref["std"]) else 0.2
        z_score = diff / std if std > 0 else 0
        # Probability decreases with distance from mean
        phoneme_formant_prob = max(0.0, 1.0 - min(1.0, z_score / 2.0))
        formant_match_prob = min(formant_match_prob, phoneme_formant_prob)
        logger.info(f"   F{i+1}: your={actual_formants[i]:.3f}, ref={formant_ref['mean'][i]:.3f}, diff={diff:.3f}, z={z_score:.2f}, prob={phoneme_formant_prob:.4f}")
        formant_details.append({
            "formant": f"F{i+1}",
            "your_value": round(float(actual_formants[i]), 3),
            "reference_mean": round(float(formant_ref["mean"][i]), 3),
            "reference_std": round(float(std), 3),
            "z_score": round(float(z_score), 2),
            "match_probability": round(float(phoneme_formant_prob), 3)
        })
    logger.info(f"   ✅ Global formant match probability: {formant_match_prob:.4f}")
    scoring_details["global_features"]["formant_analysis"] = formant_details
    scoring_details["global_features"]["formant_match_probability"] = round(float(formant_match_prob), 3)
    
    # Get per-phoneme features first (needed for rhythm analysis)
    per_phoneme = acoustic_features.get("per_phoneme_features", [])
    
    # Analyze rhythm and timing patterns (critical for accent detection)
    rhythm_analysis = _analyze_rhythm_patterns(phoneme_segments, per_phoneme, target_accent, personalized_baseline)
    scoring_details["rhythm_analysis"] = rhythm_analysis
    global_rhythm_score = rhythm_analysis.get("rhythm_match_score", 0.5)
    
    logger.info(f"\n🎼 RHYTHM & TIMING ANALYSIS:")
    logger.info(f"   Timing variability (CV): {rhythm_analysis.get('timing_variability', 0):.3f}")
    logger.info(f"   Vowel-to-consonant ratio: {rhythm_analysis.get('vowel_consonant_ratio', 0):.3f}")
    logger.info(f"   Stress pattern: {rhythm_analysis.get('stress_pattern', 'unknown')}")
    logger.info(f"   Overall rhythm match score: {global_rhythm_score:.3f}")
    print(f"\n🔍 PER-PHONEME ANALYSIS:")
    print(f"   Total phoneme segments: {len(phoneme_segments)}")
    print(f"   Total per-phoneme features: {len(per_phoneme)}")
    
    logger.info(f"\n🔍 PER-PHONEME ANALYSIS:")
    logger.info(f"   Total phoneme segments: {len(phoneme_segments)}")
    logger.info(f"   Total per-phoneme features: {len(per_phoneme)}")
    if len(phoneme_segments) != len(per_phoneme):
        print(f"   ⚠️  MISMATCH: {len(phoneme_segments)} segments but {len(per_phoneme)} features!")
        logger.warning(f"   ⚠️  MISMATCH: {len(phoneme_segments)} segments but {len(per_phoneme)} features!")
    
    # Phoneme-level probabilistic scoring
    for i, segment in enumerate(phoneme_segments):
        phoneme = segment["phoneme"]
        logger.info(f"\n   📍 Phoneme #{i+1}: '{phoneme}' (start={segment.get('start', 0):.3f}s, duration={segment.get('duration', 0):.3f}s)")
        
        if i < len(per_phoneme):
            features = per_phoneme[i]
            actual_pitch = features.get("pitch", pitch_ref["mean"])
            actual_intensity = features.get("intensity", 0.5)
            actual_duration = features.get("duration", 0.1)
            actual_mfcc = features.get("mfcc_mean", [0.0] * 5)
            
            logger.info(f"      Raw features:")
            logger.info(f"         Pitch: {actual_pitch:.1f} Hz")
            logger.info(f"         Intensity: {actual_intensity:.6f}")
            logger.info(f"         Duration: {actual_duration:.4f} s")
            logger.info(f"         MFCCs: {actual_mfcc[:3]}...")
            
            # REMOVED: Strict pitch validation - let probabilistic scoring handle it
            # Pitch can vary widely in speech (harmonics, formants, consonants can be > 500 Hz)
            # Only reject truly invalid pitches (likely measurement errors)
            if actual_pitch < 20 or actual_pitch > 5000:
                logger.warning(f"      ⚠️  Extremely invalid pitch ({actual_pitch:.1f} Hz) - likely measurement error, setting deviation to 0.9")
                deviations[phoneme] = 0.9
                continue
            
            # Validate intensity (much more lenient - only reject truly silent)
            if actual_intensity < 0.0001:  # Very strict - only truly silent
                logger.warning(f"      ⚠️  Very low intensity ({actual_intensity:.6f}) - setting deviation to 0.9")
                deviations[phoneme] = 0.9
                continue
            
            # Probabilistic pitch scoring (TEST MODE: compare directly to user's baseline)
            # Get normalized_pitch early so it's always available
            normalized_pitch = features.get("pitch_normalized", 0.0)
            pitch_min, pitch_max = pitch_ref["min"], pitch_ref["max"]
            pitch_mean = pitch_ref["mean"]  # User's baseline pitch in TEST MODE
            
            # TEST MODE: If using personalized baseline, compare directly to user's baseline
            if personalized_baseline:
                logger.info(f"      🎵 Pitch analysis (TEST MODE - comparing to YOUR baseline):")
                logger.info(f"         Your pitch: {actual_pitch:.1f} Hz")
                logger.info(f"         YOUR baseline pitch: {pitch_mean:.1f} Hz")
                
                # Compare actual pitch to user's baseline pitch
                distance_from_baseline = abs(actual_pitch - pitch_mean)
                # Use baseline std for tolerance (how much variation is normal for this user)
                baseline_std = pitch_ref.get("std", 30.0)
                max_distance = baseline_std * 2.5  # 2.5 standard deviations (more lenient)
                
                logger.info(f"         Distance from YOUR baseline: {distance_from_baseline:.1f} Hz")
                logger.info(f"         Max distance (2.5*std): {max_distance:.1f} Hz")
                
                if distance_from_baseline <= max_distance:
                    # Close to baseline = high score (normal voice)
                    if max_distance > 0:
                        # Very lenient: within 2.5 std = 0.95-1.0, within 1 std = 0.98-1.0
                        pitch_prob = max(0.95, 1.0 - (distance_from_baseline / max_distance) * 0.05)
                        logger.info(f"         ✅ Close to YOUR baseline!")
                        logger.info(f"         Calculation: max(0.95, 1.0 - ({distance_from_baseline:.1f} / {max_distance:.1f}) * 0.05) = {pitch_prob:.4f}")
                    else:
                        pitch_prob = 0.98  # Very high if exactly at baseline
                        logger.info(f"         ✅ Exactly at YOUR baseline: {pitch_prob:.4f}")
                else:
                    # Far from baseline = lower score (different accent)
                    # Still lenient but penalize more
                    pitch_prob = max(0.4, 1.0 - (distance_from_baseline / max_distance) * 0.6)
                    logger.info(f"         ⚠️  Far from YOUR baseline (different accent?)")
                    logger.info(f"         Calculation: max(0.4, 1.0 - ({distance_from_baseline:.1f} / {max_distance:.1f}) * 0.6) = {pitch_prob:.4f}")
            else:
                # Fallback: original logic (no baseline)
                logger.info(f"      🎵 Pitch analysis (no baseline - using range check):")
                logger.info(f"         Your pitch: {actual_pitch:.1f} Hz")
                logger.info(f"         Reference range: {pitch_min:.0f}-{pitch_max:.0f} Hz")
                if pitch_min <= actual_pitch <= pitch_max:
                    distance_from_mean = abs(actual_pitch - pitch_mean)
                    max_distance = pitch_ref["std"] * 2.0
                    logger.info(f"         ✅ Within range!")
                    if max_distance > 0:
                        pitch_prob = max(0.85, 1.0 - (distance_from_mean / max_distance) * 0.15)
                    else:
                        pitch_prob = 0.95
                else:
                    pitch_z = abs(normalized_pitch - pitch_ref["normalized_mean"]) / pitch_ref["normalized_std"] if pitch_ref["normalized_std"] > 0 else 0
                    pitch_prob = max(0.2, 1.0 - min(0.8, pitch_z / 2.0))
                    logger.info(f"         ❌ Outside range")
            
            logger.info(f"         ✅ Pitch probability: {pitch_prob:.4f}")
            
            # Probabilistic intensity scoring (much more lenient)
            normalized_intensity = features.get("intensity_normalized", 0.5)
            intensity_ref = ref_dist["intensity"]
            logger.info(f"      🔊 Intensity analysis:")
            logger.info(f"         Raw intensity: {actual_intensity:.6f}")
            logger.info(f"         Normalized intensity: {normalized_intensity:.6f}")
            logger.info(f"         Reference mean: {intensity_ref['normalized_mean']:.3f}")
            # If intensity is reasonable (not zero), give it decent probability (more lenient)
            if normalized_intensity > 0.05:  # Lower threshold
                # Within reasonable range - high probability
                intensity_prob = 0.9  # Higher default for reasonable intensity
                logger.info(f"         ✅ Normalized > 0.05 - using default: 0.9")
            else:
                # Very low intensity - still give some credit
                intensity_z = abs(normalized_intensity - intensity_ref["normalized_mean"]) / intensity_ref["normalized_std"] if intensity_ref["normalized_std"] > 0 else 0
                intensity_prob = max(0.6, 1.0 - min(0.4, intensity_z / 3.0))  # Higher minimum, less penalty
                logger.info(f"         ⚠️  Normalized <= 0.05 - using z-score")
                logger.info(f"         Z-score: {intensity_z:.2f}")
                logger.info(f"         Calculation: max(0.6, 1.0 - min(0.4, {intensity_z:.2f} / 3.0)) = {intensity_prob:.4f}")
            logger.info(f"         ✅ Intensity probability: {intensity_prob:.4f}")
            
            # Duration scoring with rhythm pattern analysis
            is_vowel = phoneme[0] in "AEIOU" if len(phoneme) > 0 else False
            duration_ref = ref_dist["vowel_duration"] if is_vowel else ref_dist["consonant_duration"]
            duration_min, duration_max = duration_ref["min"], duration_ref["max"]
            duration_mean = duration_ref["mean"]
            duration_std = duration_ref["std"]
            
            logger.info(f"      ⏱️  Duration & Rhythm analysis:")
            logger.info(f"         Is vowel: {is_vowel}")
            logger.info(f"         Your duration: {actual_duration:.4f} s")
            logger.info(f"         Reference mean: {duration_mean:.4f} s, std: {duration_std:.4f} s")
            logger.info(f"         Reference range: {duration_min:.4f}-{duration_max:.4f} s")
            logger.info(f"         Global rhythm score: {global_rhythm_score:.3f}")
            
            # 1. Individual phoneme duration match (z-score)
            if duration_std > 0:
                z_score = abs(actual_duration - duration_mean) / duration_std
                individual_duration_prob = max(0.2, 1.0 - min(0.8, z_score / 2.5))
                logger.info(f"         Individual duration z-score: {z_score:.2f} → prob: {individual_duration_prob:.4f}")
            else:
                if duration_min <= actual_duration <= duration_max:
                    individual_duration_prob = 0.8
                else:
                    individual_duration_prob = 0.4
                logger.info(f"         Individual duration (fallback): {individual_duration_prob:.4f}")
            
            # 2. Combine with global rhythm pattern score
            # Rhythm patterns are THE MOST CRITICAL for accent detection - weight them heavily
            # Individual duration: 20%, Rhythm pattern: 80% (rhythm is what distinguishes accents!)
            duration_prob = individual_duration_prob * 0.2 + global_rhythm_score * 0.8
            logger.info(f"         Combined: {individual_duration_prob:.4f}*0.2 + {global_rhythm_score:.3f}*0.8 = {duration_prob:.4f}")
            logger.info(f"         ✅ Final duration probability: {duration_prob:.4f}")
            
            # MFCC scoring - comparing against personalized baseline (TEST MODE)
            logger.info(f"      🎼 MFCC analysis:")
            logger.info(f"         Your MFCCs: {actual_mfcc[:5]}")
            
            if len(actual_mfcc) >= 5:
                # Calculate MFCC vector magnitude (Euclidean norm)
                mfcc_magnitude = np.sqrt(sum([m**2 for m in actual_mfcc[:5]]))
                
                # Reference: Use personalized baseline MFCC magnitude (user's actual voice)
                # Try personalized_baseline first, then ref_dist, then default
                if personalized_baseline and "predicted_mfcc_magnitude" in personalized_baseline:
                    ref_magnitude = personalized_baseline.get("predicted_mfcc_magnitude", 350.0)
                    logger.info(f"         Your MFCC magnitude: {mfcc_magnitude:.2f}")
                    logger.info(f"         YOUR baseline MFCC magnitude: {ref_magnitude:.2f} (from onboarding)")
                elif ref_dist and "predicted_mfcc_magnitude" in ref_dist:
                    ref_magnitude = ref_dist.get("predicted_mfcc_magnitude", 350.0)
                    logger.info(f"         Your MFCC magnitude: {mfcc_magnitude:.2f}")
                    logger.info(f"         YOUR baseline MFCC magnitude: {ref_magnitude:.2f} (from ref_dist)")
                else:
                    # Fallback to estimated if no baseline
                    ref_magnitude = 350.0  # Default from user's logs
                    logger.info(f"         Your MFCC magnitude: {mfcc_magnitude:.2f}")
                    logger.info(f"         Estimated reference magnitude: {ref_magnitude:.2f} (⚠️  no baseline, using default)")
                
                mfcc_distance = abs(mfcc_magnitude - ref_magnitude) / ref_magnitude if ref_magnitude > 0 else 1.0
                logger.info(f"         Normalized distance: {mfcc_distance:.3f}")
                
                # Convert distance to probability: distance=0 → 1.0, distance=0.3 → 0.7, distance=0.5+ → lower
                # More lenient for small deviations (within 30% = high score)
                if mfcc_distance < 0.3:
                    mfcc_prob = max(0.7, 1.0 - mfcc_distance * 1.0)  # Small deviation = high score
                else:
                    mfcc_prob = max(0.1, 1.0 - min(0.9, mfcc_distance * 1.5))  # Larger deviation = lower score
                logger.info(f"         Calculation: distance={mfcc_distance:.3f} → prob={mfcc_prob:.4f}")
            else:
                mfcc_prob = 0.3  # Lower default if insufficient MFCCs (penalize missing data)
                logger.info(f"         Using default: 0.3 (insufficient MFCCs - penalized)")
            
            logger.info(f"         ✅ MFCC probability: {mfcc_prob:.4f}")
            
            # Combine probabilities using weighted average (NO ARTIFICIAL BOOSTS)
            # Pitch (40%) and MFCC (40%) - BOTH MOST IMPORTANT for accent detection
            # Duration/Rhythm (15%), Formants (4%), Intensity (1%)
            print(f"      🧮 COMBINING PROBABILITIES:")
            print(f"         Weights: Pitch=40%, MFCC=40%, Duration/Rhythm=15%, Formants=4%, Intensity=1%")
            logger.info(f"      🧮 COMBINING PROBABILITIES:")
            logger.info(f"         Weights: Pitch=40%, MFCC=40%, Duration/Rhythm=15%, Formants=4%, Intensity=1%")
            combined_prob = (
                pitch_prob * 0.40 +       # Pitch is critical for accent detection
                mfcc_prob * 0.40 +        # MFCCs are equally critical (spectral characteristics)
                duration_prob * 0.15 +    # Duration/Rhythm is important (stress vs syllable timing)
                formant_match_prob * 0.04 +  # Formants important for vowels
                intensity_prob * 0.01      # Intensity least important
            )
            print(f"         Calculation:")
            print(f"            = {pitch_prob:.4f}*0.40 + {mfcc_prob:.4f}*0.40 + {duration_prob:.4f}*0.15 + {formant_match_prob:.4f}*0.04 + {intensity_prob:.4f}*0.01")
            print(f"            = {pitch_prob*0.40:.4f} + {mfcc_prob*0.40:.4f} + {duration_prob*0.15:.4f} + {formant_match_prob*0.04:.4f} + {intensity_prob*0.01:.4f}")
            print(f"            = {combined_prob:.4f}")
            logger.info(f"         Calculation:")
            logger.info(f"            = {pitch_prob:.4f}*0.40 + {mfcc_prob:.4f}*0.40 + {duration_prob:.4f}*0.15 + {formant_match_prob:.4f}*0.04 + {intensity_prob:.4f}*0.01")
            logger.info(f"            = {pitch_prob*0.40:.4f} + {mfcc_prob*0.40:.4f} + {duration_prob*0.15:.4f} + {formant_match_prob*0.04:.4f} + {intensity_prob*0.01:.4f}")
            logger.info(f"            = {combined_prob:.4f}")
            
            # NO ARTIFICIAL BOOSTS - let the math speak for itself
            # If the user has a different accent, the probabilities will reflect that
            
            print(f"         ✅ Final combined probability: {combined_prob:.4f}")
            logger.info(f"         ✅ Final combined probability: {combined_prob:.4f}")
            
            # Apply user baseline adaptation if available
            baseline_adjustment = None
            if user_baseline:
                # Adjust based on user's consistent patterns
                user_pitch_bias = user_baseline.get("pitch_bias", 0.0)
                user_intensity_bias = user_baseline.get("intensity_bias", 0.0)
                
                # If user consistently has different pitch/intensity, adjust expectations
                pitch_boost = 0.0
                intensity_boost = 0.0
                if abs(normalized_pitch - user_pitch_bias) < 0.1:
                    pitch_boost = 0.1
                    pitch_prob = min(1.0, pitch_prob + pitch_boost)
                if abs(normalized_intensity - user_intensity_bias) < 0.1:
                    intensity_boost = 0.1
                    intensity_prob = min(1.0, intensity_prob + intensity_boost)
                
                combined_prob = (
                    pitch_prob * 0.3 +
                    intensity_prob * 0.2 +
                    duration_prob * 0.2 +
                    mfcc_prob * 0.15 +
                    formant_match_prob * 0.15
                )
                
                baseline_adjustment = {
                    "pitch_boost": round(float(pitch_boost), 2),
                    "intensity_boost": round(float(intensity_boost), 2),
                    "user_pitch_bias": round(float(user_pitch_bias), 3),
                    "user_intensity_bias": round(float(user_intensity_bias), 3)
                }
            
            # Convert probability to deviation score (invert: 1.0 prob = 0.0 deviation)
            deviation = 1.0 - combined_prob
            deviations[phoneme] = float(max(0.0, min(1.0, deviation)))
            logger.info(f"      📊 DEVIATION:")
            logger.info(f"         deviation = 1.0 - {combined_prob:.4f} = {deviation:.4f}")
            logger.info(f"         ✅ Final deviation for '{phoneme}': {deviation:.4f}")
            
            # Store detailed breakdown for this phoneme (ensure all values are JSON-serializable)
            phoneme_detail = {
                "phoneme": str(phoneme),
                "features": {
                    "pitch_hz": round(float(actual_pitch), 1),
                    "pitch_normalized": round(float(normalized_pitch), 4),
                    "intensity": round(float(actual_intensity), 4),
                    "intensity_normalized": round(float(normalized_intensity), 4),
                    "duration_seconds": round(float(actual_duration), 3)
                },
                "probabilities": {
                    "pitch_prob": round(float(pitch_prob), 3),
                    "intensity_prob": round(float(intensity_prob), 3),
                    "duration_prob": round(float(duration_prob), 3),
                    "mfcc_prob": round(float(mfcc_prob), 3),
                    "formant_prob": round(float(formant_match_prob), 3),
                    "combined_prob": round(float(combined_prob), 3)
                },
                "reference_comparison": {
                    "pitch_ref_mean": round(float(pitch_ref["mean"]), 1),
                    "pitch_ref_range": f"{float(pitch_ref['min']):.0f}-{float(pitch_ref['max']):.0f} Hz",
                    "duration_ref_mean": round(float(duration_ref["mean"]), 3),
                    "duration_ref_range": f"{float(duration_ref['min']):.3f}-{float(duration_ref['max']):.3f} sec"
                },
                "final_score": {
                    "deviation": round(float(deviation), 3),
                    "accent_score": round(float((1.0 - deviation) * 100), 1)
                }
            }
            
            if baseline_adjustment:
                phoneme_detail["baseline_adjustment"] = baseline_adjustment
            
            scoring_details["per_phoneme_details"].append(phoneme_detail)
        else:
            # Use global probabilities if no per-phoneme features
            global_prob = (pitch_match_prob * 0.5 + formant_match_prob * 0.5)
            deviations[phoneme] = float(max(0.0, min(1.0, 1.0 - global_prob)))
    
    # If no per-phoneme features at all
    if not deviations:
        global_prob = (pitch_match_prob * 0.5 + formant_match_prob * 0.5)
        for segment in phoneme_segments:
            deviations[segment["phoneme"]] = float(max(0.0, min(1.0, 1.0 - global_prob)))
    
    # Final adjustment: boost scores for native-like speech (much more aggressive)
    print(f"\n🎯 FINAL SCORE CALCULATION:")
    avg_dev = sum(deviations.values()) / len(deviations) if deviations else 0.5
    print(f"   Average deviation (before boosts): {avg_dev:.4f}")
    print(f"   Individual deviations: {[(p, round(d, 4)) for p, d in list(deviations.items())[:5]]}...")
    
    logger.info(f"\n🎯 FINAL SCORE CALCULATION:")
    logger.info(f"   Average deviation (before boosts): {avg_dev:.4f}")
    logger.info(f"   Individual deviations: {[(p, round(d, 4)) for p, d in list(deviations.items())[:5]]}...")
    
    # NO ARTIFICIAL BOOSTS - the probabilities already reflect accent accuracy
    # If someone has a different accent, their deviations should reflect that
    # Boosts were causing false high scores for non-native accents
    native_boost_applied = False
    logger.info(f"   📊 No artificial boosts applied - using raw probability scores")
    logger.info(f"   📊 This ensures accurate accent detection (different accents will show lower scores)")
    
    # Calculate final accent score
    final_accent_score = (1.0 - avg_dev) * 100
    print(f"   ✅ FINAL ACCENT SCORE:")
    print(f"      Average deviation: {avg_dev:.4f}")
    print(f"      Score = (1.0 - {avg_dev:.4f}) * 100 = {final_accent_score:.1f}%")
    print("=" * 80)
    
    logger.info(f"   ✅ FINAL ACCENT SCORE:")
    logger.info(f"      Average deviation: {avg_dev:.4f}")
    logger.info(f"      Score = (1.0 - {avg_dev:.4f}) * 100 = {final_accent_score:.1f}%")
    logger.info("=" * 80)
    
    scoring_details["summary"] = {
        "average_deviation": round(float(avg_dev), 3),
        "accent_score_percent": round(float(final_accent_score), 1),
        "total_phonemes_analyzed": int(len(deviations)),
        "native_boost_applied": bool(native_boost_applied),  # Explicit bool conversion
        "user_baseline_used": bool(user_baseline is not None)  # Explicit bool conversion
    }
    
    logger.info(f"Computed {len(deviations)} phoneme deviations using probabilistic modeling (avg: {avg_dev:.2f}, score: {final_accent_score:.1f}%)")
    logger.info(f"Speaking rate: {scoring_details.get('speaking_rate', {}).get('words_per_second', 0):.2f} words/sec")
    
    return {"deviations": deviations, "scoring_details": scoring_details}


def _compute_heuristic(
    acoustic_features: Dict[str, Any],
    target_accent: str,
    phoneme_segments: List[Dict[str, Any]]
) -> Dict[str, float]:
    """
    Legacy heuristic function (kept for compatibility)
    Now calls probabilistic heuristic
    """
    return _compute_probabilistic_heuristic(acoustic_features, target_accent, phoneme_segments, None)


def _analyze_rhythm_patterns(
    phoneme_segments: List[Dict[str, Any]],
    per_phoneme_features: List[Dict[str, Any]],
    target_accent: str,
    personalized_baseline: Optional[Dict[str, Any]] = None  # NEW: Use personalized rhythm predictions
) -> Dict[str, Any]:
    """
    Analyze rhythm and timing patterns (critical for accent detection)
    
    Measures:
    1. Timing variability (coefficient of variation) - stress-timed vs syllable-timed
    2. Vowel-to-consonant duration ratio
    3. Stress pattern (which phonemes are longest)
    4. Overall rhythm consistency
    
    Returns:
        Dict with rhythm metrics and match score
    """
    if not phoneme_segments or not per_phoneme_features:
        return {
            "timing_variability": 0.0,
            "vowel_consonant_ratio": 1.0,
            "rhythm_match_score": 0.5,
            "stress_pattern": "unknown"
        }
    
    # Extract durations
    durations = []
    vowel_durations = []
    consonant_durations = []
    
    for i, segment in enumerate(phoneme_segments):
        if i < len(per_phoneme_features):
            duration = per_phoneme_features[i].get("duration", segment.get("duration", 0.1))
        else:
            duration = segment.get("duration", 0.1)
        
        durations.append(duration)
        
        # Classify as vowel or consonant
        phoneme = segment.get("phoneme", "")
        is_vowel = phoneme[0] in "AEIOU" if len(phoneme) > 0 else False
        
        if is_vowel:
            vowel_durations.append(duration)
        else:
            consonant_durations.append(duration)
    
    if not durations:
        return {
            "timing_variability": 0.0,
            "vowel_consonant_ratio": 1.0,
            "rhythm_match_score": 0.5,
            "stress_pattern": "unknown"
        }
    
    # 1. Calculate timing variability (Coefficient of Variation)
    # CV = std / mean - measures how variable durations are
    # High CV = stress-timed (like American English - variable syllable lengths)
    # Low CV = syllable-timed (like Indian English - more uniform syllable lengths)
    mean_duration = np.mean(durations)
    std_duration = np.std(durations) if len(durations) > 1 else 0.0
    timing_variability = std_duration / mean_duration if mean_duration > 0 else 0.0
    
    # 2. Calculate vowel-to-consonant ratio
    avg_vowel_duration = np.mean(vowel_durations) if vowel_durations else 0.1
    avg_consonant_duration = np.mean(consonant_durations) if consonant_durations else 0.1
    vowel_consonant_ratio = avg_vowel_duration / avg_consonant_duration if avg_consonant_duration > 0 else 1.0
    
    # 3. Reference values for target accent
    # American English: stress-timed (high variability ~0.4-0.6), V/C ratio ~1.5-2.0
    # Indian English: syllable-timed (low variability ~0.2-0.3), V/C ratio ~1.0-1.3
    accent_rhythm_profiles = {
        "american": {
            "expected_cv": 0.5,  # High variability (stress-timed)
            "cv_tolerance": 0.2,  # ±0.2 tolerance
            "expected_vc_ratio": 1.75,  # Vowels longer than consonants
            "vc_tolerance": 0.5
        },
        "british": {
            "expected_cv": 0.55,  # Even more stress-timed
            "cv_tolerance": 0.2,
            "expected_vc_ratio": 1.8,
            "vc_tolerance": 0.5
        },
        "australian": {
            "expected_cv": 0.5,
            "cv_tolerance": 0.2,
            "expected_vc_ratio": 1.7,
            "vc_tolerance": 0.5
        },
        "canadian": {
            "expected_cv": 0.5,
            "cv_tolerance": 0.2,
            "expected_vc_ratio": 1.75,
            "vc_tolerance": 0.5
        }
    }
    
    # Use personalized rhythm predictions if available (TEST MODE: use user's actual rhythm)
    if personalized_baseline:
        expected_cv = personalized_baseline.get("predicted_rhythm_cv", 0.5)
        expected_vc_ratio = personalized_baseline.get("predicted_vc_ratio", 1.75)
        profile = {
            "expected_cv": expected_cv,
            "cv_tolerance": 0.3,  # More lenient tolerance for user's actual rhythm
            "expected_vc_ratio": expected_vc_ratio,
            "vc_tolerance": 0.6  # More lenient tolerance
        }
        logger.info(f"   ✅ Using YOUR actual rhythm as baseline: CV={expected_cv:.3f}, V/C={expected_vc_ratio:.3f}")
        logger.info(f"   → Normal rhythm = 100%, Different rhythm = lower score")
    else:
        profile = accent_rhythm_profiles.get(target_accent.lower(), accent_rhythm_profiles["american"])
    
    # 4. Calculate rhythm match score (STRICTER - accent differences are critical)
    # Compare timing variability
    cv_diff = abs(timing_variability - profile["expected_cv"])
    # Stricter: use smaller tolerance, penalize more heavily
    # If CV is off by 0.2 (e.g., 0.3 vs 0.5), that's a major accent difference
    cv_match = max(0.0, 1.0 - min(1.0, cv_diff / (profile["cv_tolerance"] * 0.7)))  # 30% stricter
    
    # Compare vowel-consonant ratio
    vc_diff = abs(vowel_consonant_ratio - profile["expected_vc_ratio"])
    # Stricter: V/C ratio differences are also critical for accent
    vc_match = max(0.0, 1.0 - min(1.0, vc_diff / (profile["vc_tolerance"] * 0.7)))  # 30% stricter
    
    # Combined rhythm score (weighted: CV 70%, V/C ratio 30% - CV is more distinctive)
    rhythm_match_score = cv_match * 0.7 + vc_match * 0.3
    
    # Determine stress pattern
    if timing_variability > 0.4:
        stress_pattern = "stress-timed"
    elif timing_variability < 0.3:
        stress_pattern = "syllable-timed"
    else:
        stress_pattern = "mixed"
    
    return {
        "timing_variability": round(float(timing_variability), 3),
        "vowel_consonant_ratio": round(float(vowel_consonant_ratio), 3),
        "rhythm_match_score": round(float(rhythm_match_score), 3),
        "stress_pattern": stress_pattern,
        "cv_match": round(float(cv_match), 3),
        "vc_match": round(float(vc_match), 3),
        "expected_cv": profile["expected_cv"],
        "expected_vc_ratio": profile["expected_vc_ratio"],
        "avg_vowel_duration": round(float(avg_vowel_duration), 4),
        "avg_consonant_duration": round(float(avg_consonant_duration), 4)
    }


async def _predict_personalized_benchmarks(
    baseline_pitch_mean: float,
    baseline_pitch_std: float,
    baseline_intensity_mean: float,
    baseline_mfcc_profile: List[float],
    baseline_rhythm_cv: float,
    baseline_vc_ratio: float,
    target_accent: str,
    language: str
) -> Dict[str, Any]:
    """
    Use user's actual voice baseline as the reference (TEST MODE)
    
    Instead of predicting what their voice SHOULD sound like, we use their ACTUAL voice
    as the baseline. This means:
    - If they speak normally (their baseline), score = 100%
    - If they do a different accent, it deviates from baseline = lower score
    
    Args:
        baseline_pitch_mean: User's natural pitch (Hz)
        baseline_pitch_std: User's pitch variation
        baseline_intensity_mean: User's natural intensity
        baseline_mfcc_profile: User's typical MFCC pattern
        baseline_rhythm_cv: User's natural timing variability
        baseline_vc_ratio: User's natural vowel/consonant ratio
        target_accent: Target accent (e.g., "american")
        language: Target language
    
    Returns:
        Dict with benchmarks set to user's actual baseline (for testing)
    """
    # USE USER'S ACTUAL VOICE AS THE REFERENCE (TEST MODE)
    # This means their normal voice = 100%, different accents = lower scores
    
    # Use user's actual pitch as the reference
    predicted_pitch_mean = baseline_pitch_mean
    predicted_pitch_std = baseline_pitch_std if baseline_pitch_std > 0 else 30.0
    predicted_pitch_range = (
        max(80.0, predicted_pitch_mean - predicted_pitch_std * 2.5),  # Wider range
        min(500.0, predicted_pitch_mean + predicted_pitch_std * 2.5)
    )
    
    # Use user's actual MFCC profile as the reference
    # Calculate average MFCC magnitude from their baseline
    if baseline_mfcc_profile and len(baseline_mfcc_profile) > 0:
        baseline_mfcc_magnitude = np.sqrt(sum([m**2 for m in baseline_mfcc_profile[:5]]))
    else:
        baseline_mfcc_magnitude = 350.0  # Default from logs
    
    # Use user's actual rhythm as the reference
    predicted_rhythm_cv = baseline_rhythm_cv if baseline_rhythm_cv > 0 else 0.3
    predicted_vc_ratio = baseline_vc_ratio if baseline_vc_ratio > 0 else 1.5
    
    logger.info(f"🎯 TEST MODE: Using YOUR actual voice as baseline:")
    logger.info(f"   Your pitch: {predicted_pitch_mean:.1f}Hz ± {predicted_pitch_std:.1f}Hz")
    logger.info(f"   Your MFCC magnitude: {baseline_mfcc_magnitude:.1f}")
    logger.info(f"   Your rhythm CV: {predicted_rhythm_cv:.3f}")
    logger.info(f"   Your V/C ratio: {predicted_vc_ratio:.3f}")
    logger.info(f"   → Normal voice = 100%, Different accent = lower score")
    
    return {
        "predicted_pitch_mean": round(float(predicted_pitch_mean), 1),
        "predicted_pitch_std": round(float(predicted_pitch_std), 1),
        "predicted_pitch_range": (round(float(predicted_pitch_range[0]), 1), round(float(predicted_pitch_range[1]), 1)),
        "predicted_mfcc_profile": [round(float(m), 3) for m in baseline_mfcc_profile] if baseline_mfcc_profile else [0.0] * 13,
        "predicted_mfcc_magnitude": round(float(baseline_mfcc_magnitude), 1),  # Store magnitude for comparison
        "predicted_rhythm_cv": round(float(predicted_rhythm_cv), 3),
        "predicted_vc_ratio": round(float(predicted_vc_ratio), 3)
    }


async def _get_user_baseline(user_id: str, target_accent: str) -> Optional[Dict[str, Any]]:
    """
    Get user's personalized baseline from past sessions
    Tracks consistent patterns to distinguish personal voice traits from errors
    """
    try:
        from db import Database
        
        # Get user's past sessions
        sessions_collection = Database.get_collection("sessions")
        past_sessions = await sessions_collection.find({
            "user_id": user_id,
            "target_accent": target_accent
        }).sort("timestamp", -1).limit(10).to_list(length=10)
        
        if not past_sessions or len(past_sessions) < 3:
            return None  # Need at least 3 sessions for baseline
        
        # Calculate average pitch and intensity across sessions
        pitch_values = []
        intensity_values = []
        
        for session in past_sessions:
            acoustic_features = session.get("acoustic_features", {})
            pitch_contour = acoustic_features.get("pitch_contour", [])
            if pitch_contour:
                valid_pitches = [p for p in pitch_contour if p > 50 and p < 500]
                if valid_pitches:
                    pitch_values.append(np.mean(valid_pitches))
            
            intensity = acoustic_features.get("intensity", 0.5)
            if intensity > 0.001:
                intensity_values.append(intensity)
        
        if not pitch_values or not intensity_values:
            return None
        
        # Calculate baseline (user's typical pitch/intensity)
        avg_pitch = np.mean(pitch_values)
        avg_intensity = np.mean(intensity_values)
        
        # Calculate normalized biases
        ref_dist = _get_reference_distribution(target_accent)
        pitch_ref = ref_dist["pitch"]
        intensity_ref = ref_dist["intensity"]
        
        pitch_bias = (avg_pitch - pitch_ref["mean"]) / pitch_ref["mean"] if pitch_ref["mean"] > 0 else 0.0
        intensity_bias = (avg_intensity - intensity_ref["mean"]) / intensity_ref["mean"] if intensity_ref["mean"] > 0 else 0.0
        
        return {
            "pitch_bias": pitch_bias,
            "intensity_bias": intensity_bias,
            "avg_pitch": avg_pitch,
            "avg_intensity": avg_intensity
        }
    except Exception as e:
        logger.warning(f"Failed to get user baseline: {e}")
        return None


# Initialize model on import (if available)
if TORCH_AVAILABLE:
    load_model()

