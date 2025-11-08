"""
FastAPI Routes for Multi-Sentence Accent Analysis
Analyzes multiple sentences and combines scores for more accurate accent assessment
"""

import os
import logging
import tempfile
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import json

import sys
from pathlib import Path

# Add parent directory to path for schemas
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.transcribe import transcribe_audio
from services.align import align_phonemes
from services.features import extract_acoustic_features
from services.deviation_model import compute_phoneme_deviations
from services.agent_client import call_accent_agent
from db import Database

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter(prefix="/api", tags=["multi-sentence-analysis"])


def _validate_audio(audio_path: str) -> tuple:
    """Validate audio file has actual content"""
    try:
        import librosa
        y, sr = librosa.load(audio_path, sr=None)
        
        # Check duration
        duration = len(y) / sr
        if duration < 0.5:
            return False, "Audio is too short (less than 0.5 seconds)"
        
        # Check RMS energy
        rms = librosa.feature.rms(y=y)[0]
        avg_rms = float(rms.mean())
        if avg_rms < 0.001:
            return False, "Audio appears to be silence or too quiet"
        
        return True, None
    except Exception as e:
        logger.error(f"Audio validation error: {e}")
        return False, f"Error validating audio: {str(e)}"


def _compare_transcription_to_expected(transcribed: str, expected: str) -> tuple:
    """Compare transcribed text to expected text using sequence matching"""
    import difflib
    similarity = difflib.SequenceMatcher(None, transcribed.lower(), expected.lower()).ratio()
    word_accuracy = similarity * 100
    
    warning = None
    if word_accuracy < 50:
        warning = f"Low word accuracy ({word_accuracy:.1f}%) - you may have said the wrong phrase"
    
    return word_accuracy, warning


