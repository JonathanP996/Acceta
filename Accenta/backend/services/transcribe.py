"""
Whisper Transcription Service
Converts speech audio to text using OpenAI Whisper API
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
import openai
from openai import OpenAI

# Load .env from project root
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

logger = logging.getLogger(__name__)

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.warning("OPENAI_API_KEY not set")
    client = None
else:
    client = OpenAI(api_key=api_key)


def _normalize_language_code(language: Optional[str]) -> Optional[str]:
    """
    Normalize language input to ISO-639-1 format for Whisper API
    
    Args:
        language: Language name or code (e.g., "english", "English", "en")
    
    Returns:
        ISO-639-1 language code (e.g., "en", "es", "fr") or None
    """
    if not language:
        return None
    
    language_lower = language.lower().strip()
    
    # Map common language names to ISO-639-1 codes
    # Matches the languages in frontend/src/data/languages.js
    language_map = {
        "english": "en",
        "spanish": "es",
        "french": "fr",
        "german": "de",
        "italian": "it",
        "portuguese": "pt",
        "chinese": "zh",
        "japanese": "ja",
        "korean": "ko",
        "russian": "ru",
        "arabic": "ar",
        "hindi": "hi",
        "mandarin": "zh",
        "cantonese": "zh",
        "polish": "pl",
        "dutch": "nl",
        "turkish": "tr",
        "swedish": "sv",
        "norwegian": "no",
        "danish": "da",
        "finnish": "fi",
        "greek": "el",
        "hebrew": "he",
        "thai": "th",
        "vietnamese": "vi",
        "indonesian": "id",
        "malay": "ms",
    }
    
    # If it's already a 2-letter code, return as-is
    if len(language_lower) == 2:
        return language_lower
    
    # Map from language name to code
    return language_map.get(language_lower, None)


async def transcribe_audio(
    audio_bytes: bytes,
    language: Optional[str] = None,
    model: str = "whisper-1"
) -> Dict[str, Any]:
    """
    Transcribe audio to text using Whisper API
    
    Args:
        audio_bytes: Audio file bytes (WAV format, 16kHz recommended)
        language: Optional language code or name (e.g., "en", "english", "es")
        model: Whisper model to use (default: "whisper-1")
    
    Returns:
        Dictionary with:
        - transcribed_text: The transcribed text
        - language: Detected language code
        - confidence: Optional confidence score
    """
    try:
        # Normalize language code
        language_code = _normalize_language_code(language)
        
        # Save audio to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_file_path = tmp_file.name
        
        try:
            if not client:
                raise ValueError("OpenAI client not initialized. Check OPENAI_API_KEY.")
            
            # Call Whisper API
            with open(tmp_file_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model=model,
                    file=audio_file,
                    language=language_code,  # Use normalized code
                    response_format="verbose_json"
                )
            
            result = {
                "transcribed_text": transcript.text,
                "language": transcript.language or language_code or "en",
                "confidence": getattr(transcript, "confidence", None),
                "segments": getattr(transcript, "segments", None)  # Include word-level timestamps if available
            }
            
            logger.info(f"Transcription successful: '{result['transcribed_text']}' ({len(result['transcribed_text'])} chars)")
            return result
            
        finally:
            # Clean up temp file
            os.unlink(tmp_file_path)
            
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise Exception(f"Transcription error: {str(e)}")


async def transcribe_audio_file(audio_file_path: str, language: Optional[str] = None) -> Dict[str, Any]:
    """
    Transcribe audio from file path
    
    Args:
        audio_file_path: Path to audio file
        language: Optional language code
    
    Returns:
        Dictionary with transcribed_text and language
    """
    with open(audio_file_path, "rb") as f:
        audio_bytes = f.read()
    
    return await transcribe_audio(audio_bytes, language=language)

