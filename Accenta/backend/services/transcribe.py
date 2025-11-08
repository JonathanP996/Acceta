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


async def transcribe_audio(
    audio_bytes: bytes,
    language: Optional[str] = None,
    model: str = "whisper-1"
) -> Dict[str, Any]:
    """
    Transcribe audio to text using Whisper API
    
    Args:
        audio_bytes: Audio file bytes (WAV format, 16kHz recommended)
        language: Optional language code (e.g., "en", "es", "fr")
        model: Whisper model to use (default: "whisper-1")
    
    Returns:
        Dictionary with:
        - transcribed_text: The transcribed text
        - language: Detected language code
        - confidence: Optional confidence score
    """
    try:
        # Save audio to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_file_path = tmp_file.name
        
        try:
            # Call Whisper API
            with open(tmp_file_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model=model,
                    file=audio_file,
                    language=language,
                    response_format="verbose_json"
                )
            
            result = {
                "transcribed_text": transcript.text,
                "language": transcript.language or language or "en",
                "confidence": getattr(transcript, "confidence", None)
            }
            
            logger.info(f"Transcription successful: {len(result['transcribed_text'])} characters")
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

