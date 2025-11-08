"""
AccentCoach ADK Agent
Uses Google's Agent Development Kit (ADK) with Gemini to generate personalized accent feedback
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Try to import ADK
ADK_AVAILABLE = False
CallbackContext = None
LlmRequest = None
LlmResponse = None
types = None

try:
    from google.adk.agents import LlmAgent
    from google.adk.agents.callback_context import CallbackContext
    from google.adk.models import LlmRequest, LlmResponse
    from google.genai import types
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    logger.warning("ADK not available, using fallback agent")


# Fallback: Use direct Gemini API if ADK not available
if not ADK_AVAILABLE:
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        FALLBACK_AVAILABLE = True
    except ImportError:
        FALLBACK_AVAILABLE = False
        logger.warning("Google Generative AI not available")


def before_model_callback(
    callback_context, llm_request
):
    """
    Process pronunciation data before sending to LLM
    Extracts phoneme deviations and builds comprehensive prompt
    """
    state = callback_context.state
    
    # Extract user message (contains JSON payload)
    last_user_message = ""
    if llm_request.contents and len(llm_request.contents) > 0:
        for content in reversed(llm_request.contents):
            if content.role == "user" and content.parts and len(content.parts) > 0:
                if hasattr(content.parts[0], "text") and content.parts[0].text:
                    last_user_message = content.parts[0].text
                    break
    
    # Parse JSON payload if present
    try:
        if last_user_message.startswith("{") or last_user_message.startswith("["):
            payload = json.loads(last_user_message)
            state["phoneme_deviations"] = payload.get("phoneme_deviations", {})
            state["acoustic_features"] = payload.get("acoustic_features", {})
            state["user_history"] = payload.get("user_history", {})
            state["transcribed_text"] = payload.get("transcribed_text", "")
            state["target_accent"] = payload.get("target_accent", "American")
            logger.info("Parsed pronunciation data from payload")
    except json.JSONDecodeError:
        # Not JSON, continue with normal processing
        pass
    
    logger.info("[BEFORE MODEL] Processing accent analysis request")
    return None  # Continue with normal model request


def after_model_callback(
    callback_context, llm_response
):
    """
    Transform LLM response into structured JSON output
    """
    state = callback_context.state
    
    # Extract response text
    response_text = ""
    if llm_response and llm_response.content and llm_response.content.parts:
        for part in llm_response.content.parts:
            if hasattr(part, "text") and part.text:
                response_text += part.text
    
    if not response_text:
        return None
    
    # Parse structured output from LLM response
    try:
        # Try to extract JSON from response
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            structured_output = json.loads(json_str)
        else:
            # Generate structured output from text
            structured_output = _parse_feedback_to_json(response_text, state)
        
        # Store in state for retrieval
        state["structured_feedback"] = structured_output
        
        logger.info("[AFTER MODEL] Generated structured feedback")
        
        # Return modified response with structured data
        import copy
        modified_parts = [copy.deepcopy(part) for part in llm_response.content.parts]
        modified_parts[0].text = json.dumps(structured_output, indent=2)
        
        return LlmResponse(
            content=types.Content(role="model", parts=modified_parts)
        )
        
    except Exception as e:
        logger.error(f"Failed to structure response: {e}")
        return None


def _parse_feedback_to_json(response_text: str, state: Dict) -> Dict[str, Any]:
    """Parse natural language feedback into structured JSON"""
    phoneme_deviations = state.get("phoneme_deviations", {})
    transcribed_text = state.get("transcribed_text", "")
    target_accent = state.get("target_accent", "American")
    
    # Extract strengths and weaknesses from text
    strengths = []
    weaknesses = []
    
    # Simple keyword extraction (in production, use LLM to extract)
    if "good" in response_text.lower() or "excellent" in response_text.lower():
        strengths.append("Good pronunciation overall")
    if "improve" in response_text.lower() or "work on" in response_text.lower():
        weaknesses.append("Some phonemes need improvement")
    
    # Calculate accent score from deviations
    if phoneme_deviations:
        avg_deviation = sum(phoneme_deviations.values()) / len(phoneme_deviations)
        accent_score = max(0, min(100, (1 - avg_deviation) * 100))
    else:
        accent_score = 75.0
    
    # Generate exercises based on high-deviation phonemes
    high_deviations = {
        k: v for k, v in phoneme_deviations.items() 
        if v > 0.6
    }
    exercises = []
    for phoneme in high_deviations.keys():
        exercises.append(f"Practice: '{phoneme}' sound - focus on tongue placement and airflow")
    
    return {
        "accent_score": round(accent_score, 1),
        "strengths": strengths if strengths else ["Good effort"],
        "weaknesses": weaknesses if weaknesses else ["Continue practicing"],
        "personalized_exercises": exercises if exercises else ["Practice common phrases"],
        "feedback_summary": response_text[:500]  # Truncate if too long
    }


# Create ADK Agent
if ADK_AVAILABLE:
    root_agent = LlmAgent(
        name="accent_coach_agent",
        model="gemini-2.0-flash",
        description="AI agent that analyzes pronunciation and generates personalized accent feedback",
        instruction="""
        You are an expert accent coach helping users improve their pronunciation.
        
        Analyze the provided phoneme deviation data and acoustic features to:
        1. Identify strengths in the user's pronunciation
        2. Identify specific weaknesses (phonemes with high deviation scores)
        3. Generate personalized exercises targeting problem areas
        4. Provide encouraging, actionable feedback
        
        Return your analysis in JSON format with:
        - accent_score: 0-100 score
        - strengths: List of positive aspects
        - weaknesses: List of areas needing improvement
        - personalized_exercises: List of specific practice exercises
        - feedback_summary: Natural language summary
        
        Be encouraging and specific in your feedback.
        """,
        before_model_callback=before_model_callback,
        after_model_callback=after_model_callback,
    )
else:
    root_agent = None
    logger.warning("ADK Agent not available, will use fallback")


async def run_accent_agent(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main function to run the accent coach agent
    
    Args:
        data: Dictionary containing:
            - user_id: User identifier
            - session_id: Session identifier
            - language: Target language
            - target_accent: Target accent (e.g., "British", "American")
            - phoneme_deviations: Dict mapping phoneme -> deviation_score
            - acoustic_features: Dict with MFCC, pitch, formant data
            - transcribed_text: Transcribed speech text
            - user_history: Previous session data
    
    Returns:
        Dictionary with:
            - accent_score: Overall score (0-100)
            - strengths: List of strengths
            - weaknesses: List of weaknesses
            - personalized_exercises: List of exercise recommendations
            - feedback_summary: Natural language feedback
    """
    try:
        if ADK_AVAILABLE and root_agent:
            # Use ADK agent
            prompt = json.dumps(data, indent=2)
            response = root_agent.run(prompt)
            
            # Extract structured output from response
            if hasattr(response, "text"):
                try:
                    return json.loads(response.text)
                except json.JSONDecodeError:
                    # Fallback parsing
                    return _parse_feedback_to_json(response.text, {"phoneme_deviations": data.get("phoneme_deviations", {})})
            else:
                return _generate_fallback_feedback(data)
        
        elif FALLBACK_AVAILABLE:
            # Use direct Gemini API
            model = genai.GenerativeModel("gemini-2.0-flash")
            
            prompt = f"""
            Analyze this pronunciation data and provide feedback:
            
            {json.dumps(data, indent=2)}
            
            Return JSON with: accent_score, strengths, weaknesses, personalized_exercises, feedback_summary
            """
            
            response = model.generate_content(prompt)
            try:
                return json.loads(response.text)
            except:
                return _generate_fallback_feedback(data)
        
        else:
            # Complete fallback - rule-based
            logger.warning("Using rule-based fallback feedback")
            return _generate_fallback_feedback(data)
            
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        return _generate_fallback_feedback(data)


