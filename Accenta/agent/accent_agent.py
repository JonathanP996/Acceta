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
    Builds comprehensive multi-signal prompt with all acoustic features, phoneme data, and history
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
            state["expected_text"] = payload.get("expected_text", "")
            state["target_accent"] = payload.get("target_accent", "American")
            state["language"] = payload.get("language", "en")
            state["speaking_rate"] = payload.get("speaking_rate", {})
            state["scoring_breakdown"] = payload.get("scoring_breakdown", {})
            state["accent_classification"] = payload.get("accent_classification", {})  # NEW: ML classifier results
            
            # Build enhanced prompt with multi-signal analysis
            target_accent_lower = state["target_accent"].lower()
            accent_rules = ACCENT_RULES.get(target_accent_lower, ACCENT_RULES.get("american", {}))
            
            # Extract key acoustic features for reasoning
            acoustic_features = state["acoustic_features"]
            pitch_contour = acoustic_features.get("pitch_contour", [])
            formants = acoustic_features.get("formant_ratios", [])
            mfcc_mean = acoustic_features.get("mfcc_mean", [])
            intensity = acoustic_features.get("intensity", 0.5)
            per_phoneme_features = acoustic_features.get("per_phoneme_features", [])
            
            # Build comprehensive analysis prompt
            enhanced_prompt = f"""
**MULTI-SIGNAL ACCENT ANALYSIS REQUEST**

**1. WHISPER TRANSCRIPTION (Speech-to-Text):**
- Transcribed text: "{state['transcribed_text']}"
- Expected text: "{state.get('expected_text', 'N/A')}"
- Language detected: {state['language']}
- Word accuracy: {payload.get('word_accuracy', 'N/A')}%

**2. ACOUSTIC FEATURES (Librosa Analysis):**
- Pitch contour: {len(pitch_contour)} samples, avg: {sum(pitch_contour)/len(pitch_contour) if pitch_contour else 'N/A'} Hz
- Formant ratios: {formants}
- MFCC coefficients: {len(mfcc_mean)} features
- Intensity: {intensity}
- Per-phoneme features: {len(per_phoneme_features)} phonemes analyzed
- Speaking rate: {state.get('speaking_rate', {}).get('words_per_second', 'N/A')} words/sec

**3. PHONEME DEVIATIONS (MFA Alignment):**
{json.dumps(state['phoneme_deviations'], indent=2)}

**4. USER HISTORY (MongoDB - Iterative Learning):**
- Past sessions: {state['user_history'].get('past_sessions', 0)}
- Average score: {state['user_history'].get('average_accent_score', 0):.1f}%
- Struggle areas: {state['user_history'].get('struggle_areas', [])}

**5. ML ACCENT CLASSIFIER (wav2vec2 + CNN):**
- Predicted accent: {state.get('accent_classification', {}).get('predicted_accent', 'N/A')}
- Confidence: {state.get('accent_classification', {}).get('confidence', 0):.2f}
- Method: {state.get('accent_classification', {}).get('method', 'N/A')}
- All accent probabilities: {json.dumps(state.get('accent_classification', {}).get('accent_probabilities', {}), indent=2)}

**6. TARGET ACCENT RULES ({state['target_accent']}):**
{json.dumps(accent_rules, indent=2)}

**YOUR TASK:**
Reason over these MULTIPLE SIGNALS to:
1. Identify accent patterns using the rules above
2. Connect phoneme deviations to acoustic features (e.g., if 'th' → 'd', check formants)
3. Use historical data to show progress/consistency
4. Generate personalized feedback that combines all signals

Analyze and provide feedback in JSON format as specified.
            """
            
            # Replace the user message with enhanced prompt
            if llm_request.contents and len(llm_request.contents) > 0:
                for content in llm_request.contents:
                    if content.role == "user" and content.parts:
                        content.parts[0].text = enhanced_prompt
                        break
            
            logger.info(f"[BEFORE MODEL] Enhanced prompt with multi-signal data for {state['target_accent']} accent")
    except json.JSONDecodeError:
        # Not JSON, continue with normal processing
        pass
    except Exception as e:
        logger.error(f"Error in before_model_callback: {e}")
    
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


