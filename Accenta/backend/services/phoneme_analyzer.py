"""
Phoneme Analysis Service
Extracts phonemes from text and compares user pronunciation with target
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# Simple phoneme mapping for common English sounds
# This is a simplified version - for production, use phonemizer library
ENGLISH_PHONEME_MAP = {
    # Vowels
    'a': ['AE', 'AH', 'AA', 'AY'],
    'e': ['EH', 'IY', 'AH'],
    'i': ['IH', 'IY', 'AY'],
    'o': ['AA', 'OW', 'AO', 'AH'],
    'u': ['UH', 'UW', 'AH'],
    # Consonants
    'th': ['TH', 'DH'],
    'ch': ['CH'],
    'sh': ['SH'],
    'ng': ['NG'],
    'b': ['B'],
    'd': ['D'],
    'f': ['F'],
    'g': ['G'],
    'h': ['HH'],
    'j': ['JH'],
    'k': ['K'],
    'l': ['L'],
    'm': ['M'],
    'n': ['N'],
    'p': ['P'],
    'r': ['R'],
    's': ['S'],
    't': ['T'],
    'v': ['V'],
    'w': ['W'],
    'y': ['Y'],
    'z': ['Z'],
}

# Try to import phonemizer for better accuracy
PHONEMIZER_AVAILABLE = False
try:
    from phonemizer import phonemize
    from phonemizer.backend import EspeakBackend
    # Test if espeak is actually available
    import os
    import subprocess
    # Check common espeak locations
    espeak_paths = ['/opt/homebrew/bin/espeak', '/usr/local/bin/espeak', '/usr/bin/espeak']
    espeak_found = any(os.path.exists(path) for path in espeak_paths) or subprocess.run(['which', 'espeak'], capture_output=True).returncode == 0
    
    if espeak_found:
        PHONEMIZER_AVAILABLE = True
        logger.info("✓ Phonemizer library available with espeak")
    else:
        logger.warning("Phonemizer available but espeak not found - using simplified phoneme mapping")
except ImportError:
    logger.warning("Phonemizer not available - using simplified phoneme mapping")
except Exception as e:
    logger.warning(f"Phonemizer initialization failed: {e} - using simplified phoneme mapping")


def extract_phonemes_simple(text: str, language: str = "en") -> str:
    """
    Simple phoneme extraction using basic mapping
    Falls back to this if phonemizer is not available
    """
    text_lower = text.lower()
    phonemes = []
    
    # Simple word-by-word phoneme approximation
    words = re.findall(r'\b\w+\b', text_lower)
    for word in words:
        # Very basic phoneme approximation
        # In production, use phonemizer or MFA
        word_phonemes = []
        i = 0
        while i < len(word):
            # Check for multi-character phonemes first
            if i < len(word) - 1:
                two_char = word[i:i+2]
                if two_char in ENGLISH_PHONEME_MAP:
                    word_phonemes.extend(ENGLISH_PHONEME_MAP[two_char])
                    i += 2
                    continue
            # Single character
            if word[i] in ENGLISH_PHONEME_MAP:
                word_phonemes.extend(ENGLISH_PHONEME_MAP[word[i]])
            i += 1
        
        if word_phonemes:
            phonemes.extend(word_phonemes)
            phonemes.append(' ')  # Word separator
    
    return ' '.join(phonemes).strip()


def extract_phonemes(text: str, language: str = "en") -> str:
    """
    Extract phonemes from text using phonemizer if available, otherwise simple mapping
    
    Args:
        text: Text to convert to phonemes
        language: Language code (default: "en")
    
    Returns:
        Space-separated phoneme sequence (e.g., "DH AH K W IH K ...")
    """
    if PHONEMIZER_AVAILABLE:
        try:
            # Ensure espeak is in PATH
            import os
            espeak_paths = ['/opt/homebrew/bin', '/usr/local/bin', '/usr/bin']
            current_path = os.environ.get('PATH', '')
            for path in espeak_paths:
                if path not in current_path and os.path.exists(os.path.join(path, 'espeak')):
                    os.environ['PATH'] = f"{path}:{current_path}"
            
            # Use espeak backend for English
            backend = EspeakBackend('en-us')  # American English
            phonemes = phonemize(
                text,
                backend=backend,
                separator=' ',
                strip=True,
                preserve_punctuation=False,
                with_stress=False
            )
            # Convert to uppercase and clean up
            phonemes = phonemes.upper().strip()
            logger.info(f"Extracted phonemes using phonemizer: {phonemes[:50]}...")
            return phonemes
        except Exception as e:
            logger.warning(f"Phonemizer failed, using simple mapping: {e}")
            return extract_phonemes_simple(text, language)
    else:
        return extract_phonemes_simple(text, language)


def compare_phonemes(target_phonemes: str, user_phonemes: str) -> Dict[str, Any]:
    """
    Compare target and user phoneme sequences to find differences
    
    Args:
        target_phonemes: Target phoneme sequence
        user_phonemes: User's phoneme sequence
    
    Returns:
        Dictionary with differences, alignment, and similarity score
    """
    target_list = target_phonemes.split()
    user_list = user_phonemes.split()
    
    # Calculate Levenshtein distance and alignment
    matcher = SequenceMatcher(None, target_list, user_list)
    similarity = matcher.ratio()
    
    # Find differences
    differences = []
    opcodes = matcher.get_opcodes()
    
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == 'replace':
            target_seg = ' '.join(target_list[i1:i2])
            user_seg = ' '.join(user_list[j1:j2])
            differences.append({
                'type': 'phoneme_mismatch',
                'target_phonemes': target_seg,
                'user_phonemes': user_seg,
                'position': i1,
                'issue': f"Phoneme mismatch: expected '{target_seg}', got '{user_seg}'"
            })
        elif tag == 'delete':
            target_seg = ' '.join(target_list[i1:i2])
            differences.append({
                'type': 'missing_phoneme',
                'target_phonemes': target_seg,
                'user_phonemes': '',
                'position': i1,
                'issue': f"Missing phoneme(s): '{target_seg}'"
            })
        elif tag == 'insert':
            user_seg = ' '.join(user_list[j1:j2])
            differences.append({
                'type': 'extra_phoneme',
                'target_phonemes': '',
                'user_phonemes': user_seg,
                'position': j1,
                'issue': f"Extra phoneme(s): '{user_seg}'"
            })
    
    return {
        'similarity_score': similarity,
        'differences': differences,
        'target_phonemes': target_phonemes,
        'user_phonemes': user_phonemes,
        'target_count': len(target_list),
        'user_count': len(user_list)
    }


async def analyze_pronunciation(
    target_text: str,
    user_text: str,
    language: str = "en"
) -> Dict[str, Any]:
    """
    Analyze pronunciation differences between target and user text
    
    Args:
        target_text: Target/reference text
        user_text: User's transcribed text
        language: Language code
    
    Returns:
        Dictionary with phoneme analysis and differences
    """
    try:
        # Extract phonemes from both texts
        target_phonemes = extract_phonemes(target_text, language)
        user_phonemes = extract_phonemes(user_text, language)
        
        # Compare phonemes
        comparison = compare_phonemes(target_phonemes, user_phonemes)
        
        return {
            'target_text': target_text,
            'user_text': user_text,
            'target_phonemes': target_phonemes,
            'user_phonemes': user_phonemes,
            'similarity_score': comparison['similarity_score'],
            'differences': comparison['differences'],
            'confidence_score': comparison['similarity_score']  # Use similarity as confidence
        }
    except Exception as e:
        logger.error(f"Phoneme analysis failed: {e}")
        raise Exception(f"Phoneme analysis error: {str(e)}")

