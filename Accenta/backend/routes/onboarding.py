"""
Onboarding endpoint for voice baseline extraction
Users record their voice, we extract baseline features, then predict personalized benchmarks
"""

import os
import logging
import tempfile
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.transcribe import transcribe_audio
from db import Database

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter(prefix="/api", tags=["onboarding"])


@router.post("/onboarding/voice_baseline")
async def create_voice_baseline(
    user_id: str = Form(...),
    language: str = Form(...),
    target_accent: str = Form(...),
    audio_file: UploadFile = File(...)
):
    """
    Store basic user onboarding information
    
    Args:
        user_id: User identifier
        language: Target language (e.g., "english")
        target_accent: Target accent (e.g., "american")
        audio_file: Audio recording (stored for future use)
    
    Returns:
        Success confirmation
    """
    try:
        # Save uploaded audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            audio_bytes = await audio_file.read()
            tmp_file.write(audio_bytes)
            tmp_file_path = tmp_file.name
        
        try:
            # Step 1: Transcribe (optional - just to verify audio is valid)
            logger.info(f"Processing onboarding audio for user {user_id}")
            transcription = await transcribe_audio(audio_bytes, language=language)
            transcribed_text = transcription.get("transcribed_text", "")
            
            if not transcribed_text or len(transcribed_text.strip()) < 3:
                raise HTTPException(
                    status_code=400,
                    detail="Could not transcribe audio. Please speak clearly and try again."
                )
            
            # Step 2: Store basic baseline in database
            baseline_doc = {
                "user_id": user_id,
                "language": language,
                "target_accent": target_accent,
                "created_at": transcription.get("timestamp"),
                "updated_at": transcription.get("timestamp")
            }
            
            baselines_collection = Database.get_collection("voice_baselines")
            await baselines_collection.update_one(
                {"user_id": user_id, "language": language, "target_accent": target_accent},
                {"$set": baseline_doc},
                upsert=True
            )
            
            logger.info(f"Voice baseline created for user {user_id} ({language}, {target_accent})")
            
            return JSONResponse({
                "success": True,
                "message": "Voice baseline created successfully"
            })
            
        finally:
            # Clean up temp file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Onboarding failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create voice baseline: {str(e)}"
        )

