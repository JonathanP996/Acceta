"""
Agent Client Service
Calls the AccentCoach ADK agent from the backend
"""

import os
import logging
from typing import Dict, Any, Optional
import sys
import numpy as np

logger = logging.getLogger(__name__)

# Add agent directory to path
agent_path = os.path.join(os.path.dirname(__file__), "../../agent")
if os.path.exists(agent_path):
    sys.path.insert(0, agent_path)
    try:
        from accent_agent import run_accent_agent
        AGENT_AVAILABLE = True
    except ImportError:
        AGENT_AVAILABLE = False
        logger.warning("Accent agent not available, will use heuristic feedback")
else:
    AGENT_AVAILABLE = False
    logger.warning("Agent directory not found, will use heuristic feedback")


async def call_accent_agent(
        user_id: str,
        session_id: str,
        language: str,
        target_accent: str,
        phoneme_deviations: Dict[str, float],
        acoustic_features: Dict[str, Any],
        transcribed_text: str,
        user_history: Optional[Dict[str, Any]] = None,
        expected_text: Optional[str] = None,
        speaking_rate: Optional[Dict[str, Any]] = None,
        scoring_breakdown: Optional[Dict[str, Any]] = None,
        accent_classification: Optional[Dict[str, Any]] = None  # NEW: ML accent classification
    ) -> Dict[str, Any]:
    """
    Call the AccentCoach agent with pronunciation data
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        language: Target language
        target_accent: Target accent
        phoneme_deviations: Phoneme deviation scores
        acoustic_features: Acoustic feature data
        transcribed_text: Transcribed speech
        user_history: Previous session history
    
    Returns:
        Agent response with feedback and exercises
    """
    try:
        # Validate we have real deviations (not just defaults)
        if not phoneme_deviations or len(phoneme_deviations) == 0:
            logger.warning("No phoneme deviations provided")
            return {
                "accent_score": 0.0,
                "strengths": [],
                "weaknesses": ["No speech detected in audio"],
                "personalized_exercises": ["Please record audio with clear speech"],
                "feedback_summary": "No speech detected. Please speak clearly and try again."
            }
        
        # Check if deviations indicate silence (all very high = likely silence)
        # RELAXED: Only flag as silence if deviations are extremely high AND we have other indicators
        avg_deviation = sum(phoneme_deviations.values()) / len(phoneme_deviations)
        
        # Get acoustic features to double-check
        per_phoneme_features = acoustic_features.get("per_phoneme_features", [])
        if per_phoneme_features:
            valid_intensities = [f.get("intensity", 0.5) for f in per_phoneme_features if f.get("intensity", 0.5) > 0.001]
            avg_intensity = np.mean(valid_intensities) if valid_intensities else 0.0
        else:
            avg_intensity = acoustic_features.get("intensity", 0.5)
        
        # Only flag as silence if BOTH conditions are met (very strict)
        if avg_deviation > 0.95 and avg_intensity < 0.001:
            logger.warning(f"Very high deviation ({avg_deviation:.2f}) AND low intensity ({avg_intensity:.6f}) - likely silence")
            return {
                "accent_score": 0.0,
                "strengths": [],
                "weaknesses": ["No clear speech detected"],
                "personalized_exercises": ["Please speak clearly into the microphone", "Check your microphone is working"],
                "feedback_summary": "No clear speech detected in the recording. Please speak clearly and try again."
            }
        
        # Calculate accurate score from real phoneme deviations
        accent_score = max(0.0, min(100.0, (1.0 - avg_deviation) * 100))
        
        # Analyze specific phoneme issues for accurate feedback
        high_deviation_phonemes = [
            (phoneme, dev) for phoneme, dev in phoneme_deviations.items() 
            if dev > 0.4
        ]
        high_deviation_phonemes.sort(key=lambda x: x[1], reverse=True)
        
        # Get acoustic feature insights
        per_phoneme_features = acoustic_features.get("per_phoneme_features", [])
        if per_phoneme_features:
            valid_pitches = [f.get("pitch", 200.0) for f in per_phoneme_features if 50 < f.get("pitch", 200.0) < 500]
            valid_intensities = [f.get("intensity", 0.5) for f in per_phoneme_features if f.get("intensity", 0.5) > 0.01]
            avg_pitch = np.mean(valid_pitches) if valid_pitches else 200.0
            avg_intensity = np.mean(valid_intensities) if valid_intensities else 0.5
        else:
            avg_pitch = 200.0
            avg_intensity = 0.5
        
        # Generate accurate feedback based on actual analysis
        strengths = []
        weaknesses = []
        exercises = []
        
        # Analyze strengths
        if avg_deviation < 0.3:
            strengths.append("Excellent pronunciation accuracy")
        if len(high_deviation_phonemes) < len(phoneme_deviations) * 0.3:
            strengths.append("Most phonemes are well-pronounced")
        if 0.4 <= avg_intensity <= 0.7:
            strengths.append("Good speech intensity and clarity")
        
        # Analyze weaknesses based on actual deviations
        if high_deviation_phonemes:
            top_issues = high_deviation_phonemes[:3]
            issue_phonemes = [p[0] for p in top_issues]
            if any(p.lower() in "aeiou" for p in issue_phonemes):
                weaknesses.append("Vowel sounds need improvement")
            if any(p.lower() not in "aeiou" for p in issue_phonemes):
                weaknesses.append("Some consonant sounds need work")
        
        if avg_pitch < 150 or avg_pitch > 250:
            weaknesses.append("Pitch patterns differ from target accent")
        
        if avg_intensity < 0.3:
            weaknesses.append("Speech intensity is too low")
        elif avg_intensity > 0.8:
            weaknesses.append("Speech intensity is too high")
        
        # Generate specific exercises based on actual issues
        if high_deviation_phonemes:
            top_phoneme = high_deviation_phonemes[0][0]
            exercises.append(f"Focus on pronouncing '{top_phoneme}' sound correctly")
        
        if any("vowel" in w.lower() for w in weaknesses):
            exercises.append("Practice vowel sounds with native speaker recordings")
        
        if any("consonant" in w.lower() for w in weaknesses):
            exercises.append("Work on consonant clarity and tongue placement")
        
        if any("pitch" in w.lower() for w in weaknesses):
            exercises.append("Practice intonation patterns of the target accent")
        
        # Default exercises if none generated
        if not exercises:
            exercises.append("Continue practicing with native speaker examples")
        
        # Try to use actual agent FIRST (more accurate feedback with multi-signal approach)
        if AGENT_AVAILABLE:
            try:
                # Prepare comprehensive agent input with ALL signals (multi-signal approach)
                # Signal 1: Whisper STT (transcribed_text, expected_text, word_accuracy)
                # Signal 2: Acoustic features (Librosa: MFCCs, pitch, formants, intensity)
                # Signal 3: Phoneme deviations (MFA alignment)
                # Signal 4: User history (MongoDB: past sessions, progress)
                # Signal 5: Speaking rate (words/sec, phonemes/sec)
                # Signal 6: ML Accent Classifier (wav2vec2 + CNN) - NEW!
                agent_input = {
                    "user_id": user_id,
                    "session_id": session_id,
                    "language": language,
                    "target_accent": target_accent,
                    "phoneme_deviations": phoneme_deviations,  # MFA phoneme alignment
                    "acoustic_features": acoustic_features,  # Librosa: MFCCs, pitch, formants, intensity
                    "transcribed_text": transcribed_text,  # Whisper STT
                    "expected_text": expected_text,  # For word accuracy comparison
                    "user_history": user_history or {},  # MongoDB: iterative learning data
                    "speaking_rate": speaking_rate or {},  # Speaking rate analysis
                    "scoring_breakdown": scoring_breakdown or {},  # Detailed scoring for reasoning
                    "accent_classification": accent_classification or {}  # NEW: ML accent classifier results
                }
                
                # Call agent with timeout
                import asyncio
                try:
                    result = await asyncio.wait_for(run_accent_agent(agent_input), timeout=10.0)
                    logger.info(f"Agent returned feedback for session {session_id}")
                    return result
                except asyncio.TimeoutError:
                    logger.warning("Agent call timed out, using heuristic feedback")
                    # Fall through to heuristic feedback below
                except Exception as agent_error:
                    logger.warning(f"Agent call failed ({agent_error}), using heuristic feedback")
                    # Fall through to heuristic feedback below
            except Exception as e:
                logger.warning(f"Agent unavailable ({e}), using heuristic feedback")
                # Fall through to heuristic feedback below
        
        # Fallback: Generate heuristic feedback if agent not available or failed
        logger.info(f"Using heuristic feedback for session {session_id} (score: {accent_score:.1f}%, {len(high_deviation_phonemes)} high-deviation phonemes)")
        
        # Generate summary for heuristic feedback
        if accent_score >= 80:
            summary = f"Excellent! Your {target_accent} accent accuracy is {accent_score:.1f}%. You're very close to native pronunciation!"
        elif accent_score >= 60:
            summary = f"Good progress! Your {target_accent} accent accuracy is {accent_score:.1f}%. Focus on the areas mentioned above."
        elif accent_score >= 40:
            summary = f"Your {target_accent} accent accuracy is {accent_score:.1f}%. Keep practicing the specific sounds mentioned."
        else:
            summary = f"Your {target_accent} accent accuracy is {accent_score:.1f}%. Focus on basic pronunciation fundamentals."
        
        return {
            "accent_score": accent_score,
            "strengths": strengths if strengths else ["Keep practicing"],
            "weaknesses": weaknesses if weaknesses else ["Continue working on pronunciation"],
            "personalized_exercises": exercises if exercises else ["Practice common phrases"],
            "feedback_summary": summary
        }
        
    except Exception as e:
        logger.error(f"Feedback generation failed: {e}")
        # Return fallback feedback
        avg_deviation = sum(phoneme_deviations.values()) / len(phoneme_deviations) if phoneme_deviations else 0.5
        accent_score = max(0.0, min(100.0, (1.0 - avg_deviation) * 100))
        return {
            "accent_score": accent_score,
            "strengths": ["Keep practicing"],
            "weaknesses": ["Continue working on pronunciation"],
            "personalized_exercises": ["Practice common phrases"],
            "feedback_summary": f"Your {target_accent} accent accuracy is {accent_score:.1f}%. Keep practicing!"
        }

