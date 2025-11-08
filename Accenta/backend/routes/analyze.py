"""
FastAPI Routes for Accent Analysis
"""

import os
import logging
import tempfile
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional

import sys
from pathlib import Path

# Add parent directory to path for schemas
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.transcribe import transcribe_audio
from services.align import align_phonemes
from services.features import extract_acoustic_features
from services.deviation_model import compute_phoneme_deviations
from services.agent_client import call_accent_agent
from services.tts import text_to_speech
from db import Database
from schemas.memory_schema import SessionData, Feedback

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze_accent")
async def analyze_accent(
    user_id: str = Form(...),
    session_id: str = Form(...),
    language: str = Form(...),
    target_accent: str = Form(...),
    audio_file: UploadFile = File(...)
):
    """
    Full accent analysis endpoint
    Processes audio through: Whisper → MFA → Librosa → PyTorch → Agent → TTS
    """
    try:
        # Save uploaded audio to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            audio_bytes = await audio_file.read()
            tmp_file.write(audio_bytes)
            tmp_file_path = tmp_file.name
        
        try:
            # Step 1: Transcribe audio
            logger.info(f"Transcribing audio for session {session_id}")
            transcription = await transcribe_audio(audio_bytes, language=language)
            transcribed_text = transcription["transcribed_text"]
            
            # Step 2: Align phonemes
            logger.info("Aligning phonemes")
            phoneme_segments = await align_phonemes(
                tmp_file_path,
                transcribed_text,
                language=language
            )
            
            # Step 3: Extract acoustic features
            logger.info("Extracting acoustic features")
            acoustic_features = await extract_acoustic_features(
                tmp_file_path,
                phoneme_segments
            )
            
            # Step 4: Compute phoneme deviations
            logger.info("Computing phoneme deviations")
            phoneme_deviations = await compute_phoneme_deviations(
                acoustic_features,
                target_accent=target_accent,
                phoneme_segments=phoneme_segments
            )
            
            # Step 5: Get user history from MongoDB
            user_history = await _get_user_history(user_id, language, target_accent)
            
            # Step 6: Call AccentCoach agent
            logger.info("Calling AccentCoach agent")
            agent_feedback = await call_accent_agent(
                user_id=user_id,
                session_id=session_id,
                language=language,
                target_accent=target_accent,
                phoneme_deviations=phoneme_deviations,
                acoustic_features=acoustic_features,
                transcribed_text=transcribed_text,
                user_history=user_history
            )
            
            # Step 7: Generate TTS audio for feedback
            logger.info("Generating TTS audio")
            tts_audio = await text_to_speech(
                agent_feedback.get("feedback_summary", "Good job!"),
                accent=target_accent
            )
            
            # Step 8: Save session data to MongoDB
            session_data = SessionData(
                session_id=session_id,
                language=language,
                target_accent=target_accent,
                accent_score=agent_feedback.get("accent_score", 0.0),
                phoneme_deviations=phoneme_deviations,
                acoustic_features=acoustic_features,
                exercises=agent_feedback.get("personalized_exercises", []),
                feedback_summary=agent_feedback.get("feedback_summary", "")
            )
            
            await _save_session(user_id, session_data)
            
            # Step 9: Save feedback
            feedback = Feedback(
                feedback_id=f"fb_{session_id}",
                session_id=session_id,
                user_id=user_id,
                accent_score=agent_feedback.get("accent_score", 0.0),
                strengths=agent_feedback.get("strengths", []),
                weaknesses=agent_feedback.get("weaknesses", []),
                personalized_exercises=agent_feedback.get("personalized_exercises", []),
                feedback_summary=agent_feedback.get("feedback_summary", "")
            )
            
            await _save_feedback(feedback)
            
            # Return response
            return JSONResponse({
                "success": True,
                "session_id": session_id,
                "transcribed_text": transcribed_text,
                "phoneme_deviations": phoneme_deviations,
                "accent_score": agent_feedback.get("accent_score", 0.0),
                "strengths": agent_feedback.get("strengths", []),
                "weaknesses": agent_feedback.get("weaknesses", []),
                "personalized_exercises": agent_feedback.get("personalized_exercises", []),
                "feedback_summary": agent_feedback.get("feedback_summary", ""),
                "tts_audio_base64": _encode_audio_base64(tts_audio)
            })
            
        finally:
            # Clean up temp file
            os.unlink(tmp_file_path)
            
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _get_user_history(user_id: str, language: str, accent: str) -> dict:
    """Get user's previous session history"""
    try:
        profiles_collection = Database.get_collection("profiles")
        profile = await profiles_collection.find_one({
            "user_id": user_id,
            "language": language,
            "accent": accent
        })
        
        if profile:
            return {
                "past_sessions": len(profile.get("session_history", [])),
                "average_accent_score": profile.get("overall_score", 0.0),
                "struggle_areas": profile.get("struggle_areas", [])
            }
        return {}
    except Exception as e:
        logger.error(f"Failed to get user history: {e}")
        return {}


async def _save_session(user_id: str, session_data: SessionData):
    """Save session data to MongoDB"""
    try:
        sessions_collection = Database.get_collection("sessions")
        await sessions_collection.insert_one(session_data.model_dump())
        
        # Update user profile
        profiles_collection = Database.get_collection("profiles")
        await profiles_collection.update_one(
            {
                "user_id": user_id,
                "language": session_data.language,
                "accent": session_data.target_accent
            },
            {
                "$push": {"session_history": session_data.model_dump()},
                "$inc": {"total_sessions": 1},
                "$set": {"updated_at": session_data.timestamp}
            },
            upsert=True
        )
    except Exception as e:
        logger.error(f"Failed to save session: {e}")


async def _save_feedback(feedback: Feedback):
    """Save feedback to MongoDB"""
    try:
        feedback_collection = Database.get_collection("feedback")
        await feedback_collection.insert_one(feedback.model_dump())
    except Exception as e:
        logger.error(f"Failed to save feedback: {e}")


def _encode_audio_base64(audio_bytes: bytes) -> str:
    """Encode audio bytes to base64 for JSON response"""
    import base64
    return base64.b64encode(audio_bytes).decode("utf-8")

