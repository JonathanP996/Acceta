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
import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.transcribe import transcribe_audio
from services.align import align_phonemes
from services.features import extract_acoustic_features
from services.deviation_model import _predict_personalized_benchmarks
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
    Extract voice baseline from onboarding recording
    
    User records themselves speaking naturally in their native language.
    We extract their voice characteristics and predict personalized benchmarks
    for the target accent.
    
    Args:
        user_id: User identifier
        language: Target language (e.g., "english")
        target_accent: Target accent (e.g., "american")
        audio_file: Audio recording of user speaking naturally
    
    Returns:
        Voice baseline data with predicted benchmarks
    """
    try:
        # Save uploaded audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            audio_bytes = await audio_file.read()
            tmp_file.write(audio_bytes)
            tmp_file_path = tmp_file.name
        
        try:
            # Step 1: Transcribe (to get text for phoneme alignment)
            logger.info(f"Transcribing onboarding audio for user {user_id}")
            transcription = await transcribe_audio(audio_bytes, language=language)
            transcribed_text = transcription["transcribed_text"]
            
            if not transcribed_text or len(transcribed_text.strip()) < 3:
                raise HTTPException(
                    status_code=400,
                    detail="Could not transcribe audio. Please speak clearly and try again."
                )
            
            # Step 2: Align phonemes
            logger.info("Aligning phonemes for baseline extraction")
            phoneme_segments = await align_phonemes(
                tmp_file_path,
                transcribed_text,
                language=language
            )
            
            # Step 3: Extract acoustic features (this is the user's baseline)
            logger.info("Extracting baseline acoustic features")
            baseline_features = await extract_acoustic_features(
                tmp_file_path,
                phoneme_segments
            )
            
            # Step 4: Extract baseline characteristics
            pitch_contour = baseline_features.get("pitch_contour", [200.0])
            valid_pitches = [p for p in pitch_contour if 80 <= p <= 500]
            baseline_pitch_mean = float(np.mean(valid_pitches)) if valid_pitches else 200.0
            baseline_pitch_std = float(np.std(valid_pitches)) if len(valid_pitches) > 1 else 30.0
            
            baseline_intensity = baseline_features.get("intensity", 0.5)
            baseline_intensity_mean = float(baseline_intensity)
            baseline_intensity_std = 0.2  # Estimate - would need multiple recordings for real std
            
            baseline_mfcc = baseline_features.get("mfcc_mean", [0.0] * 13)
            baseline_mfcc_profile = [float(m) for m in baseline_mfcc[:13]]
            
            # Extract rhythm characteristics
            per_phoneme = baseline_features.get("per_phoneme_features", [])
            if per_phoneme:
                durations = [f.get("duration", 0.1) for f in per_phoneme]
                vowel_durations = []
                consonant_durations = []
                
                for i, seg in enumerate(phoneme_segments):
                    if i < len(per_phoneme):
                        phoneme = seg.get("phoneme", "")
                        is_vowel = phoneme[0] in "AEIOU" if len(phoneme) > 0 else False
                        duration = per_phoneme[i].get("duration", 0.1)
                        
                        if is_vowel:
                            vowel_durations.append(duration)
                        else:
                            consonant_durations.append(duration)
                
                mean_duration = np.mean(durations) if durations else 0.1
                std_duration = np.std(durations) if len(durations) > 1 else 0.05
                baseline_rhythm_cv = float(std_duration / mean_duration) if mean_duration > 0 else 0.3
                
                avg_vowel = np.mean(vowel_durations) if vowel_durations else 0.15
                avg_consonant = np.mean(consonant_durations) if consonant_durations else 0.08
                baseline_vc_ratio = float(avg_vowel / avg_consonant) if avg_consonant > 0 else 1.5
            else:
                baseline_rhythm_cv = 0.3
                baseline_vc_ratio = 1.5
            
            # Step 5: Predict personalized benchmarks for target accent
            # This uses AI to predict what the user's voice should sound like in the target accent
            logger.info(f"Predicting personalized benchmarks for {target_accent} accent")
            predicted_benchmarks = await _predict_personalized_benchmarks(
                baseline_pitch_mean=baseline_pitch_mean,
                baseline_pitch_std=baseline_pitch_std,
                baseline_intensity_mean=baseline_intensity_mean,
                baseline_mfcc_profile=baseline_mfcc_profile,
                baseline_rhythm_cv=baseline_rhythm_cv,
                baseline_vc_ratio=baseline_vc_ratio,
                target_accent=target_accent,
                language=language
            )
            
            # Step 6: Store baseline in database
            baseline_doc = {
                "user_id": user_id,
                "language": language,
                "baseline_pitch_mean": baseline_pitch_mean,
                "baseline_pitch_std": baseline_pitch_std,
                "baseline_intensity_mean": baseline_intensity_mean,
                "baseline_intensity_std": baseline_intensity_std,
                "baseline_mfcc_profile": baseline_mfcc_profile,
                "baseline_rhythm_cv": baseline_rhythm_cv,
                "baseline_vowel_consonant_ratio": baseline_vc_ratio,
                **predicted_benchmarks,
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
                "message": "Voice baseline created successfully",
                "baseline": {
                    "your_natural_pitch": round(baseline_pitch_mean, 1),
                    "your_natural_intensity": round(baseline_intensity_mean, 3),
                    "your_natural_rhythm": round(baseline_rhythm_cv, 3),
                    "predicted_benchmarks": predicted_benchmarks
                }
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

