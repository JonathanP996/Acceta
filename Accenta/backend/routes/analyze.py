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
logger.setLevel(logging.INFO)  # Ensure INFO level logging

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze_accent")
async def analyze_accent(
    user_id: str = Form(...),
    session_id: str = Form(...),
    language: str = Form(...),
    target_accent: str = Form(...),
    expected_text: str = Form(None),  # The phrase the user should have said
    audio_file: UploadFile = File(...)
):
    """
    Full accent analysis endpoint
    Processes audio through: Whisper → Simplified Analysis → Agent → Feedback
    """
    try:
        # Save uploaded audio to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            audio_bytes = await audio_file.read()
            tmp_file.write(audio_bytes)
            tmp_file_path = tmp_file.name
        
        try:
            # Step 0: Validate audio has actual content (not silence)
            logger.info(f"Validating audio for session {session_id}")
            audio_valid, validation_error = await _validate_audio(tmp_file_path)
            if not audio_valid:
                raise HTTPException(
                    status_code=400,
                    detail=validation_error or "Audio appears to be empty or too quiet. Please record again."
                )
            
            # Step 1: Transcribe audio (this is fast)
            logger.info(f"Transcribing audio for session {session_id}")
            transcription = await transcribe_audio(audio_bytes, language=language)
            transcribed_text = transcription["transcribed_text"]
            
            # Validate transcription has content - RELAXED (Whisper is good at detecting speech)
            # If Whisper couldn't transcribe, it might still be valid audio (just unclear)
            # Don't reject - let the analysis continue with what we have
            if not transcribed_text or len(transcribed_text.strip()) < 1:
                logger.warning(f"Whisper returned empty/very short transcription: '{transcribed_text}', but continuing analysis")
                # Use a placeholder to continue - the acoustic analysis will still work
                if not transcribed_text or len(transcribed_text.strip()) == 0:
                    transcribed_text = "speech detected"  # Placeholder to continue
            
            # Step 1.5: Verify user said the correct phrase (if expected_text provided)
            word_accuracy = None
            text_match_warning = None
            if expected_text:
                word_accuracy, text_match_warning = _compare_transcription_to_expected(
                    transcribed_text, 
                    expected_text
                )
                logger.info(f"Word accuracy: {word_accuracy:.1f}% (expected: '{expected_text}', got: '{transcribed_text}')")
                if word_accuracy < 50:
                    logger.warning(f"Low word accuracy ({word_accuracy:.1f}%) - user may have said wrong phrase")
            
            # Step 2: Phoneme alignment (using improved English phoneme dictionary)
            logger.info("Aligning phonemes to audio timeline")
            phoneme_segments = await align_phonemes(
                tmp_file_path,
                transcribed_text,
                language=language
            )
            
            # Step 2.5: Classify accent using ML classifier (NEW)
            # Use fast heuristic by default to avoid timeout - ML classifier can be slow
            logger.info("Classifying accent (using fast heuristic to avoid timeout)")
            try:
                # Use asyncio timeout wrapper to ensure we don't block
                import asyncio
                from services.accent_classifier import classify_accent, _heuristic_accent_classification
                accent_classification = await asyncio.wait_for(
                    classify_accent(
                        tmp_file_path,
                        use_classifier=False,  # Disable ML classifier for now to avoid timeout
                        timeout=5.0
                    ),
                    timeout=5.0  # Maximum 5 seconds total
                )
            except asyncio.TimeoutError:
                logger.warning("Accent classification timed out, using quick heuristic fallback")
                from services.accent_classifier import _heuristic_accent_classification
                accent_classification = _heuristic_accent_classification(tmp_file_path)
            except Exception as e:
                logger.warning(f"Accent classification failed: {e}, using heuristic fallback")
                from services.accent_classifier import _heuristic_accent_classification
                accent_classification = _heuristic_accent_classification(tmp_file_path)
            logger.info(f"Accent classification: {accent_classification.get('predicted_accent')} "
                      f"(confidence: {accent_classification.get('confidence', 0):.2f}, "
                      f"method: {accent_classification.get('method', 'unknown')})")
            
            # Step 3: Extract acoustic features (MFCCs, pitch, formants, duration, intensity)
            logger.info("Extracting acoustic features (MFCCs, pitch, formants, duration)")
            try:
                acoustic_features = await extract_acoustic_features(
                    tmp_file_path,
                    phoneme_segments
                )
            except Exception as e:
                logger.warning(f"Feature extraction failed, using fallback: {e}")
                # Use minimal fallback features
                acoustic_features = {
                    "mfcc_mean": [0.0] * 13,
                    "pitch_contour": [200.0],
                    "formant_ratios": [0.5, 1.0, 1.5],
                    "intensity": 0.5,
                    "per_phoneme_features": [
                        {
                            "phoneme": seg.get("phoneme", "a"),
                            "mfcc_mean": [0.0] * 5,
                            "pitch": 200.0,
                            "duration": seg.get("duration", 0.1),
                            "intensity": 0.5
                        }
                        for seg in phoneme_segments[:10]  # Limit to 10 for speed
                    ]
                }
            
            # Step 4: Compute pronunciation scoring (probabilistic modeling with multi-speaker reference)
            logger.info("Computing phoneme deviations (probabilistic modeling with normalized features)")
            deviation_result = await compute_phoneme_deviations(
                acoustic_features,
                target_accent=target_accent,
                phoneme_segments=phoneme_segments,
                user_id=user_id,  # For personalized baseline adaptation
                language=language  # NEW: For personalized baseline lookup
            )
            
            # Extract deviations and scoring details
            if isinstance(deviation_result, dict) and "deviations" in deviation_result:
                phoneme_deviations = deviation_result["deviations"]
                scoring_details = deviation_result.get("scoring_details", {})
            else:
                # Legacy format (just deviations dict)
                phoneme_deviations = deviation_result
                scoring_details = {}
            
            # Step 5: Get user history (quick DB query)
            user_history = await _get_user_history(user_id, language, target_accent)
            
            # Step 6: Call AccentCoach agent with ALL signals (multi-signal approach)
            logger.info("Calling AccentCoach agent with multi-signal data (Whisper + Librosa + MFA + History + Classifier)")
            try:
                # Pass comprehensive data including expected text, scoring breakdown, and accent classification
                agent_feedback = await call_accent_agent(
                    user_id=user_id,
                    session_id=session_id,
                    language=language,
                    target_accent=target_accent,
                    phoneme_deviations=phoneme_deviations,
                    acoustic_features=acoustic_features,
                    transcribed_text=transcribed_text,
                    expected_text=expected_text,  # For word accuracy analysis
                    user_history=user_history,  # For iterative feedback
                    speaking_rate=scoring_details.get("speaking_rate"),  # Speaking rate analysis
                    scoring_breakdown=scoring_details,  # Detailed scoring for reasoning
                    accent_classification=accent_classification  # NEW: ML accent classification
                )
            except Exception as e:
                logger.warning(f"Agent call failed, using fallback feedback: {e}")
                # Generate quick fallback feedback
                avg_deviation = sum(phoneme_deviations.values()) / len(phoneme_deviations) if phoneme_deviations else 0.5
                accent_score = max(0.0, min(100.0, (1.0 - avg_deviation) * 100))
                agent_feedback = {
                    "accent_score": accent_score,
                    "strengths": ["Clear pronunciation", "Good pace"],
                    "weaknesses": ["Some vowel sounds need work"] if avg_deviation > 0.3 else [],
                    "personalized_exercises": [
                        "Practice vowel sounds",
                        "Focus on word stress patterns"
                    ],
                    "feedback_summary": f"Your {target_accent} accent accuracy is {accent_score:.1f}%. Keep practicing!"
                }
            
            # Step 7: Skip TTS for now (makes it faster) - can add back later
            # tts_audio = await text_to_speech(
            #     agent_feedback.get("feedback_summary", "Good job!"),
            #     accent=target_accent
            # )
            
            # Step 8: Save session data (async, don't wait)
            try:
                from datetime import datetime
                session_data = SessionData(
                    session_id=session_id,
                    timestamp=transcription.get("timestamp") or datetime.now(),
                    language=language,
                    target_accent=target_accent,
                    accent_score=agent_feedback.get("accent_score", 0.0),
                    phoneme_deviations=phoneme_deviations,
                    exercises=agent_feedback.get("personalized_exercises", []),
                    feedback_summary=agent_feedback.get("feedback_summary", "")
                )
                # Don't await - save in background
                import asyncio
                asyncio.create_task(_save_session(user_id, session_data))
            except Exception as e:
                logger.warning(f"Failed to save session: {e}")
            
            # Step 9: Save feedback (async, don't wait)
            try:
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
                # Don't await - save in background
                import asyncio
                asyncio.create_task(_save_feedback(feedback))
            except Exception as e:
                logger.warning(f"Failed to save feedback: {e}")
            
            # Return response immediately with all feedback
            response_data = {
                "success": True,
                "session_id": session_id,
                "transcribed_text": transcribed_text,
                "expected_text": expected_text if expected_text else None,
                "word_accuracy": word_accuracy,
                "phoneme_deviations": phoneme_deviations,
                "accent_score": agent_feedback.get("accent_score", 0.0),
                "strengths": agent_feedback.get("strengths", []),
                "weaknesses": agent_feedback.get("weaknesses", []),
                "personalized_exercises": agent_feedback.get("personalized_exercises", []),
                "feedback_summary": agent_feedback.get("feedback_summary", ""),
                "scoring_breakdown": scoring_details,  # Add detailed scoring breakdown
            }
            
            # Add warning if text doesn't match
            if text_match_warning:
                response_data["text_match_warning"] = text_match_warning
                # Add to weaknesses if not already there
                if text_match_warning not in response_data["weaknesses"]:
                    response_data["weaknesses"].insert(0, text_match_warning)
            
            return JSONResponse(response_data)
            
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_file_path)
            except:
                pass
            
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


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


