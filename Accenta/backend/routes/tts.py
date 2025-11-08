"""
Text-to-Speech Routes
ElevenLabs TTS endpoint
"""

import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional

from services.tts import text_to_speech

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tts", tags=["text-to-speech"])


class TTSRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None
    accent: Optional[str] = None


@router.post("/generate")
async def generate_tts(request: TTSRequest):
    """
    Generate speech from text using ElevenLabs TTS
    
    Args:
        request: TTS request with text and optional voice/accent
    
    Returns:
        Audio file (MP3 format)
    """
    try:
        logger.info(f"Generating TTS for text: {request.text[:50]}...")
        
        audio_bytes = await text_to_speech(
            text=request.text,
            voice_id=request.voice_id,
            accent=request.accent
        )
        
        if audio_bytes is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate TTS audio"
            )
        
        logger.info(f"TTS generated successfully ({len(audio_bytes)} bytes)")
        
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=speech.mp3"
            }
        )
        
    except Exception as e:
        logger.error(f"TTS generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"TTS generation failed: {str(e)}"
        )