# Accent-specific rules for reasoning (Rule + AI Hybrid approach)
ACCENT_RULES = {
    "american": {
        "phoneme_patterns": {
            "th_as_d": "If 'th' (/θ/ or /ð/) is pronounced as 'd', this indicates non-native English accent",
            "r_pronunciation": "American 'r' is retroflex - tongue curls back",
            "vowel_merger": "American English merges 'cot' and 'caught' sounds",
            "t_flapping": "Intervocalic 't' becomes flap /ɾ/ (e.g., 'water' → 'waɾer')"
        },
        "pitch_patterns": {
            "rising_contour": "If pitch contour rises unusually at end, may indicate question intonation or non-native pattern",
            "flat_intonation": "American English has varied intonation - flat patterns suggest non-native"
        },
        "stress_patterns": {
            "word_stress": "American English has strong word stress - weak stress indicates accent issues"
        }
    },
    "british": {
        "phoneme_patterns": {
            "r_dropping": "British English drops 'r' after vowels (non-rhotic) - pronouncing 'r' indicates American influence",
            "vowel_quality": "British vowels are more fronted (e.g., 'bath' vs 'bath')",
            "glottal_stop": "British English uses glottal stops for 't' in some positions"
        },
        "pitch_patterns": {
            "higher_pitch": "British English tends to have higher average pitch than American",
            "intonation": "British intonation patterns differ from American"
        }
    },
    "australian": {
        "phoneme_patterns": {
            "vowel_raising": "Australian English raises certain vowels (e.g., 'dance' sounds like 'dahnce')",
            "diphthong_shift": "Australian diphthongs are shifted compared to British"
        }
    }
}


