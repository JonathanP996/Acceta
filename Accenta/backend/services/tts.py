"""
ElevenLabs Text-to-Speech Service
Converts text to natural-sounding speech with accent
"""

import os
import logging
from typing import Optional
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

logger = logging.getLogger(__name__)

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"


async def text_to_speech(
    text: str,
    voice_id: str = "21m00Tcm4TlvDq8ikWAM",  # Default voice (Rachel)
    model_id: str = "eleven_multilingual_v2",
    accent: Optional[str] = None
) -> bytes:
    """
    Convert text to speech using ElevenLabs API
    
    Args:
        text: Text to convert to speech
        voice_id: ElevenLabs voice ID
        model_id: Model to use
        accent: Optional accent hint (e.g., "british", "american")
    
    Returns:
        Audio bytes (MP3 format)
    """
    if not ELEVENLABS_API_KEY:
        logger.error("ELEVENLABS_API_KEY not set")
        raise ValueError("ElevenLabs API key not configured")
    
    try:
        # Map accent to voice if provided
        voice_id = _get_voice_for_accent(accent) if accent else voice_id
        
        url = f"{ELEVENLABS_API_URL}/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        data = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        
        audio_bytes = response.content
        logger.info(f"Generated TTS audio: {len(audio_bytes)} bytes")
        return audio_bytes
        
    except Exception as e:
        logger.error(f"TTS generation failed: {e}")
        raise Exception(f"TTS error: {str(e)}")


def _get_voice_for_accent(accent: str) -> str:
    """
    Map accent name to ElevenLabs voice ID
    This is a simplified mapping - you can expand with more voices
    """
    accent_lower = accent.lower() if accent else ""
    
    voice_map = {
        "british": "21m00Tcm4TlvDq8ikWAM",  # Rachel (British)
        "american": "EXAVITQu4vr4xnSDxMaL",  # Bella (American)
        "australian": "pNInz6obpgDQGcFmaJgB",  # Adam (Australian)
        "spanish": "ThT5KcBeYPX3keUQqHPh",  # Dorothy (Spanish)
        "french": "VR6AewLTigWG4xSOukaG",  # Arnold (French)
    }
    
    return voice_map.get(accent_lower, voice_map["american"])


async def save_tts_to_file(text: str, output_path: str, accent: Optional[str] = None) -> str:
    """
    Generate TTS and save to file
    
    Args:
        text: Text to convert
        output_path: Path to save audio file
        accent: Optional accent
    
    Returns:
        Path to saved file
    """
    audio_bytes = await text_to_speech(text, accent=accent)
    
    with open(output_path, "wb") as f:
        f.write(audio_bytes)
    
    logger.info(f"Saved TTS to {output_path}")
    return output_path