async def _validate_audio(audio_file_path: str) -> tuple:
    """
    Validate that audio file contains actual speech content
    
    Returns:
        (is_valid, error_message)
    """
    try:
        import librosa
        import numpy as np
        
        # Load audio
        y, sr = librosa.load(audio_file_path, sr=None)
        
        # Check 1: Audio duration
        duration = len(y) / sr
        if duration < 0.5:  # Less than 0.5 seconds
            return False, "Audio is too short. Please record at least 0.5 seconds."
        
        # Check 2: Audio energy/intensity (not silence) - RELAXED thresholds
        rms = librosa.feature.rms(y=y)[0]
        avg_rms = np.mean(rms)
        max_rms = np.max(rms)
        
        # Much more lenient thresholds - only reject if truly silent
        if avg_rms < 0.001 and max_rms < 0.01:
            logger.warning(f"Very low RMS: avg={avg_rms:.6f}, max={max_rms:.6f}")
            return False, "Audio appears to be silence or too quiet. Please speak louder."
        
        # Check 3: Audio has variation (not just noise) - RELAXED
        rms_std = np.std(rms)
        if rms_std < 0.001:  # Very lenient - only reject if completely flat
            logger.warning(f"Very low RMS variation: {rms_std:.6f}")
            return False, "Audio lacks variation. Please speak clearly."
        
        # Check 4: Has some frequency content (not just DC) - RELAXED
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        avg_centroid = np.mean(spectral_centroid)
        if avg_centroid < 50:  # Very lenient - only reject if extremely low frequency
            logger.warning(f"Very low spectral centroid: {avg_centroid:.1f}Hz")
            return False, "Audio quality is too low. Please check your microphone."
        
        logger.info(f"Audio validation passed: duration={duration:.2f}s, avg_rms={avg_rms:.4f}, spectral_centroid={avg_centroid:.1f}Hz")
        return True, None
        
    except Exception as e:
        logger.error(f"Audio validation failed: {e}")
        # If validation fails, still allow processing but log warning
        return True, None  # Don't block on validation errors