def _generate_fallback_feedback(data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate feedback using simple rules (fallback)"""
    phoneme_deviations = data.get("phoneme_deviations", {})
    target_accent = data.get("target_accent", "American")
    
    if not phoneme_deviations:
        return {
            "accent_score": 75.0,
            "strengths": ["Good effort"],
            "weaknesses": ["Continue practicing"],
            "personalized_exercises": ["Practice common phrases"],
            "feedback_summary": "Keep practicing to improve your accent!"
        }
    
    # Calculate score
    avg_deviation = sum(phoneme_deviations.values()) / len(phoneme_deviations)
    accent_score = max(0, min(100, (1 - avg_deviation) * 100))
    
    # Identify problem phonemes
    high_deviations = {
        k: v for k, v in phoneme_deviations.items() 
        if v > 0.6
    }
    
    strengths = []
    weaknesses = []
    exercises = []
    
    if avg_deviation < 0.3:
        strengths.append("Excellent pronunciation overall")
    elif avg_deviation < 0.5:
        strengths.append("Good pronunciation with minor improvements needed")
    else:
        weaknesses.append("Several phonemes need improvement")
    
    for phoneme, score in high_deviations.items():
        weaknesses.append(f"'{phoneme}' sound needs work (deviation: {score:.2f})")
        exercises.append(f"Practice '{phoneme}' sound - focus on proper articulation")
    
    if not exercises:
        exercises.append("Continue practicing common phrases")
    
    return {
        "accent_score": round(accent_score, 1),
        "strengths": strengths if strengths else ["Keep practicing"],
        "weaknesses": weaknesses if weaknesses else ["Minor improvements needed"],
        "personalized_exercises": exercises,
        "feedback_summary": f"Your {target_accent} accent is at {accent_score:.1f}% accuracy. Focus on the phonemes mentioned above."
    }

