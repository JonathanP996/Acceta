"""
Montreal Forced Aligner (MFA) Service
Aligns transcribed text to phonemes with timestamps
"""

import os
import logging
from typing import List, Dict, Any, Optional
import tempfile
import subprocess

logger = logging.getLogger(__name__)


class PhonemeSegment:
    """Phoneme segment with timing information"""
    def __init__(self, phoneme: str, start: float, end: float, duration: float, stress: str = "neutral"):
        self.phoneme = phoneme
        self.start = start
        self.end = end
        self.duration = duration
        self.stress = stress
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "phoneme": self.phoneme,
            "start": self.start,
            "end": self.end,
            "duration": self.duration,
            "stress_pattern": self.stress
        }


async def align_phonemes(
    audio_file_path: str,
    transcribed_text: str,
    language: str = "en"
) -> List[Dict[str, Any]]:
    """
    Align transcribed text to phonemes using MFA
    
    Args:
        audio_file_path: Path to audio file
        transcribed_text: Transcribed text from Whisper
        language: Language code (e.g., "en", "es")
    
    Returns:
        List of phoneme segments with timing information
    """
    try:
        # For MVP, we'll use a simplified heuristic alignment
        # In production, this would call MFA CLI or Python API
        logger.warning("Using heuristic alignment (MFA not fully integrated)")
        
        # Simplified phoneme extraction and timing
        phonemes = _extract_phonemes_heuristic(transcribed_text, language)
        total_duration = _estimate_audio_duration(audio_file_path)
        
        # Distribute phonemes evenly across duration (simplified)
        segments = []
        phoneme_duration = total_duration / len(phonemes) if phonemes else 0.1
        
        for i, phoneme in enumerate(phonemes):
            start = i * phoneme_duration
            end = start + phoneme_duration
            segment = PhonemeSegment(
                phoneme=phoneme,
                start=start,
                end=end,
                duration=phoneme_duration,
                stress="primary" if i % 3 == 0 else "neutral"
            )
            segments.append(segment.to_dict())
        
        logger.info(f"Aligned {len(segments)} phonemes")
        return segments
        
    except Exception as e:
        logger.error(f"Phoneme alignment failed: {e}")
        # Fallback: return basic segments
        return _fallback_alignment(transcribed_text)


def _extract_phonemes_heuristic(text: str, language: str) -> List[str]:
    """
    Heuristic phoneme extraction (simplified)
    In production, use MFA's phoneme dictionary
    """
    # Simplified: split into character-level phonemes
    # This is a placeholder - real MFA would use proper phoneme dictionaries
    text_clean = text.lower().replace(" ", "")
    phonemes = []
    
    # Basic phoneme mapping (very simplified)
    for char in text_clean:
        if char.isalpha():
            phonemes.append(char)
    
    return phonemes if phonemes else ["a", "h"]


def _estimate_audio_duration(audio_file_path: str) -> float:
    """Estimate audio duration using librosa"""
    try:
        import librosa
        y, sr = librosa.load(audio_file_path, sr=None)
        duration = len(y) / sr
        return duration
    except Exception as e:
        logger.warning(f"Could not estimate duration: {e}, using default 2.0s")
        return 2.0


def _fallback_alignment(text: str) -> List[Dict[str, Any]]:
    """Fallback alignment if MFA fails"""
    words = text.split()
    segments = []
    current_time = 0.0
    
    for word in words:
        # Estimate 0.5s per word
        duration = 0.5
        segments.append({
            "phoneme": word[0] if word else "a",
            "start": current_time,
            "end": current_time + duration,
            "duration": duration,
            "stress_pattern": "neutral"
        })
        current_time += duration
    
    return segments if segments else [{
        "phoneme": "a",
        "start": 0.0,
        "end": 1.0,
        "duration": 1.0,
        "stress_pattern": "neutral"
    }]