def _compare_transcription_to_expected(transcribed: str, expected: str) -> tuple[float, Optional[str]]:
    """
    Compare transcribed text to expected phrase
    
    Returns:
        (word_accuracy_percentage, warning_message_if_low)
    """
    import re
    from difflib import SequenceMatcher
    
    # Normalize both texts (lowercase, remove punctuation)
    def normalize(text):
        # Remove punctuation and convert to lowercase
        text = re.sub(r'[^\w\s]', '', text.lower())
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text
    
    transcribed_norm = normalize(transcribed)
    expected_norm = normalize(expected)
    
    # Split into words
    transcribed_words = transcribed_norm.split()
    expected_words = expected_norm.split()
    
    if not expected_words:
        return 100.0, None
    
    if not transcribed_words:
        return 0.0, "No words detected in your speech. Please speak clearly."
    
    # Calculate word-level similarity using SequenceMatcher
    # This handles word order differences and partial matches
    similarity = SequenceMatcher(None, transcribed_norm, expected_norm).ratio()
    word_accuracy = similarity * 100
    
    # Also calculate exact word match percentage
    transcribed_set = set(transcribed_words)
    expected_set = set(expected_words)
    
    # Words that match exactly
    matching_words = transcribed_set.intersection(expected_set)
    exact_match_pct = (len(matching_words) / len(expected_set)) * 100 if expected_set else 0
    
    # Use the higher of the two (similarity accounts for word order, exact match is stricter)
    final_accuracy = max(word_accuracy, exact_match_pct * 0.8)  # Weight exact match slightly less
    
    # Generate warning if accuracy is low
    warning = None
    if final_accuracy < 50:
        warning = f"You said something different from the prompt. Expected: '{expected}', but heard: '{transcribed}'. Please repeat the exact phrase shown."
    elif final_accuracy < 70:
        warning = f"Some words don't match. Expected: '{expected}', but heard: '{transcribed}'. Try to match the phrase exactly."
    
    return round(final_accuracy, 1), warning


def _encode_audio_base64(audio_bytes: bytes) -> str:
    """Encode audio bytes to base64 for JSON response"""
    import base64
    return base64.b64encode(audio_bytes).decode("utf-8")
