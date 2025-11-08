"""
Montreal Forced Aligner (MFA) Service
Aligns transcribed text to phonemes with timestamps
"""

import os
import logging
from typing import List, Dict, Any, Optional
import tempfile
import subprocess
import re

logger = logging.getLogger(__name__)

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logger.warning("Librosa not available for duration estimation")


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
            "phoneme": self.phoneme,  # Fixed: was using undefined 'phoneme' variable
            "start": self.start,
            "end": self.end,
            "duration": self.duration,
            "stress_pattern": self.stress
        }


# Proper word-to-phoneme dictionary (CMU-like) - for common words
WORD_TO_PHONEMES = {
    # Common words from test prompts
    'the': ['DH', 'AH'],  # "the" = /ðə/
    'quick': ['K', 'W', 'IH', 'K'],  # "quick" = /kwɪk/
    'brown': ['B', 'R', 'AW', 'N'],  # "brown" = /braʊn/
    'fox': ['F', 'AA', 'K', 'S'],  # "fox" = /fɑks/
    'jumps': ['JH', 'AH', 'M', 'P', 'S'],  # "jumps" = /dʒʌmps/
    'over': ['OW', 'V', 'ER'],  # "over" = /oʊvər/
    'lazy': ['L', 'EY', 'Z', 'IY'],  # "lazy" = /leɪzi/
    'dog': ['D', 'AO', 'G'],  # "dog" = /dɔg/
    'she': ['SH', 'IY'],  # "she" = /ʃi/
    'sells': ['S', 'EH', 'L', 'Z'],  # "sells" = /sɛlz/
    'seashells': ['S', 'IY', 'SH', 'EH', 'L', 'Z'],  # "seashells" = /siʃɛlz/
    'by': ['B', 'AY'],  # "by" = /baɪ/
    'seashore': ['S', 'IY', 'SH', 'AO', 'R'],  # "seashore" = /siʃɔr/
    'how': ['HH', 'AW'],  # "how" = /haʊ/
    'much': ['M', 'AH', 'CH'],  # "much" = /mʌtʃ/
    'wood': ['W', 'UH', 'D'],  # "wood" = /wʊd/
    'would': ['W', 'UH', 'D'],  # "would" = /wʊd/
    'woodchuck': ['W', 'UH', 'D', 'CH', 'AH', 'K'],  # "woodchuck" = /wʊdtʃʌk/
    'chuck': ['CH', 'AH', 'K'],  # "chuck" = /tʃʌk/
    'peter': ['P', 'IY', 'T', 'ER'],  # "peter" = /pitər/
    'piper': ['P', 'AY', 'P', 'ER'],  # "piper" = /paɪpər/
    'picked': ['P', 'IH', 'K', 'T'],  # "picked" = /pɪkt/
    'peck': ['P', 'EH', 'K'],  # "peck" = /pɛk/
    'pickled': ['P', 'IH', 'K', 'AH', 'L', 'D'],  # "pickled" = /pɪkəld/
    'peppers': ['P', 'EH', 'P', 'ER', 'Z'],  # "peppers" = /pɛpərz/
    'betty': ['B', 'EH', 'T', 'IY'],  # "betty" = /bɛti/
    'botter': ['B', 'AA', 'T', 'ER'],  # "botter" = /bɑtər/
    'bought': ['B', 'AO', 'T'],  # "bought" = /bɔt/
    'butter': ['B', 'AH', 'T', 'ER'],  # "butter" = /bʌtər/
    'slit': ['S', 'L', 'IH', 'T'],  # "slit" = /slɪt/
    'sheet': ['SH', 'IY', 'T'],  # "sheet" = /ʃit/
}

