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

# Load .env from project root (Accenta directory)
# Find the .env file by going up from backend/services/tts.py
current_file = Path(__file__).resolve()
# backend/services/tts.py -> backend/services -> backend -> Accenta
project_root = current_file.parent.parent.parent
env_path = project_root / ".env"

# Also try loading from backend directory (if .env is there)
if not env_path.exists():
    env_path = current_file.parent.parent / ".env"

load_dotenv(env_path, override=True)

logger = logging.getLogger(__name__)

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "").strip()  # Strip whitespace
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"

# Log if key is loaded (for debugging)
if ELEVENLABS_API_KEY:
    logger.info(f"ElevenLabs API key loaded from {env_path}")
else:
    logger.warning(f"ElevenLabs API key NOT loaded. Checked: {env_path}")


async def text_to_speech(
    text: str,
    voice_id: Optional[str] = None,
    model_id: str = "eleven_multilingual_v2",
    accent: Optional[str] = None,
    robotic: bool = False
) -> bytes:
    """
    Convert text to speech using ElevenLabs API
    
    Args:
        text: Text to convert to speech
        voice_id: ElevenLabs voice ID (optional)
        model_id: Model to use
        accent: Optional accent hint (e.g., "british", "american")
    
    Returns:
        Audio bytes (MP3 format)
    """
    if not ELEVENLABS_API_KEY:
        logger.error("ELEVENLABS_API_KEY not set")
        raise ValueError("ElevenLabs API key not configured")
    
    try:
        # Determine voice_id: use provided, or map from accent, or use default
        if voice_id:
            final_voice_id = voice_id
        elif accent:
            final_voice_id = _get_voice_for_accent(accent, robotic=robotic)
        else:
            # Default: use robotic voice if requested, otherwise Rachel
            final_voice_id = "pNInz6obpgDQGcFmaJgB" if robotic else "21m00Tcm4TlvDq8ikWAM"
        
        url = f"{ELEVENLABS_API_URL}/{final_voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        data = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                # Robotic voice settings: lower stability = more robotic, lower similarity = less natural
                "stability": 0.1 if robotic else 0.5,  # Lower = more robotic/variable (0.1 = very robotic)
                "similarity_boost": 0.1 if robotic else 0.75,  # Lower = less natural, more robotic (0.1 = very robotic)
                "style": 0.0,  # Neutral style
                "use_speaker_boost": False if robotic else True
            }
        }
        
        logger.info(f"Calling ElevenLabs TTS with voice_id: {final_voice_id}, text: {text[:50]}...")
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        
        audio_bytes = response.content
        logger.info(f"Generated TTS audio: {len(audio_bytes)} bytes")
        return audio_bytes
        
    except requests.exceptions.HTTPError as http_err:
        if http_err.response and http_err.response.status_code == 401:
            logger.error(f"ElevenLabs API authentication failed (401): Invalid or expired API key")
            raise Exception("ElevenLabs API key is invalid or expired. Please check your API key configuration.")
        elif http_err.response and http_err.response.status_code == 429:
            logger.error(f"ElevenLabs API rate limit exceeded (429)")
            raise Exception("ElevenLabs API rate limit exceeded. Please try again later.")
        else:
            logger.error(f"TTS generation failed with HTTP error: {http_err}")
            raise Exception(f"TTS error: {str(http_err)}")
    except Exception as e:
        logger.error(f"TTS generation failed: {e}")
        raise Exception(f"TTS error: {str(e)}")


