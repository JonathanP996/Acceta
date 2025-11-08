"""
Librosa Feature Extraction Service
Extracts acoustic features (MFCCs, pitch, formants) from audio
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logger.warning("Librosa not available, using fallback feature extraction")


async def extract_acoustic_features(
    audio_file_path: str,
    phoneme_segments: List[Dict[str, Any]],
    sample_rate: int = 16000
) -> Dict[str, Any]:
    """
    Extract acoustic features for each phoneme segment
    
    Args:
        audio_file_path: Path to audio file
        phoneme_segments: List of phoneme segments with timing
        sample_rate: Audio sample rate
    
    Returns:
        Dictionary with:
        - mfcc_mean: Average MFCC coefficients
        - pitch_contour: Pitch values over time
        - formant_ratios: Formant frequency ratios
        - intensity: Average intensity
        - per_phoneme_features: Features for each phoneme
    """
    if not LIBROSA_AVAILABLE:
        logger.warning("Using fallback feature extraction")
        return _fallback_features(phoneme_segments)
    
    try:
        # Load audio
        y, sr = librosa.load(audio_file_path, sr=sample_rate)
        
        # Extract global features
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_mean = np.mean(mfccs, axis=1).tolist()
        
        # Extract pitch (F0)
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_values.append(float(pitch))
        
        pitch_contour = pitch_values if pitch_values else [200.0]  # Default pitch
        
        # Estimate formants (simplified - real formants need more complex analysis)
        formant_ratios = _estimate_formants(y, sr)
        
        # Calculate intensity
        intensity = float(np.mean(np.abs(y)))
        
        # Extract per-phoneme features
        per_phoneme_features = []
        for segment in phoneme_segments:
            start_sample = int(segment["start"] * sr)
            end_sample = int(segment["end"] * sr)
            phoneme_audio = y[start_sample:end_sample]
            
            if len(phoneme_audio) > 0:
                phoneme_mfcc = librosa.feature.mfcc(y=phoneme_audio, sr=sr, n_mfcc=13)
                phoneme_pitch, _ = librosa.piptrack(y=phoneme_audio, sr=sr)
                
                per_phoneme_features.append({
                    "phoneme": segment["phoneme"],
                    "mfcc_mean": np.mean(phoneme_mfcc, axis=1).tolist()[:5],  # First 5 MFCCs
                    "pitch": float(np.mean(phoneme_pitch[phoneme_pitch > 0])) if np.any(phoneme_pitch > 0) else 200.0,
                    "duration": segment["duration"],
                    "intensity": float(np.mean(np.abs(phoneme_audio)))
                })
            else:
                per_phoneme_features.append({
                    "phoneme": segment["phoneme"],
                    "mfcc_mean": [0.0] * 5,
                    "pitch": 200.0,
                    "duration": segment["duration"],
                    "intensity": 0.0
                })
        
        result = {
            "mfcc_mean": mfcc_mean[:13],  # First 13 MFCCs
            "pitch_contour": pitch_contour[:100],  # Limit to 100 points
            "formant_ratios": formant_ratios,
            "intensity": intensity,
            "per_phoneme_features": per_phoneme_features
        }
        
        logger.info(f"Extracted features for {len(phoneme_segments)} phonemes")
        return result
        
    except Exception as e:
        logger.error(f"Feature extraction failed: {e}")
        return _fallback_features(phoneme_segments)


def _estimate_formants(y: np.ndarray, sr: int) -> List[float]:
    """Estimate formant ratios (simplified)"""
    # Simplified formant estimation
    # Real formant analysis requires LPC or similar techniques
    try:
        # Use spectral centroid as proxy
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        centroid_mean = float(np.mean(spectral_centroids))
        
        # Estimate formant-like ratios
        f1 = centroid_mean * 0.6
        f2 = centroid_mean * 1.2
        f3 = centroid_mean * 1.8
        
        return [f1 / 1000.0, f2 / 1000.0, f3 / 1000.0]  # Normalize
    except:
        return [0.5, 1.0, 1.5]  # Default ratios


def _fallback_features(phoneme_segments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Fallback feature extraction if librosa fails"""
    return {
        "mfcc_mean": [0.0] * 13,
        "pitch_contour": [200.0],
        "formant_ratios": [0.5, 1.0, 1.5],
        "intensity": 0.5,
        "per_phoneme_features": [
            {
                "phoneme": seg["phoneme"],
                "mfcc_mean": [0.0] * 5,
                "pitch": 200.0,
                "duration": seg["duration"],
                "intensity": 0.5
            }
            for seg in phoneme_segments
        ]
    }