async def _analyze_single_sentence(
    audio_bytes: bytes,
    audio_path: str,
    expected_text: Optional[str],
    language: str,
    target_accent: str,
    user_id: str,
    sentence_index: int
) -> Dict[str, Any]:
    """
    Analyze a single sentence and return its score and features.
    Returns a dictionary with score, features, and metadata.
    """
    try:
        # Step 1: Transcribe
        transcription = await transcribe_audio(audio_bytes, language=language)
        transcribed_text = transcription.get("transcribed_text", "")
        
        if not transcribed_text or len(transcribed_text.strip()) < 1:
            logger.warning(f"Sentence {sentence_index}: Empty transcription, using placeholder")
            transcribed_text = "speech detected"
        
        # Step 2: Word accuracy check
        word_accuracy = None
        if expected_text:
            word_accuracy, _ = _compare_transcription_to_expected(transcribed_text, expected_text)
        
        # Step 3: Phoneme alignment
        phoneme_segments = await align_phonemes(audio_path, transcribed_text, language=language)
        
        # Step 4: Extract acoustic features
        acoustic_features = await extract_acoustic_features(
            audio_path,
            phoneme_segments=phoneme_segments
        )
        
        # Step 5: Compute deviations and score
        deviation_result = await compute_phoneme_deviations(
            acoustic_features,
            target_accent=target_accent,
            phoneme_segments=phoneme_segments,
            user_id=user_id,
            language=language,
            expected_text=expected_text
        )
        
        if isinstance(deviation_result, dict) and "deviations" in deviation_result:
            phoneme_deviations = deviation_result["deviations"]
            scoring_details = deviation_result.get("scoring_details", {})
        else:
            phoneme_deviations = deviation_result
            scoring_details = {}
        
        # Extract the accent score
        accent_score = scoring_details.get("summary", {}).get("accent_score_percent", 0.0)
        
        # Calculate feature vector for this sentence
        # F_i = [MFCC_mean, pitch_mean, duration_mean, formants_mean]
        mfcc_mean = acoustic_features.get("mfcc_mean", [0.0] * 13)
        pitch_contour = acoustic_features.get("pitch_contour", [])
        intensity = acoustic_features.get("intensity", 0.5)
        formant_ratios = acoustic_features.get("formant_ratios", [0.5, 1.0, 1.5])
        
        # Calculate means
        pitch_mean = float(sum(pitch_contour) / len(pitch_contour)) if pitch_contour else 0.0
        mfcc_magnitude = float(sum(abs(x) for x in mfcc_mean[:5])) if mfcc_mean else 0.0
        
        feature_vector = {
            "mfcc_magnitude": mfcc_magnitude,
            "pitch_mean": pitch_mean,
            "intensity": float(intensity),
            "formant_f1": float(formant_ratios[0]) if len(formant_ratios) > 0 else 0.0,
            "formant_f2": float(formant_ratios[1]) if len(formant_ratios) > 1 else 0.0,
        }
        
        return {
            "sentence_index": sentence_index,
            "transcribed_text": transcribed_text,
            "expected_text": expected_text,
            "word_accuracy": word_accuracy,
            "accent_score": float(accent_score),
            "phoneme_deviations": phoneme_deviations,
            "feature_vector": feature_vector,
            "scoring_details": scoring_details,
            "phoneme_count": len(phoneme_segments),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error analyzing sentence {sentence_index}: {e}")
        return {
            "sentence_index": sentence_index,
            "success": False,
            "error": str(e),
            "accent_score": 0.0
        }


@router.post("/analyze_accent_multi")
async def analyze_accent_multi(
    user_id: str = Form(...),
    session_id: str = Form(...),
    language: str = Form(...),
    target_accent: str = Form(...),
    expected_texts: str = Form(...),  # JSON array of expected texts
    audio_files: List[UploadFile] = File(...)  # Multiple audio files
):
    """
    Multi-sentence accent analysis endpoint.
    
    Analyzes multiple sentences and combines scores using weighted averaging:
    AccentScore = 1 - (1/N) * sum(w_i * d_i)
    
    Where:
    - N = number of sentences
    - w_i = weight for sentence i (based on phoneme count, vowel content, etc.)
    - d_i = distance score for sentence i
    
    Args:
        user_id: User ID
        session_id: Session ID
        language: Language code (ISO-639-1)
        target_accent: Target accent name
        expected_texts: JSON array of expected texts for each sentence
        audio_files: List of audio files (one per sentence)
    
    Returns:
        Combined accent score and per-sentence feedback
    """
    try:
        # Parse expected texts
        try:
            expected_texts_list = json.loads(expected_texts)
            if not isinstance(expected_texts_list, list):
                raise ValueError("expected_texts must be a JSON array")
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid JSON in expected_texts: {str(e)}"
            )
        
        if len(audio_files) != len(expected_texts_list):
            raise HTTPException(
                status_code=400,
                detail=f"Mismatch: {len(audio_files)} audio files but {len(expected_texts_list)} expected texts"
            )
        
        logger.info(f"Starting multi-sentence analysis: {len(audio_files)} sentences for session {session_id}")
        
        # Analyze each sentence
        sentence_results = []
        temp_files = []
        
        try:
            for i, (audio_file, expected_text) in enumerate(zip(audio_files, expected_texts_list)):
                logger.info(f"Analyzing sentence {i+1}/{len(audio_files)}: '{expected_text[:50]}...'")
                
                # Save audio to temp file
                audio_bytes = await audio_file.read()
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                    tmp_file.write(audio_bytes)
                    tmp_file_path = tmp_file.name
                    temp_files.append(tmp_file_path)
                
                # Validate audio
                audio_valid, validation_error = _validate_audio(tmp_file_path)
                if not audio_valid:
                    logger.warning(f"Sentence {i+1}: Audio validation failed: {validation_error}")
                    sentence_results.append({
                        "sentence_index": i,
                        "success": False,
                        "error": validation_error,
                        "accent_score": 0.0,
                        "expected_text": expected_text
                    })
                    continue
                
                # Analyze sentence
                result = await _analyze_single_sentence(
                    audio_bytes=audio_bytes,
                    audio_path=tmp_file_path,
                    expected_text=expected_text,
                    language=language,
                    target_accent=target_accent,
                    user_id=user_id,
                    sentence_index=i
                )
                sentence_results.append(result)
        
        finally:
            # Clean up temp files
            for tmp_path in temp_files:
                try:
                    os.unlink(tmp_path)
                except:
                    pass
        
        # Filter successful analyses
        successful_results = [r for r in sentence_results if r.get("success", False)]
        
        if not successful_results:
            raise HTTPException(
                status_code=400,
                detail="All sentence analyses failed. Please check your audio files."
            )
        
        logger.info(f"Successfully analyzed {len(successful_results)}/{len(sentence_results)} sentences")
        
        # Calculate weights for each sentence
        # Weight by: phoneme count (more phonemes = more important) and vowel content
        weights = []
        for result in successful_results:
            phoneme_count = result.get("phoneme_count", 0)
            # Base weight on phoneme count (normalize to 0-1)
            # More phonemes = more representative of accent
            weight = min(1.0, phoneme_count / 30.0)  # 30 phonemes = full weight
            weights.append(weight)
        
        # Normalize weights so they sum to 1
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        else:
            # Equal weights if all weights are 0
            weights = [1.0 / len(successful_results)] * len(successful_results)
        
        # Calculate combined score using weighted average
        # AccentScore = 1 - (1/N) * sum(w_i * d_i)
        # Where d_i = 1 - (accent_score_i / 100) is the deviation
        combined_score = 0.0
        total_weighted_score = 0.0
        
        for i, result in enumerate(successful_results):
            score = result.get("accent_score", 0.0)
            weight = weights[i]
            # Convert score to deviation: d_i = 1 - (score / 100)
            deviation = 1.0 - (score / 100.0)
            # Weighted contribution
            total_weighted_score += weight * score
        
        # Final combined score (weighted average)
        combined_score = total_weighted_score
        
        # Calculate per-sentence statistics
        scores = [r.get("accent_score", 0.0) for r in successful_results]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        min_score = min(scores) if scores else 0.0
        max_score = max(scores) if scores else 0.0
        
        # Identify struggle areas across all sentences
        all_phoneme_deviations = {}
        for result in successful_results:
            deviations = result.get("phoneme_deviations", {})
            for phoneme, deviation in deviations.items():
                if phoneme not in all_phoneme_deviations:
                    all_phoneme_deviations[phoneme] = []
                all_phoneme_deviations[phoneme].append(deviation)
        
        # Calculate average deviation per phoneme
        struggle_areas = []
        for phoneme, deviation_list in all_phoneme_deviations.items():
            avg_deviation = sum(deviation_list) / len(deviation_list)
            if avg_deviation > 0.5:  # High deviation = struggle area
                struggle_areas.append({
                    "phoneme": phoneme,
                    "average_deviation": round(avg_deviation, 3),
                    "occurrences": len(deviation_list)
                })
        
        # Sort by deviation (worst first)
        struggle_areas.sort(key=lambda x: x["average_deviation"], reverse=True)
        
        logger.info(f"Combined accent score: {combined_score:.1f}% (from {len(successful_results)} sentences)")
        logger.info(f"Score range: {min_score:.1f}% - {max_score:.1f}%, Average: {avg_score:.1f}%")
        
        # Prepare response
        response_data = {
            "success": True,
            "session_id": session_id,
            "combined_accent_score": round(float(combined_score), 1),
            "average_score": round(float(avg_score), 1),
            "min_score": round(float(min_score), 1),
            "max_score": round(float(max_score), 1),
            "sentences_analyzed": len(successful_results),
            "total_sentences": len(sentence_results),
            "per_sentence_results": [
                {
                    "sentence_index": r.get("sentence_index"),
                    "expected_text": r.get("expected_text"),
                    "transcribed_text": r.get("transcribed_text"),
                    "accent_score": round(float(r.get("accent_score", 0.0)), 1),
                    "word_accuracy": round(float(r.get("word_accuracy", 0.0)), 1) if r.get("word_accuracy") else None,
                    "phoneme_count": r.get("phoneme_count", 0),
                    "weight": round(float(weights[i]), 3) if i < len(weights) else 0.0
                }
                for i, r in enumerate(successful_results)
            ],
            "struggle_areas": struggle_areas[:10],  # Top 10 struggle areas
            "feedback_summary": f"Analyzed {len(successful_results)} sentences. Your {target_accent} accent accuracy is {combined_score:.1f}% overall."
        }
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in multi-sentence analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Multi-sentence analysis failed: {str(e)}"
        )