def _get_voice_for_accent(accent: str, robotic: bool = False) -> str:
    """
    Map accent name to ElevenLabs voice ID
    This is a simplified mapping - you can expand with more voices
    
    Args:
        accent: Accent name
        robotic: If True, use a more robotic-sounding voice
    """
    if not accent:
        return "EXAVITQu4vr4xnSDxMaL"  # Default: American
    
    accent_lower = accent.lower()
    
    # For robotic voice, use a deeper/more mechanical voice
    if robotic:
        # Use a deeper voice ID that sounds more robotic
        # "pNInz6obpgDQGcFmaJgB" (Adam) tends to sound more robotic with low stability
        # Alternative robotic voices: "EXAVITQu4vr4xnSDxMaL" (Bella - can sound robotic with low settings)
        # Using Adam with very low stability/similarity for maximum robotic effect
        return "pNInz6obpgDQGcFmaJgB"
    
    # Map common accent names to voice IDs
    # All voices are ElevenLabs voices - no fallback
    voice_map = {
        # English accents
        "british": "21m00Tcm4TlvDq8ikWAM",  # Rachel (British)
        "british english": "21m00Tcm4TlvDq8ikWAM",
        "american": "EXAVITQu4vr4xnSDxMaL",  # Bella (American)
        "american english": "EXAVITQu4vr4xnSDxMaL",
        "australian": "pNInz6obpgDQGcFmaJgB",  # Adam (Australian)
        "australian english": "pNInz6obpgDQGcFmaJgB",
        "canadian": "EXAVITQu4vr4xnSDxMaL",  # Use American for Canadian
        "canadian english": "EXAVITQu4vr4xnSDxMaL",
        "irish": "21m00Tcm4TlvDq8ikWAM",  # Use British for Irish
        "irish english": "21m00Tcm4TlvDq8ikWAM",
        "scottish": "21m00Tcm4TlvDq8ikWAM",  # Use British for Scottish
        "scottish english": "21m00Tcm4TlvDq8ikWAM",
        # Spanish accents
        "spanish": "ThT5KcBeYPX3keUQqHPh",  # Dorothy (Spanish)
        "castilian": "ThT5KcBeYPX3keUQqHPh",  # Castilian Spanish
        "castilian spanish": "ThT5KcBeYPX3keUQqHPh",
        "mexican": "ThT5KcBeYPX3keUQqHPh",  # Mexican Spanish
        "mexican spanish": "ThT5KcBeYPX3keUQqHPh",
        "argentinian": "ThT5KcBeYPX3keUQqHPh",  # Argentinian Spanish
        "argentinian spanish": "ThT5KcBeYPX3keUQqHPh",
        "colombian": "ThT5KcBeYPX3keUQqHPh",  # Colombian Spanish
        "colombian spanish": "ThT5KcBeYPX3keUQqHPh",
        # French accents
        "french": "VR6AewLTigWG4xSOukaG",  # Arnold (French)
        "parisian": "VR6AewLTigWG4xSOukaG",  # Parisian French
        "parisian french": "VR6AewLTigWG4xSOukaG",
        "quebecois": "VR6AewLTigWG4xSOukaG",  # Québécois French
        "quebecois french": "VR6AewLTigWG4xSOukaG",
        "belgian": "VR6AewLTigWG4xSOukaG",  # Belgian French
        "belgian french": "VR6AewLTigWG4xSOukaG",
        # German accents
        "german": "EXAVITQu4vr4xnSDxMaL",  # Use default for German
        "standard german": "EXAVITQu4vr4xnSDxMaL",
        "austrian": "EXAVITQu4vr4xnSDxMaL",  # Austrian German
        "austrian german": "EXAVITQu4vr4xnSDxMaL",
        "swiss": "EXAVITQu4vr4xnSDxMaL",  # Swiss German
        "swiss german": "EXAVITQu4vr4xnSDxMaL",
        # Italian accents
        "italian": "EXAVITQu4vr4xnSDxMaL",  # Use default for Italian
        "tuscan": "EXAVITQu4vr4xnSDxMaL",  # Tuscan Italian
        "tuscan italian": "EXAVITQu4vr4xnSDxMaL",
        "roman": "EXAVITQu4vr4xnSDxMaL",  # Roman Italian
        "roman italian": "EXAVITQu4vr4xnSDxMaL",
        "southern": "EXAVITQu4vr4xnSDxMaL",  # Southern Italian
        "southern italian": "EXAVITQu4vr4xnSDxMaL",
        # Portuguese accents
        "portuguese": "EXAVITQu4vr4xnSDxMaL",  # Use default for Portuguese
        "european portuguese": "EXAVITQu4vr4xnSDxMaL",
        "brazilian": "EXAVITQu4vr4xnSDxMaL",  # Brazilian Portuguese
        "brazilian portuguese": "EXAVITQu4vr4xnSDxMaL",
        # Mandarin accents
        "mandarin": "EXAVITQu4vr4xnSDxMaL",  # Use default for Mandarin
        "beijing": "EXAVITQu4vr4xnSDxMaL",  # Beijing Mandarin
        "beijing mandarin": "EXAVITQu4vr4xnSDxMaL",
        "taiwanese": "EXAVITQu4vr4xnSDxMaL",  # Taiwanese Mandarin
        "taiwanese mandarin": "EXAVITQu4vr4xnSDxMaL",
        # Japanese accents
        "japanese": "EXAVITQu4vr4xnSDxMaL",  # Use default for Japanese
        "tokyo": "EXAVITQu4vr4xnSDxMaL",  # Tokyo Japanese
        "tokyo japanese": "EXAVITQu4vr4xnSDxMaL",
        "osaka": "EXAVITQu4vr4xnSDxMaL",  # Osaka Japanese
        "osaka japanese": "EXAVITQu4vr4xnSDxMaL",
    }
    
    # Try exact match first
    if accent_lower in voice_map:
        return voice_map[accent_lower]
    
    # Try partial match (e.g., "British English" contains "british")
    for key, voice_id in voice_map.items():
        if key in accent_lower or accent_lower in key:
            return voice_id
    
    # Default to American
    return "EXAVITQu4vr4xnSDxMaL"


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