# Character-level mapping (fallback for unknown words)
CHAR_TO_PHONEMES = {
    'a': ['AE', 'AH', 'AA'],  # cat, about, father
    'e': ['EH', 'ER', 'EY'],  # bed, her, they
    'i': ['IH', 'IY', 'AY'],  # bit, beat, bite
    'o': ['AO', 'OW', 'OY'],  # law, go, boy
    'u': ['UH', 'UW', 'AW'],  # book, boot, now
    'b': ['B'], 'c': ['K', 'S'], 'd': ['D'], 'f': ['F'], 'g': ['G'],
    'h': ['HH'], 'j': ['JH'], 'k': ['K'], 'l': ['L'], 'm': ['M'],
    'n': ['N'], 'p': ['P'], 'q': ['K'], 'r': ['R'], 's': ['S'],
    't': ['T'], 'v': ['V'], 'w': ['W'], 'x': ['K', 'S'], 'y': ['Y'], 'z': ['Z'],
    'th': ['TH', 'DH'], 'ch': ['CH'], 'sh': ['SH'], 'zh': ['ZH'], 'ng': ['NG']
}


def _text_to_phonemes_english(text: str) -> List[str]:
    """
    Convert English text to phonemes using a simplified dictionary
    This is a basic implementation - real MFA would use proper dictionaries
    """
    text_lower = text.lower().strip()
    # Remove punctuation
    text_clean = re.sub(r'[^\w\s]', '', text_lower)
    words = text_clean.split()
    
    phonemes = []
    for word in words:
        word_phonemes = _word_to_phonemes(word)
        phonemes.extend(word_phonemes)
    
    return phonemes if phonemes else ['AH']  # Default to schwa


def _word_to_phonemes(word: str) -> List[str]:
    """Convert a single word to phonemes - use proper dictionary first, then fallback"""
    word_lower = word.lower().strip()
    
    # First, try to find the word in our dictionary (proper phonemes)
    if word_lower in WORD_TO_PHONEMES:
        return WORD_TO_PHONEMES[word_lower]
    
    # Fallback: character-level mapping (less accurate but better than nothing)
    phonemes = []
    i = 0
    while i < len(word_lower):
        # Check for multi-character phonemes first (th, ch, sh, ng)
        if i + 1 < len(word_lower):
            two_char = word_lower[i:i+2]
            if two_char in CHAR_TO_PHONEMES:
                phoneme_list = CHAR_TO_PHONEMES[two_char]
                phonemes.append(phoneme_list[0])  # Use first variant
                i += 2
                continue
        
        # Single character
        char = word_lower[i]
        if char in CHAR_TO_PHONEMES:
            phoneme_list = CHAR_TO_PHONEMES[char]
            phonemes.append(phoneme_list[0])  # Use first variant
        i += 1
    
    return phonemes if phonemes else ['AH']


