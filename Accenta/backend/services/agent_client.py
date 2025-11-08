"""
Agent Client Service
Calls the AccentCoach ADK agent from the backend
"""

import os
import logging
from typing import Dict, Any, Optional
import sys

# Add agent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../agent"))

from accent_agent import run_accent_agent

logger = logging.getLogger(__name__)


async def call_accent_agent(
    user_id: str,
    session_id: str,
    language: str,
    target_accent: str,
    phoneme_deviations: Dict[str, float],
    acoustic_features: Dict[str, Any],
    transcribed_text: str,
    user_history: Optional[Dict[str, Any]] = None
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
        # Prepare agent input
        agent_input = {
            "user_id": user_id,
            "session_id": session_id,
            "language": language,
            "target_accent": target_accent,
            "phoneme_deviations": phoneme_deviations,
            "acoustic_features": acoustic_features,
            "transcribed_text": transcribed_text,
            "user_history": user_history or {}
        }
        
        # Call agent
        result = await run_accent_agent(agent_input)
        
        logger.info(f"Agent returned feedback for session {session_id}")
        return result
        
    except Exception as e:
        logger.error(f"Agent call failed: {e}")
        # Return fallback feedback
        return {
            "accent_score": 50.0,
            "strengths": ["Keep practicing"],
            "weaknesses": ["Continue working on pronunciation"],
            "personalized_exercises": ["Practice common phrases"],
            "feedback_summary": "Analysis in progress. Please try again."
        }