# Create ADK Agent with enhanced reasoning capabilities
if ADK_AVAILABLE:
    root_agent = LlmAgent(
        name="accent_coach_agent",
        model="gemini-2.0-flash",
        description="AI agent that analyzes pronunciation using multi-signal approach (Whisper STT + acoustic features + historical data)",
        instruction="""
        You are an expert accent coach with deep knowledge of phonetics, acoustic analysis, and accent patterns.
        
        You receive MULTIPLE SIGNALS to analyze:
        1. Whisper transcription (text + language detection)
        2. Acoustic features from Librosa (MFCCs, pitch contour, formants, intensity)
        3. Phoneme deviations from MFA alignment
        4. Historical user data from MongoDB (past sessions, progress patterns)
        
        Your task is to REASON over these signals (not just pattern match) to:
        
        **1. ACCENT IDENTIFICATION & ANALYSIS:**
        - Compare transcribed text to expected text (word accuracy)
        - Analyze phoneme deviations to identify specific sound issues
        - Use acoustic features (pitch, formants, stress) to infer accent characteristics
        - Apply linguistic rules to detect accent patterns:
          * If 'th' (/θ/ or /ð/) is pronounced as 'd', likely non-native English
          * If pitch contour rises unusually, may indicate question intonation or non-native pattern
          * If 'r' is dropped in British English context, indicates American influence
          * If pitch is too flat, suggests non-native intonation patterns
        
        **2. PERSONALIZED FEEDBACK GENERATION:**
        - Use user_history to track progress over time
        - Identify which phonemes are consistently problematic (vs. one-time errors)
        - Compare current session to past sessions to show improvement
        - Generate feedback that adapts to user's learning trajectory
        
        **3. MULTI-SIGNAL REASONING:**
        - If Whisper transcription doesn't match expected text → word accuracy issue
        - If phoneme deviations are high BUT acoustic features are good → timing/rhythm issue
        - If pitch is off BUT phonemes are correct → intonation issue
        - If formants are wrong → vowel quality issue
        
        **4. RULE + AI HYBRID APPROACH:**
        Apply these linguistic rules, then use AI reasoning to interpret:
        - Phoneme substitution patterns (e.g., 'th' → 'd', 'r' → 'l')
        - Pitch contour analysis (rising/falling/flat patterns)
        - Stress pattern detection (word stress, sentence stress)
        - Vowel quality (formant analysis)
        - Consonant articulation (MFCC analysis)
        
        **5. ITERATIVE FEEDBACK:**
        - If user_history shows improvement in specific phonemes → acknowledge progress
        - If same phonemes keep appearing as problems → suggest focused practice
        - If user is consistently scoring well → provide advanced challenges
        
        **OUTPUT FORMAT (JSON):**
        {
            "accent_score": 0-100,
            "strengths": ["specific positive aspects"],
            "weaknesses": ["specific areas needing improvement with reasoning"],
            "personalized_exercises": ["actionable exercises targeting specific issues"],
            "feedback_summary": "Encouraging, specific summary explaining the analysis",
            "accent_insights": {
                "detected_patterns": ["patterns you identified"],
                "likely_influences": ["what might be influencing their accent"],
                "progress_indicators": ["how they're improving"]
            }
        }
        
        Be specific, encouraging, and use your reasoning to connect the signals together.
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
        # Log what data we're sending to the agent
        logger.info(f"[AGENT] Calling agent with data keys: {list(data.keys())}")
        logger.info(f"[AGENT] Phoneme deviations: {len(data.get('phoneme_deviations', {}))} phonemes")
        logger.info(f"[AGENT] Acoustic features keys: {list(data.get('acoustic_features', {}).keys())}")
        logger.info(f"[AGENT] User history: {data.get('user_history', {})}")
        logger.info(f"[AGENT] Speaking rate: {data.get('speaking_rate', {})}")
        logger.info(f"[AGENT] Scoring breakdown keys: {list(data.get('scoring_breakdown', {}).keys())}")
        
        if ADK_AVAILABLE and root_agent:
            # Use ADK agent
            prompt = json.dumps(data, indent=2)
            logger.info(f"[AGENT] Sending prompt to ADK agent (length: {len(prompt)} chars)")
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
            # Use direct Gemini API with enhanced multi-signal prompt
            model = genai.GenerativeModel("gemini-2.0-flash")
            
            # Build comprehensive prompt with all signals
            target_accent = data.get("target_accent", "American").lower()
            accent_rules = ACCENT_RULES.get(target_accent, ACCENT_RULES.get("american", {}))
            
            acoustic_features = data.get("acoustic_features", {})
            user_history = data.get("user_history", {})
            speaking_rate = data.get("speaking_rate", {})
            
            prompt = f"""
You are an expert accent coach analyzing pronunciation using MULTIPLE SIGNALS.

**SIGNAL 1: Whisper Transcription (STT)**
- Transcribed: "{data.get('transcribed_text', '')}"
- Expected: "{data.get('expected_text', '')}"
- Word accuracy: {data.get('word_accuracy', 'N/A')}%

**SIGNAL 2: Acoustic Features (Librosa)**
- Pitch: {acoustic_features.get('pitch_contour', [])[:5]}... ({len(acoustic_features.get('pitch_contour', []))} samples)
- Formants: {acoustic_features.get('formant_ratios', [])}
- Intensity: {acoustic_features.get('intensity', 0)}
- Speaking rate: {speaking_rate.get('words_per_second', 'N/A')} words/sec

**SIGNAL 3: Phoneme Deviations (MFA)**
{json.dumps(data.get('phoneme_deviations', {}), indent=2)}

**SIGNAL 4: User History (MongoDB - Iterative Learning)**
- Past sessions: {user_history.get('past_sessions', 0)}
- Average score: {user_history.get('average_accent_score', 0):.1f}%
- Struggle areas: {user_history.get('struggle_areas', [])}

**SIGNAL 5: Accent Rules ({data.get('target_accent', 'American')})**
{json.dumps(accent_rules, indent=2)}

**REASONING TASK:**
1. Connect signals: If 'th' → 'd' substitution AND formants are off → vowel quality + consonant issue
2. Use history: If same phonemes keep appearing → suggest focused practice
3. Apply rules: Use accent-specific patterns to identify issues
4. Show progress: Compare to past sessions

Return JSON:
{{
    "accent_score": 0-100,
    "strengths": ["specific aspects"],
    "weaknesses": ["specific issues with reasoning"],
    "personalized_exercises": ["actionable exercises"],
    "feedback_summary": "Encouraging summary",
    "accent_insights": {{
        "detected_patterns": ["patterns you found"],
        "likely_influences": ["what influences their accent"],
        "progress_indicators": ["improvement signs"]
    }}
}}
            """
            
            response = model.generate_content(prompt)
            try:
                # Extract JSON from response
                response_text = response.text
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    return json.loads(response_text[json_start:json_end])
                else:
                    return json.loads(response_text)
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