async def align_phonemes(
    audio_file_path: str,
    transcribed_text: str,
    language: str = "en"
) -> List[Dict[str, Any]]:
    """
    Align transcribed text to phonemes using improved heuristic alignment
    For production, this would use MFA CLI or Python API
    
    Args:
        audio_file_path: Path to audio file
        transcribed_text: Transcribed text from Whisper
        language: Language code (e.g., "en", "es")
    
    Returns:
        List of phoneme segments with timing information
    """
    try:
        # Get audio duration
        if LIBROSA_AVAILABLE:
            try:
                y, sr = librosa.load(audio_file_path, sr=None)
                total_duration = len(y) / sr
            except Exception as e:
                logger.warning(f"Could not load audio for duration: {e}")
                total_duration = len(transcribed_text.split()) * 0.5  # Estimate 0.5s per word
        else:
            total_duration = len(transcribed_text.split()) * 0.5
        
        # Convert text to phonemes
        if language.lower() in ['en', 'english']:
            phonemes = _text_to_phonemes_english(transcribed_text)
        else:
            # For other languages, use character-level fallback
            phonemes = [c for c in transcribed_text.lower() if c.isalpha()]
            if not phonemes:
                phonemes = ['AH']
        
        if not phonemes:
            logger.warning("No phonemes extracted, using fallback")
            return _fallback_alignment(transcribed_text, total_duration)
        
        # Align phonemes to audio timeline
        # Distribute time based on phoneme type and word boundaries
        segments = []
        words = transcribed_text.split()
        word_phoneme_map = {}
        
        # Map phonemes to words
        phoneme_idx = 0
        for word in words:
            word_clean = re.sub(r'[^\w]', '', word.lower())
            if language.lower() in ['en', 'english']:
                word_phonemes = _word_to_phonemes(word_clean)
            else:
                word_phonemes = [c for c in word_clean if c.isalpha()]
            
            if word_phonemes:
                word_phoneme_map[word] = word_phonemes
                phoneme_idx += len(word_phonemes)
        
        # Calculate timing
        # Vowels typically longer than consonants
        # Stressed syllables longer than unstressed
        current_time = 0.0
        phoneme_idx = 0
        
        for word in words:
            word_phonemes = word_phoneme_map.get(word, [])
            if not word_phonemes:
                continue
            
            # Estimate word duration (longer words take more time)
            word_duration = max(0.3, len(word) * 0.08)  # At least 0.3s, ~0.08s per character
            
            # Distribute time across phonemes in this word
            for i, phoneme in enumerate(word_phonemes):
                # Vowels are longer than consonants
                is_vowel = phoneme[0] in 'AEIOU' if len(phoneme) > 0 else False
                base_duration = 0.12 if is_vowel else 0.08
                
                # First phoneme in word might be slightly longer (onset)
                if i == 0:
                    base_duration *= 1.2
                
                # Last phoneme might be shorter (coda)
                if i == len(word_phonemes) - 1:
                    base_duration *= 0.9
                
                # Scale to fit word duration
                phoneme_duration = (base_duration / sum([0.12 if p[0] in 'AEIOU' else 0.08 for p in word_phonemes])) * word_duration
                
                segment = PhonemeSegment(
                    phoneme=phoneme,
                    start=current_time,
                    end=current_time + phoneme_duration,
                    duration=phoneme_duration,
                    stress="primary" if i == 0 and is_vowel else "neutral"
                )
                segments.append(segment.to_dict())
                current_time += phoneme_duration
            
            # Small pause between words
            current_time += 0.05
        
        # Normalize to actual audio duration
        if segments and current_time > 0:
            scale_factor = total_duration / current_time
            for segment in segments:
                segment["start"] *= scale_factor
                segment["end"] *= scale_factor
                segment["duration"] *= scale_factor
        
        logger.info(f"Aligned {len(segments)} phonemes for text: '{transcribed_text}'")
        return segments
        
    except Exception as e:
        logger.error(f"Phoneme alignment failed: {e}")
        return _fallback_alignment(transcribed_text, 2.0)


def _fallback_alignment(text: str, duration: float = 2.0) -> List[Dict[str, Any]]:
    """Fallback alignment if main method fails - use proper phoneme conversion"""
    words = text.split()
    segments = []
    current_time = 0.0
    time_per_word = duration / len(words) if words else duration
    
    for word in words:
        word_clean = re.sub(r'[^\w]', '', word.lower())
        # Use proper phoneme conversion, not character splitting!
        phonemes = _word_to_phonemes(word_clean)
        time_per_phoneme = time_per_word / len(phonemes) if phonemes else 0.1
        
        for phoneme in phonemes:
            segments.append({
                "phoneme": phoneme,  # Already proper phoneme like 'AE', 'DH', etc.
                "start": current_time,
                "end": current_time + time_per_phoneme,
                "duration": time_per_phoneme,
                "stress_pattern": "neutral"
            })
            current_time += time_per_phoneme
        
        current_time += 0.05  # Small pause
    
    return segments if segments else [{
        "phoneme": "AH",
        "start": 0.0,
        "end": duration,
        "duration": duration,
        "stress_pattern": "neutral"
    }]
