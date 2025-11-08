"""
Librosa Feature Extraction Service
Extracts acoustic features (MFCCs, pitch, formants) from audio
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Ensure INFO level logging

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
        
        # Extract global features (optimized - use fewer frames for speed)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=512)  # Larger hop for speed
        mfcc_mean = np.mean(mfccs, axis=1).tolist()
        
        # Extract pitch (F0) using pyin - specifically targets fundamental frequency
        # pyin is better than piptrack because it filters out harmonics/formants
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y, 
            fmin=librosa.note_to_hz('C2'),  # ~65 Hz - minimum F0 for speech
            fmax=librosa.note_to_hz('C7'),  # ~2093 Hz - maximum F0 for speech
            sr=sr,
            hop_length=512
        )
        
        # Filter to only valid F0 values (not NaN) and within speech range (80-500 Hz)
        pitch_values = []
        for pitch in f0:
            if not np.isnan(pitch) and 80 <= pitch <= 500:  # F0 range for human speech
                pitch_values.append(float(pitch))
        
        # If we have valid pitches, use them; otherwise use median of all non-NaN values
        if not pitch_values:
            # Fallback: use all non-NaN values (might include some harmonics, but better than nothing)
            pitch_values = [float(p) for p in f0 if not np.isnan(p) and p > 0]
            # Filter to reasonable range
            pitch_values = [p for p in pitch_values if 50 <= p <= 1000]
        
        pitch_contour = pitch_values if pitch_values else [200.0]  # Default pitch
        
        # Estimate formants (simplified - real formants need more complex analysis)
        formant_ratios = _estimate_formants(y, sr)
        
        # Calculate intensity
        intensity = float(np.mean(np.abs(y)))
        
        # Extract per-phoneme features for ALL segments (real analysis)
        per_phoneme_features = []
        segments_to_process = phoneme_segments  # Process all segments for accuracy
        
        logger.info(f"🔬 EXTRACTING PER-PHONEME FEATURES:")
        logger.info(f"   Processing {len(segments_to_process)} phoneme segments")
        
        for i, segment in enumerate(segments_to_process):
            start_sample = int(segment["start"] * sr)
            end_sample = int(segment["end"] * sr)
            phoneme_audio = y[start_sample:end_sample]
            
            logger.info(f"   [{i+1}/{len(segments_to_process)}] '{segment['phoneme']}': start={segment['start']:.3f}s, end={segment['end']:.3f}s, duration={segment['duration']:.3f}s, samples={len(phoneme_audio)}")
            
            if len(phoneme_audio) > 100:  # Only process if enough samples
                # Use faster hop_length for phoneme-level features
                phoneme_mfcc = librosa.feature.mfcc(y=phoneme_audio, sr=sr, n_mfcc=13, hop_length=256)
                
                # Extract F0 using pyin (better than piptrack - filters harmonics)
                phoneme_f0, _, _ = librosa.pyin(
                    phoneme_audio,
                    fmin=librosa.note_to_hz('C2'),  # ~65 Hz
                    fmax=librosa.note_to_hz('C7'),  # ~2093 Hz
                    sr=sr,
                    hop_length=256
                )
                
                # Filter to only valid F0 values in speech range (80-500 Hz)
                valid_f0 = [float(p) for p in phoneme_f0 if not np.isnan(p) and 80 <= p <= 500]
                
                # Use median for more robust pitch estimation (less affected by outliers)
                if valid_f0:
                    mean_pitch = float(np.median(valid_f0))
                else:
                    # Fallback: use all non-NaN values, then filter
                    fallback_f0 = [float(p) for p in phoneme_f0 if not np.isnan(p) and p > 0]
                    fallback_f0 = [p for p in fallback_f0 if 50 <= p <= 1000]
                    mean_pitch = float(np.median(fallback_f0)) if fallback_f0 else 200.0
                
                intensity = float(np.mean(np.abs(phoneme_audio)))
                
                logger.info(f"      Extracted: pitch={mean_pitch:.1f}Hz, intensity={intensity:.6f}, MFCCs={np.mean(phoneme_mfcc, axis=1).tolist()[:3]}")
                
                per_phoneme_features.append({
                    "phoneme": segment["phoneme"],
                    "mfcc_mean": np.mean(phoneme_mfcc, axis=1).tolist()[:5],  # First 5 MFCCs
                    "pitch": mean_pitch,
                    "duration": segment["duration"],
                    "intensity": intensity
                })
            else:
                logger.warning(f"      ⚠️  Too few samples ({len(phoneme_audio)}) - using defaults")
                per_phoneme_features.append({
                    "phoneme": segment["phoneme"],
                    "mfcc_mean": [0.0] * 5,
                    "pitch": 200.0,
                    "duration": segment["duration"],
                    "intensity": 0.0
                })
        
        # All segments should now be processed above (no remaining segments)
        
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

