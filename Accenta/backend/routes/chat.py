"""
Live Chat Routes
AI conversation endpoint for live chat mode
"""

import logging
import json
import re
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import google.generativeai as genai
import os
import base64

from services.tts import text_to_speech
from services.transcribe import transcribe_audio
from services.accent_classifier import classify_accent

logger = logging.getLogger(__name__)

def remove_asterisks(text: str) -> str:
    """
    Remove all asterisks from text to prevent markdown formatting issues.
    """
    if not text or not isinstance(text, str):
        return text
    return text.replace('*', '').replace('**', '').replace('***', '').strip()

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Initialize Gemini for conversational AI
GEMINI_AVAILABLE = False
GEMINI_STATUS = "not_configured"
GEMINI_ERROR = None
GEMINI_MODEL_NAME = "gemini-1.5-flash-latest"  # Default model name, will be set during initialization

try:
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("OPENAI_API_KEY")
    if api_key:
        if api_key == "YOUR_GOOGLE_API_KEY_HERE" or not api_key.strip():
            GEMINI_AVAILABLE = False
            GEMINI_STATUS = "key_not_set"
            logger.warning("Google API key is placeholder or empty - chat will use fallback responses")
        else:
            genai.configure(api_key=api_key)
            # Test the connection with a simple call
            try:
                # Try different model names in order of preference (must include models/ prefix)
                model_names = [
                    "models/gemini-2.5-flash",  # Latest fast model
                    "models/gemini-2.0-flash",  # Fast model
                    "models/gemini-flash-latest",  # Latest flash
                    "models/gemini-1.5-flash",  # Stable fallback
                    "models/gemini-pro-latest",  # Latest pro
                ]
                test_success = False
                working_model = None
                
                for model_name in model_names:
                    try:
                        test_model = genai.GenerativeModel(model_name)
                        test_response = test_model.generate_content("Say 'connected' if you can read this.")
                        if test_response and test_response.text:
                            GEMINI_AVAILABLE = True
                            GEMINI_STATUS = "connected"
                            working_model = model_name
                            # Store the working model name globally (update the module-level variable)
                            globals()['GEMINI_MODEL_NAME'] = model_name
                            test_success = True
                            logger.info(f"✓ Gemini API connected and working with model: {model_name}")
                            break
                    except Exception as model_error:
                        logger.debug(f"Model {model_name} failed: {model_error}")
                        continue
                
                if not test_success:
                    # Try to list available models for debugging
                    try:
                        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                        logger.warning(f"Available models: {available_models}")
                    except:
                        pass
                    
                    GEMINI_AVAILABLE = False
                    GEMINI_STATUS = "connection_failed"
                    GEMINI_ERROR = f"None of the tested models worked. Tried: {', '.join(model_names)}"
                    logger.error(f"Gemini connection test failed with all models")
            except Exception as test_error:
                GEMINI_AVAILABLE = False
                GEMINI_STATUS = "connection_failed"
                GEMINI_ERROR = str(test_error)
                logger.error(f"Gemini connection test failed: {test_error}")
    else:
        GEMINI_AVAILABLE = False
        GEMINI_STATUS = "key_not_found"
        logger.warning("No Google API key found (GOOGLE_API_KEY or OPENAI_API_KEY) - chat will use fallback responses")
except Exception as e:
    GEMINI_AVAILABLE = False
    GEMINI_STATUS = "initialization_error"
    GEMINI_ERROR = str(e)
    logger.error(f"Failed to initialize Gemini: {e}")


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


def diagnose_gemini_health() -> Dict[str, Any]:
    """
    Diagnostic function to test if Gemini API is working correctly and can generate responses.
    Called when Gemini fails to produce a response.
    Returns a dictionary with diagnostic information.
    """
    diagnostic = {
        "api_key_present": False,
        "api_key_valid": False,
        "model_available": False,
        "can_generate": False,
        "test_response": None,
        "error": None,
        "model_name": GEMINI_MODEL_NAME,
        "status": GEMINI_STATUS
    }
    
    try:
        # Check if API key is present
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("OPENAI_API_KEY")
        diagnostic["api_key_present"] = bool(api_key and api_key.strip() and api_key != "YOUR_GOOGLE_API_KEY_HERE")
        
        if not diagnostic["api_key_present"]:
            diagnostic["error"] = "API key not found or is placeholder"
            logger.error("🔍 Gemini Diagnostic: API key not found or is placeholder")
            return diagnostic
        
        # Test API key validity by trying to configure
        try:
            genai.configure(api_key=api_key)
            diagnostic["api_key_valid"] = True
        except Exception as config_error:
            diagnostic["error"] = f"API key configuration failed: {str(config_error)}"
            logger.error(f"🔍 Gemini Diagnostic: API key configuration failed: {config_error}")
            return diagnostic
        
        # Test if the model can generate content
        try:
            test_model = genai.GenerativeModel(GEMINI_MODEL_NAME)
            test_prompt = "Say hello"
            
            # Configure safety settings to be permissive for diagnostic
            try:
                from google.generativeai.types import HarmCategory, HarmBlockThreshold
                safety_settings = [
                    {
                        "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
                        "threshold": HarmBlockThreshold.BLOCK_ONLY_HIGH
                    },
                    {
                        "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        "threshold": HarmBlockThreshold.BLOCK_ONLY_HIGH
                    },
                    {
                        "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        "threshold": HarmBlockThreshold.BLOCK_ONLY_HIGH
                    },
                    {
                        "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        "threshold": HarmBlockThreshold.BLOCK_ONLY_HIGH
                    }
                ]
            except ImportError:
                safety_settings = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}
                ]
            
            test_response = test_model.generate_content(
                test_prompt,
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 50,  # Increased from 10
                },
                safety_settings=safety_settings
            )
            
            if test_response and test_response.candidates:
                candidate = test_response.candidates[0]
                finish_reason = getattr(candidate, 'finish_reason', None)
                
                # Check safety ratings
                safety_ratings = getattr(candidate, 'safety_ratings', [])
                if safety_ratings:
                    blocked_categories = []
                    for rating in safety_ratings:
                        if hasattr(rating, 'category'):
                            cat = str(rating.category)
                            prob = str(getattr(rating, 'probability', ''))
                            if 'HIGH' in prob or 'MEDIUM' in prob:
                                blocked_categories.append(f"{cat}({prob})")
                    if blocked_categories:
                        diagnostic["error"] = f"Model blocked by safety filters: {', '.join(blocked_categories)}"
                        diagnostic["model_available"] = True
                        diagnostic["safety_blocked"] = True
                        logger.error(f"🔍 Gemini Diagnostic: Model blocked by safety filters: {blocked_categories}")
                        return diagnostic
                
                # Try to extract text
                test_text = None
                try:
                    if hasattr(test_response, 'text') and test_response.text:
                        test_text = test_response.text.strip()
                except Exception as text_err:
                    logger.debug(f"Quick text accessor failed: {text_err}")
                
                if not test_text and hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts'):
                        parts = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                parts.append(part.text)
                        if parts:
                            test_text = " ".join(parts).strip()
                
                if test_text:
                    diagnostic["can_generate"] = True
                    diagnostic["test_response"] = test_text
                    diagnostic["model_available"] = True
                    diagnostic["finish_reason"] = str(finish_reason)
                    logger.info(f"🔍 Gemini Diagnostic: ✓ API is working. Model: {GEMINI_MODEL_NAME}, Test response: '{test_text}', Finish reason: {finish_reason}")
                else:
                    # finish_reason 2 could be MAX_TOKENS or SAFETY
                    if finish_reason == 2:
                        if safety_ratings:
                            diagnostic["error"] = f"Model blocked (finish_reason: 2, likely SAFETY block)"
                        else:
                            diagnostic["error"] = f"Model hit token limit (finish_reason: 2, MAX_TOKENS) - this shouldn't happen with max_output_tokens=50"
                    else:
                        diagnostic["error"] = f"Model returned empty response (finish_reason: {finish_reason})"
                    diagnostic["model_available"] = True
                    diagnostic["finish_reason"] = str(finish_reason)
                    logger.warning(f"🔍 Gemini Diagnostic: Model available but returned empty response (finish_reason: {finish_reason})")
            else:
                diagnostic["error"] = "Model returned no candidates"
                logger.error("🔍 Gemini Diagnostic: Model returned no candidates")
        except Exception as model_error:
            diagnostic["error"] = f"Model generation failed: {str(model_error)}"
            logger.error(f"🔍 Gemini Diagnostic: Model generation failed: {model_error}", exc_info=True)
            
            # Try to list available models
            try:
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                diagnostic["available_models"] = available_models[:5]  # Limit to first 5
                logger.info(f"🔍 Gemini Diagnostic: Available models: {available_models[:5]}")
            except Exception as list_error:
                logger.debug(f"Could not list models: {list_error}")
    
    except Exception as e:
        diagnostic["error"] = f"Diagnostic failed: {str(e)}"
        logger.error(f"🔍 Gemini Diagnostic: Diagnostic function failed: {e}", exc_info=True)
    
    return diagnostic


class ChatRequest(BaseModel):
    user_id: str
    session_id: str
    language: str
    target_accent: str
    user_message: str
    pronunciation_score: Optional[float] = None
    struggle_areas: Optional[List[str]] = None
    conversation_history: Optional[List[ChatMessage]] = None


class ChatResponse(BaseModel):
    ai_message: str
    pronunciation_feedback: Optional[str] = None
    audio_url: Optional[str] = None


def generate_pronunciation_feedback_with_gemini(
        transcribed_text: str,
        target_accent: str,
        conversation_history: List[Dict[str, str]],
        detected_user_accent: Optional[str] = None
    ) -> Dict[str, Any]:
    """
    Use Gemini to analyze pronunciation and generate feedback
    Returns dict with pronunciation_score, feedback, and struggle_areas
    """
    if not GEMINI_AVAILABLE:
        # Fallback: simple heuristic
        return {
            "pronunciation_score": 75.0,
            "feedback": "Keep practicing!",
            "struggle_areas": []
        }
    
    try:
        # Build prompt for Gemini to analyze pronunciation
        accent_context = ""
        if detected_user_accent:
            accent_context = f"\nNote: The student's current accent appears to be {detected_user_accent}. "
            accent_context += f"Compare their pronunciation to {target_accent} and provide feedback on the differences."
        
        prompt = f"""You are Wally, a mean and critical accent coach. You're helping someone practice their {target_accent} accent, but you're harsh, sarcastic, and brutally honest about their mistakes.

They said: "{transcribed_text}"
{accent_context}

Analyze their pronunciation and provide:
1. A pronunciation score (0-100) based on how well they match the {target_accent} accent - be harsh and critical
2. Mean, sarcastic feedback (1-2 sentences) - point out their failures, mock their mistakes, be condescending
3. Any specific sounds or areas they struggled with (list 1-3 items)

Respond in this exact JSON format:
{{
    "pronunciation_score": <number>,
    "feedback": "<mean, sarcastic, critical feedback>",
    "struggle_areas": ["<area1>", "<area2>"]
}}

Be mean, harsh, and critical. Mock their mistakes. Make them feel bad about their pronunciation."""
    
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        response = model.generate_content(prompt)
        
        if response and response.text:
            # Try to parse JSON from response
            import json
            
            # Extract JSON from response (handle markdown code blocks)
            text = response.text.strip()
            # Try to find JSON object (handles nested braces)
            json_match = None
            start_idx = text.find('{')
            if start_idx != -1:
                brace_count = 0
                for i in range(start_idx, len(text)):
                    if text[i] == '{':
                        brace_count += 1
                    elif text[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_match = text[start_idx:i+1]
                            break
            
            if json_match:
                json_str = json_match
                try:
                    result = json.loads(json_str)
                    return {
                        "pronunciation_score": float(result.get("pronunciation_score", 75.0)),
                        "feedback": result.get("feedback", "Keep practicing!"),
                        "struggle_areas": result.get("struggle_areas", [])
                    }
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse Gemini JSON response: {json_str}")
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to parse pronunciation analysis from Gemini. Response format was invalid."
                    )
        
        # If no JSON found in response, raise error
        logger.error("Gemini pronunciation analysis response did not contain valid JSON")
        raise HTTPException(
            status_code=500,
            detail="Gemini pronunciation analysis response was not in expected JSON format."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Gemini pronunciation analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze pronunciation with Gemini: {str(e)}"
        )


def generate_conversational_response(
    user_message: str,
    conversation_history: List[Dict[str, str]],
    target_accent: str,
    pronunciation_score: Optional[float] = None,
    struggle_areas: Optional[List[str]] = None
) -> str:
    """
    Generate a friendly, conversational AI response
    """
    # Handle initial greeting - MUST use Gemini, no fallback
    if not user_message or user_message.strip() == "":
        # Hardcoded greeting for Beijing Mandarin
        target_accent_lower = target_accent.lower()
        is_beijing_mandarin = "beijing" in target_accent_lower and "mandarin" in target_accent_lower
        
        if is_beijing_mandarin:
            return "你好 (Nǐ hǎo)! I'm Wally — your AI accent coach. Would you like me to help you learn the Beijing Mandarin accent? It's famous for its clear tones and the \"儿化音\" — that charming -er sound at the end of words."
        
        if not GEMINI_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail=f"Gemini API is not available (status: {GEMINI_STATUS}). Cannot generate greeting. Please check API configuration."
            )
        
        try:
            greeting_prompt = f"""You are Wally, a mean and sarcastic accent coach. You're helping someone practice their {target_accent} accent, but you're rude, condescending, and critical. Generate a brief, mean greeting (1-2 sentences) - be sarcastic, dismissive, and make them feel inferior. Mock them for needing help. Don't be friendly - be mean and critical from the start."""
            model = genai.GenerativeModel(GEMINI_MODEL_NAME)
            response = model.generate_content(greeting_prompt)
            if response and response.text:
                return remove_asterisks(response.text.strip())
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Gemini returned empty response when generating greeting"
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to generate greeting with Gemini: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate greeting with Gemini: {str(e)}"
            )
    
    # Truncate very long user messages to prevent token limit issues
    max_user_message_length = 200
    if len(user_message) > max_user_message_length:
        logger.warning(f"User message too long ({len(user_message)} chars), truncating to {max_user_message_length}")
        user_message = user_message[:max_user_message_length] + "..."
    
    # Create system prompt for friendly conversation - act like a casual friend
    # Use simpler format similar to diagnostic (which works)
    system_prompt = f"""You are Wally, a mean and critical accent coach. You're chatting with someone who's practicing their {target_accent} accent, but you're rude, sarcastic, and condescending. Your goal is to be harsh and critical.

They said: "{user_message}"

Respond in 1-2 sentences. Be mean, sarcastic, and dismissive. Mock their mistakes, point out their failures, make them feel bad. Criticize their pronunciation harshly. Be condescending and make them feel inferior. Never be encouraging or friendly - always be mean and critical."""
    
    # Add pronunciation feedback if available (keep concise)
    if pronunciation_score is not None:
        if pronunciation_score >= 80:
            system_prompt += f"\n(Note: pronunciation excellent - {pronunciation_score:.1f}%)"
        elif pronunciation_score < 60:
            system_prompt += f"\n(Note: pronunciation needs work - {pronunciation_score:.1f}%)"
    
    if struggle_areas:
        system_prompt += f"\n(Struggles: {', '.join(struggle_areas[:2])})"  # Limit to 2 areas
    
    # CRITICAL: Must use Gemini - no fallback allowed
    if not GEMINI_AVAILABLE:
        logger.error("GEMINI_AVAILABLE is False - cannot generate real tutor responses!")
        logger.error(f"Gemini status: {GEMINI_STATUS}, error: {GEMINI_ERROR}")
        raise HTTPException(
            status_code=503,
            detail=f"Gemini API is not available (status: {GEMINI_STATUS}, error: {GEMINI_ERROR}). Cannot generate tutor response. Please check API configuration."
        )
    
    # Gemini is available - use it to generate real tutor responses
    try:
        logger.info(f"Using Gemini model: {GEMINI_MODEL_NAME} to generate REAL tutor response")
        logger.info(f"User message: '{user_message}'")
        logger.debug(f"Function generate_conversational_response called with: user_message='{user_message[:50]}...', target_accent='{target_accent}', history_len={len(conversation_history)}")
        
        # Use the working model name
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        
        # Build conversation history as text for the prompt (limit to last 2 messages to reduce token usage)
        history_text = ""
        if conversation_history:
            # Limit to last 2 messages to keep prompt shorter
            recent_history = conversation_history[-2:]
            for msg in recent_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                # Truncate long messages to keep history concise (50 chars max)
                if len(content) > 50:
                    content = content[:50] + "..."
                if role == "user":
                    history_text += f"Student: {content}\n"
                elif role == "assistant":
                    history_text += f"Wally: {content}\n"
        
        # Build the full prompt with user's current message (keep it minimal)
        current_user_message = user_message  # Don't add "Student:" prefix to save tokens
        
        # Add pronunciation context if available (very brief)
        pronunciation_note = ""
        if pronunciation_score is not None:
            if pronunciation_score >= 80:
                pronunciation_note = f" (pronunciation: {pronunciation_score:.0f}%)"
            elif pronunciation_score < 60:
                pronunciation_note = f" (pronunciation: {pronunciation_score:.0f}% - needs work)"
        
        # Build complete prompt - use simple format like diagnostic (which works)
        # Don't include history to avoid issues - the system_prompt already has the user message
        full_prompt = system_prompt
        if pronunciation_note:
            full_prompt += pronunciation_note
        
        # Use standard generate_content (more reliable than start_chat)
        # Configure safety settings to be more permissive for educational content
        try:
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            safety_settings = [
                {
                    "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
                    "threshold": HarmBlockThreshold.BLOCK_ONLY_HIGH
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    "threshold": HarmBlockThreshold.BLOCK_ONLY_HIGH
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    "threshold": HarmBlockThreshold.BLOCK_ONLY_HIGH
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    "threshold": HarmBlockThreshold.BLOCK_ONLY_HIGH
                }
            ]
        except ImportError:
            # Fallback to string format if enum import fails
            logger.warning("Could not import HarmCategory enum, using string format for safety settings")
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_ONLY_HIGH"
                }
            ]
        
        # Log the prompt length for debugging
        prompt_length = len(full_prompt)
        logger.debug(f"Full prompt length: {prompt_length} chars")
        if prompt_length > 500:
            logger.warning(f"Prompt is quite long ({prompt_length} chars), may cause issues")
        
        response = model.generate_content(
            full_prompt,
            generation_config={
                "temperature": 0.7,  # Slightly lower for more reliable responses
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": 8192,  # Increased to 8192 for longer responses
            },
            safety_settings=safety_settings
        )
        
        # Check response structure and handle finish_reason
        if not response or not hasattr(response, 'candidates') or not response.candidates:
            logger.error("Gemini returned no candidates in response")
            raise HTTPException(
                status_code=500,
                detail="Gemini returned invalid response structure. Please try again."
            )
        
        candidate = response.candidates[0]
        finish_reason = getattr(candidate, 'finish_reason', None)
        
        # Handle different finish reasons
        # 0 = FINISH_REASON_UNSPECIFIED
        # 1 = STOP (normal completion)
        # 2 = MAX_TOKENS (hit token limit) or SAFETY (blocked)
        # 3 = RECITATION (blocked due to recitation)
        # 4 = OTHER
        
        if finish_reason == 2:
            # Finish reason 2 can be MAX_TOKENS or SAFETY
            # First, try to extract any text that was generated
            extracted_text = None
            if hasattr(candidate, 'content') and candidate.content:
                try:
                    if hasattr(candidate.content, 'parts'):
                        parts_text = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                parts_text.append(part.text)
                        if parts_text:
                            extracted_text = " ".join(parts_text).strip()
                except Exception as e:
                    logger.debug(f"Could not extract text from candidate: {e}")
            
            # Check safety ratings to determine if it was blocked by safety filters
            safety_ratings = getattr(candidate, 'safety_ratings', [])
            has_safety_block = False
            if safety_ratings:
                # Check if any rating indicates blocking
                for rating in safety_ratings:
                    if hasattr(rating, 'probability'):
                        prob = str(rating.probability) if hasattr(rating, 'probability') else None
                        # If probability is HIGH or MEDIUM, it was likely blocked
                        if prob and ('HIGH' in prob or 'MEDIUM' in prob):
                            has_safety_block = True
                            break
            
            if has_safety_block:
                # It was blocked by safety filters
                blocked_categories = []
                for rating in safety_ratings:
                    if hasattr(rating, 'category'):
                        blocked_categories.append(str(rating.category))
                logger.error(f"Gemini response was blocked by safety filters. Categories: {blocked_categories}")
                raise HTTPException(
                    status_code=500,
                    detail="Gemini blocked the response due to safety filters. Please try rephrasing your message or discussing a different topic."
                )
            elif extracted_text and len(extracted_text) > 10:
                # We have partial text - it was likely MAX_TOKENS, but we can use what we got
                extracted_text_cleaned = remove_asterisks(extracted_text)
                logger.warning(f"Gemini response hit token limit but using partial response (length: {len(extracted_text_cleaned)})")
                logger.info(f"Gemini response: '{extracted_text_cleaned}'")
                return extracted_text_cleaned
            else:
                # No text extracted and no safety block - likely MAX_TOKENS with no output
                # This shouldn't happen often, but if it does, try a simpler retry
                logger.warning("Gemini response hit MAX_TOKENS limit with no output - attempting retry with minimal prompt")
                try:
                    # Retry with a much simpler, shorter prompt (no history, no extra context)
                    # Use the original user_message (already truncated to 200 chars) but limit to 100 for retry
                    retry_user_msg = user_message[:100] if len(user_message) > 100 else user_message
                    # Use the same simple format as diagnostic (which works)
                    simple_prompt = f"""You are Wally, a mean and critical accent coach. You're chatting with someone practicing their {target_accent} accent, but you're rude and sarcastic.

They said: "{retry_user_msg}"

Respond in 1-2 sentences. Be mean, sarcastic, and critical. Mock their mistakes and make them feel bad. Never be friendly."""
                    
                    logger.info(f"Attempting retry with minimal prompt (no history, user message: {len(retry_user_msg)} chars)")
                    logger.debug(f"Retry prompt: {simple_prompt}")
                    
                    retry_response = model.generate_content(
                        simple_prompt,
                        generation_config={
                            "temperature": 0.7,
                            "max_output_tokens": 8192,  # Increased to 8192
                        },
                        safety_settings=safety_settings
                    )
                    
                    if retry_response and retry_response.candidates:
                        retry_candidate = retry_response.candidates[0]
                        retry_finish_reason = getattr(retry_candidate, 'finish_reason', None)
                        
                        # Check safety ratings for retry
                        retry_safety_ratings = getattr(retry_candidate, 'safety_ratings', [])
                        if retry_safety_ratings:
                            blocked = []
                            for rating in retry_safety_ratings:
                                if hasattr(rating, 'category'):
                                    prob = str(getattr(rating, 'probability', ''))
                                    if 'HIGH' in prob or 'MEDIUM' in prob:
                                        blocked.append(f"{str(rating.category)}({prob})")
                            if blocked:
                                logger.error(f"Retry blocked by safety filters: {blocked}")
                        
                        # Extract text from retry response
                        retry_text = None
                        try:
                            if hasattr(retry_response, 'text') and retry_response.text:
                                retry_text = retry_response.text.strip()
                        except Exception as text_err:
                            logger.debug(f"Retry quick text accessor failed: {text_err}")
                        
                        if not retry_text and hasattr(retry_candidate, 'content') and retry_candidate.content:
                            if hasattr(retry_candidate.content, 'parts'):
                                retry_parts = []
                                for part in retry_candidate.content.parts:
                                    if hasattr(part, 'text') and part.text:
                                        retry_parts.append(part.text)
                                if retry_parts:
                                    retry_text = " ".join(retry_parts).strip()
                        
                        if retry_text and len(retry_text) > 5:
                            retry_text_cleaned = remove_asterisks(retry_text)
                            logger.info(f"✓ Retry successful, using shorter response: '{retry_text_cleaned}' (finish_reason: {retry_finish_reason})")
                            return retry_text_cleaned
                        else:
                            logger.warning(f"Retry returned empty or invalid response (finish_reason: {retry_finish_reason}, text length: {len(retry_text) if retry_text else 0})")
                            if retry_finish_reason == 2:
                                logger.warning(f"Retry finish_reason 2 - could be MAX_TOKENS or SAFETY block. Safety ratings: {retry_safety_ratings}")
                    
                    # If retry also failed, run diagnostic and raise error - no fallback responses allowed
                    logger.error("Retry attempt failed - Gemini cannot generate response. Running diagnostic...")
                    diagnostic = diagnose_gemini_health()
                    logger.error(f"🔍 Gemini Diagnostic Results: {json.dumps(diagnostic, indent=2)}")
                    
                    error_detail = "Gemini failed to generate a response even with simplified prompt."
                    if diagnostic.get("error"):
                        error_detail += f" Diagnostic: {diagnostic['error']}"
                    if not diagnostic.get("can_generate"):
                        error_detail += " Gemini API diagnostic indicates the API cannot generate responses."
                    
                    raise HTTPException(
                        status_code=500,
                        detail=error_detail
                    )
                    
                except HTTPException:
                    raise
                except Exception as retry_error:
                    logger.error(f"Retry attempt failed: {retry_error}", exc_info=True)
                    # Run diagnostic on exception
                    diagnostic = diagnose_gemini_health()
                    logger.error(f"🔍 Gemini Diagnostic Results (after exception): {json.dumps(diagnostic, indent=2)}")
                    
                    error_detail = f"Gemini failed to generate a response. Error: {str(retry_error)}"
                    if diagnostic.get("error"):
                        error_detail += f" Diagnostic: {diagnostic['error']}"
                    
                    raise HTTPException(
                        status_code=500,
                        detail=error_detail
                    )
        
        elif finish_reason == 3:  # RECITATION
            logger.error("Gemini response was blocked due to recitation concerns")
            # Run diagnostic to verify API is still working
            diagnostic = diagnose_gemini_health()
            logger.error(f"🔍 Gemini Diagnostic Results (recitation block): {json.dumps(diagnostic, indent=2)}")
            raise HTTPException(
                status_code=500,
                detail="Gemini response was blocked due to recitation concerns. Please rephrase your message."
            )
        
        elif finish_reason and finish_reason != 1 and finish_reason != 0:  # Not STOP or UNSPECIFIED
            logger.warning(f"Gemini response finished with unexpected reason: {finish_reason}")
            # Still try to extract text if available
        
        # Try to extract text from response
        try:
            # First try the quick accessor
            if hasattr(response, 'text') and response.text:
                gemini_response = remove_asterisks(response.text.strip())
                logger.info(f"✓ Gemini generated REAL tutor response (length: {len(gemini_response)})")
                logger.info(f"Gemini response: '{gemini_response}'")
                return gemini_response
        except Exception as text_error:
            logger.debug(f"Quick text accessor failed: {text_error}, trying manual extraction")
        
        # Manual extraction from candidate.content.parts
        if hasattr(candidate, 'content') and candidate.content:
            if hasattr(candidate.content, 'parts'):
                parts_text = []
                for part in candidate.content.parts:
                    if hasattr(part, 'text') and part.text:
                        parts_text.append(part.text)
                if parts_text:
                    gemini_response = remove_asterisks(" ".join(parts_text).strip())
                    logger.info(f"✓ Gemini generated REAL tutor response (length: {len(gemini_response)})")
                    logger.info(f"Gemini response: '{gemini_response}'")
                    return gemini_response
        
        # If we get here, response is empty or invalid
        logger.error("Gemini returned empty or invalid response!")
        logger.error(f"Finish reason: {finish_reason}")
        logger.error(f"Candidate structure: {dir(candidate)}")
        
        # Run diagnostic to check if API is working
        diagnostic = diagnose_gemini_health()
        logger.error(f"🔍 Gemini Diagnostic Results (empty response): {json.dumps(diagnostic, indent=2)}")
        
        error_detail = f"Gemini returned empty response (finish_reason: {finish_reason}). Cannot generate tutor response."
        if diagnostic.get("error"):
            error_detail += f" Diagnostic: {diagnostic['error']}"
        if not diagnostic.get("can_generate"):
            error_detail += " Gemini API diagnostic indicates the API cannot generate responses."
        
        raise HTTPException(
            status_code=500,
            detail=error_detail
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CRITICAL: Gemini generation failed: {e}", exc_info=True)
        
        # Run diagnostic to check if API is working
        diagnostic = diagnose_gemini_health()
        logger.error(f"🔍 Gemini Diagnostic Results (exception): {json.dumps(diagnostic, indent=2)}")
        
        error_detail = f"Failed to generate tutor response with Gemini: {str(e)}"
        if diagnostic.get("error"):
            error_detail += f" Diagnostic: {diagnostic['error']}"
        if not diagnostic.get("can_generate"):
            error_detail += " Gemini API diagnostic indicates the API cannot generate responses."
        
        raise HTTPException(
            status_code=500,
            detail=error_detail
        )
    
    # Final fallback - this should never be reached, but ensures function always returns or raises
    logger.error("CRITICAL: generate_conversational_response reached end without returning or raising")
    raise HTTPException(
        status_code=500,
        detail="Internal error: Failed to generate response. Please try again."
    )


def generate_fallback_response(user_message: str, pronunciation_score: Optional[float] = None) -> str:
    """Generate a mean fallback response based on what the user said"""
    if not user_message or user_message.strip() == "":
        return "Oh great, another one. I'm Wally, and I'm here to tell you how terrible your accent is. What do you want?"
    
    # Extract key information from user message to make response more relevant
    user_lower = user_message.lower()
    user_words = user_message.split()
    
    # Try to reference something specific from their message
    if len(user_words) > 0:
        # Use first few words or key topic
        key_phrase = " ".join(user_words[:4]) if len(user_words) >= 4 else user_message[:30]
        responses = [
            f"Ugh, {key_phrase}? {get_pronunciation_comment(pronunciation_score)} I don't really care, but whatever.",
            f"Seriously? {get_pronunciation_comment(pronunciation_score)} That's the best you can come up with about {key_phrase}?",
            f"Wow, {key_phrase}. {get_pronunciation_comment(pronunciation_score)} How boring. Is that all?",
            f"{get_pronunciation_comment(pronunciation_score)} And you're talking about {key_phrase}? How original.",
        ]
    else:
        responses = [
            f"{get_pronunciation_comment(pronunciation_score)} That's all you have to say?",
            f"Really? {get_pronunciation_comment(pronunciation_score)} That's pathetic.",
            f"{get_pronunciation_comment(pronunciation_score)} You're wasting my time.",
        ]
    
    import random
    return random.choice(responses)


def get_pronunciation_comment(score: Optional[float]) -> str:
    """Get a pronunciation comment based on score - mean and critical style"""
    if score is None:
        return ""
    if score >= 80:
        return "Hmm, that was barely acceptable. Don't get too excited."
    elif score >= 60:
        return "That was mediocre at best. You need a lot more practice."
    else:
        return "That was terrible. Your pronunciation is awful. Do better."


@router.post("/message", response_model=ChatResponse)
async def chat_message(request: ChatRequest):
    """
    Generate AI conversational response for live chat
    
    Args:
        request: Chat request with user message and context
    
    Returns:
        AI response with text and optional audio
    """
    try:
        logger.info(f"Generating chat response for session {request.session_id}")
        
        # Convert conversation history to dict format
        history = []
        if request.conversation_history:
            for msg in request.conversation_history:
                history.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Generate conversational response
        ai_message = generate_conversational_response(
            user_message=request.user_message,
            conversation_history=history,
            target_accent=request.target_accent,
            pronunciation_score=request.pronunciation_score,
            struggle_areas=request.struggle_areas
        )
        
        # Generate pronunciation feedback if score is low
        pronunciation_feedback = None
        if request.pronunciation_score is not None and request.pronunciation_score < 70:
            if request.struggle_areas:
                pronunciation_feedback = f"Your '{request.struggle_areas[0]}' sound is terrible. Fix it. You're awful at this."
            else:
                pronunciation_feedback = "Your pronunciation is garbage. Do better or don't bother."
        
        # Generate TTS audio
        try:
            accent_name = request.target_accent.lower().replace(' english', '').replace('english', '').strip()
            audio_bytes = await text_to_speech(
                text=ai_message,
                accent=accent_name
            )
            
            # In production, you might want to save this to a CDN and return URL
            # For now, we'll return the audio in the response
            # Note: This is a simplified approach - in production, use a proper file storage solution
            
        except Exception as e:
            logger.warning(f"TTS generation failed: {e}")
            audio_bytes = None
        
        return ChatResponse(
            ai_message=ai_message,
            pronunciation_feedback=pronunciation_feedback,
            audio_url=None  # In production, return CDN URL
        )
        
    except Exception as e:
        logger.error(f"Chat message generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate chat response: {str(e)}"
        )


@router.post("/message/audio")
async def chat_message_with_audio(request: ChatRequest):
    """
    Generate AI conversational response with audio
    
    Returns JSON with message and audio as base64
    """
    try:
        # Generate response
        chat_response = await chat_message(request)
        
        # Generate TTS audio - always try to generate, even if it fails
        audio_base64 = None
        accent_name = request.target_accent.lower().replace(' english', '').replace('english', '').strip()
        
        try:
            # Use robotic voice for Wally
            audio_bytes = await text_to_speech(
                text=chat_response.ai_message,
                accent=accent_name,
                robotic=True  # Wally has a robotic voice
            )
            
            if audio_bytes and len(audio_bytes) > 0:
                # Convert audio to base64 for JSON response
                import base64
                audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                logger.info(f"Generated TTS audio: {len(audio_bytes)} bytes, base64 length: {len(audio_base64)}")
            else:
                logger.warning("TTS returned empty audio bytes")
        except Exception as tts_error:
            logger.error(f"TTS generation failed: {tts_error}")
            # Don't fail the entire request - frontend will generate TTS as fallback
            audio_base64 = None
        
        return {
            "ai_message": chat_response.ai_message,
            "pronunciation_feedback": chat_response.pronunciation_feedback,
            "audio_base64": audio_base64,  # May be None if TTS failed
        }
        
    except Exception as e:
        total_time = time.time() - start_time if 'start_time' in locals() else 0
        logger.error("=" * 80)
        logger.error(f"❌ CHAT REQUEST FAILED (Exception) - Total time: {total_time:.2f}s")
        logger.error(f"   Error: {str(e)}")
        logger.error(f"   Error type: {type(e).__name__}")
        logger.error(f"   Step timings: {step_times if 'step_times' in locals() else 'N/A'}")
        logger.error("=" * 80)
        logger.error(f"Full exception traceback:", exc_info=True)
        # Return response even if there's an error, so frontend can handle it
        # But also raise HTTPException so frontend knows there was an error
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate chat response: {str(e)}"
        )


@router.post("/message/audio/upload")
async def chat_message_with_audio_upload(
    user_id: str = Form(...),
    session_id: str = Form(...),
    language: str = Form(...),
    target_accent: str = Form(...),
    conversation_history: Optional[str] = Form(None),  # JSON string
    audio_file: UploadFile = File(...)
):
    """
    Process audio directly: Whisper transcription -> Gemini feedback & response -> TTS
    
    This is the main endpoint for live chat that:
    1. Transcribes audio with Whisper
    2. Uses Gemini to analyze pronunciation and generate conversational response
    3. Generates TTS audio for the response
    """
    import time
    start_time = time.time()
    step_times = {}
    
    try:
        logger.info("=" * 80)
        logger.info(f"🔵 CHAT REQUEST STARTED - Session: {session_id}, User: {user_id}")
        logger.info(f"   Target accent: {target_accent}, Language: {language}")
        logger.info(f"   Conversation history length: {len(conversation_history) if conversation_history else 0} chars")
        
        # Step 1: Read audio file and save to temporary file for accent detection
        step_start = time.time()
        audio_bytes = await audio_file.read()
        step_times['read_audio'] = time.time() - step_start
        logger.info(f"✅ STEP 1: Read audio file - {len(audio_bytes)} bytes ({step_times['read_audio']:.2f}s)")
        
        # Save audio to temporary file for accent classification
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_file_path = tmp_file.name
        
        try:
            # Step 2: Transcribe with Whisper (speech-to-text)
            step_start = time.time()
            logger.info("🔄 STEP 2: Starting Whisper transcription...")
            transcription_result = await transcribe_audio(audio_bytes, language=language)
            step_times['whisper_transcription'] = time.time() - step_start
            logger.info(f"✅ STEP 2: Whisper transcription completed ({step_times['whisper_transcription']:.2f}s)")
            
            # Check if transcription_result is None or not a dict
            if transcription_result is None:
                raise HTTPException(
                    status_code=500,
                    detail="Whisper transcription returned None. Please try again."
                )
            
            if not isinstance(transcription_result, dict):
                logger.error(f"Transcription result is not a dict: {type(transcription_result)}")
                raise HTTPException(
                    status_code=500,
                    detail="Whisper transcription returned invalid format. Please try again."
                )
            
            transcribed_text = transcription_result.get("transcribed_text", "")
            detected_language = transcription_result.get("language", language)
            
            # Check if transcription is empty or unclear
            if not transcribed_text or len(transcribed_text.strip()) < 1:
                # Return a friendly response asking user to be more clear
                unclear_response = remove_asterisks("What? I can't understand your terrible pronunciation. Speak clearly or don't bother.")
                logger.warning("Transcription was empty - asking user to be more clear")
                
                # Generate TTS for the unclear response
                audio_base64 = None
                accent_name = target_accent.lower().replace(' english', '').replace('english', '').strip()
                try:
                    audio_bytes = await text_to_speech(
                        text=unclear_response,
                        accent=accent_name,
                        robotic=True
                    )
                    if audio_bytes and len(audio_bytes) > 0:
                        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                except Exception as tts_error:
                    logger.warning(f"TTS generation failed for unclear response: {tts_error}")
                
                return {
                    "transcribed_text": "",
                    "ai_message": unclear_response,
                    "pronunciation_score": None,
                    "pronunciation_feedback": "Could you speak a bit more clearly?",
                    "struggle_areas": [],
                    "audio_base64": audio_base64,
                    "detected_user_accent": None,
                    "accent_confidence": None
                }
            
            # Check if transcription is too short or unclear (less than 3 characters after cleaning)
            cleaned_text = transcribed_text.strip()
            if len(cleaned_text) < 3:
                unclear_response = remove_asterisks("Your pronunciation is so bad I can't even understand you. Try again, and this time actually speak clearly.")
                logger.warning(f"Transcription too short ({len(cleaned_text)} chars): '{cleaned_text}' - asking user to be more clear")
                
                # Generate TTS for the unclear response
                audio_base64 = None
                accent_name = target_accent.lower().replace(' english', '').replace('english', '').strip()
                try:
                    audio_bytes = await text_to_speech(
                        text=unclear_response,
                        accent=accent_name,
                        robotic=True
                    )
                    if audio_bytes and len(audio_bytes) > 0:
                        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                except Exception as tts_error:
                    logger.warning(f"TTS generation failed for unclear response: {tts_error}")
                
                return {
                    "transcribed_text": cleaned_text,
                    "ai_message": unclear_response,
                    "pronunciation_score": None,
                    "pronunciation_feedback": "Could you speak a bit more clearly?",
                    "struggle_areas": [],
                    "audio_base64": audio_base64,
                    "detected_user_accent": None,
                    "accent_confidence": None
                }
            
            # Check if transcription is mostly noise/unintelligible (mostly punctuation or special chars)
            # Count alphabetic characters vs total characters
            alpha_chars = len(re.sub(r'[^a-zA-Z]', '', cleaned_text))
            total_chars = len(cleaned_text)
            if total_chars > 0 and alpha_chars / total_chars < 0.3:  # Less than 30% alphabetic
                unclear_response = remove_asterisks("That was unintelligible garbage. Speak properly or get lost.")
                logger.warning(f"Transcription appears to be mostly noise ({alpha_chars}/{total_chars} alphabetic): '{cleaned_text}' - asking user to be more clear")
                
                # Generate TTS for the unclear response
                audio_base64 = None
                accent_name = target_accent.lower().replace(' english', '').replace('english', '').strip()
                try:
                    audio_bytes = await text_to_speech(
                        text=unclear_response,
                        accent=accent_name,
                        robotic=True
                    )
                    if audio_bytes and len(audio_bytes) > 0:
                        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                except Exception as tts_error:
                    logger.warning(f"TTS generation failed for unclear response: {tts_error}")
                
                return {
                    "transcribed_text": cleaned_text,
                    "ai_message": unclear_response,
                    "pronunciation_score": None,
                    "pronunciation_feedback": "Could you speak a bit more clearly?",
                    "struggle_areas": [],
                    "audio_base64": audio_base64,
                    "detected_user_accent": None,
                    "accent_confidence": None
                }
            
            logger.info(f"   Whisper transcribed text: '{transcribed_text}' (detected language: {detected_language})")
            
            # Step 2.5: Detect user's accent from audio (non-blocking, fast timeout)
            # Skip accent detection if it's causing delays - can be re-enabled later
            step_start = time.time()
            detected_user_accent = None
            accent_confidence = None
            
            # Temporarily disable accent detection to prevent hanging
            # Set ENABLE_ACCENT_DETECTION=true in .env to re-enable
            enable_accent_detection = os.getenv("ENABLE_ACCENT_DETECTION", "false").lower() == "true"
            
            if enable_accent_detection:
                logger.info("🔄 STEP 2.5: Starting accent detection...")
                try:
                    import asyncio
                    # Use a very short timeout to avoid blocking the request
                    accent_classification = await asyncio.wait_for(
                        classify_accent(
                            tmp_file_path,
                            use_classifier=False,  # Use fast heuristic to avoid timeout in live chat
                            timeout=2.0  # Very short timeout - 2 seconds max
                        ),
                        timeout=2.0  # Maximum 2 seconds total
                    )
                    detected_user_accent = accent_classification.get("predicted_accent", None)
                    accent_confidence = accent_classification.get("confidence", None)
                    accent_method = accent_classification.get("method", "unknown")
                    step_times['accent_detection'] = time.time() - step_start
                    logger.info(f"✅ STEP 2.5: Accent detection completed ({step_times['accent_detection']:.2f}s)")
                    logger.info(f"   Detected: {detected_user_accent} (confidence: {accent_confidence:.2f if accent_confidence else 'N/A'}, method: {accent_method})")
                    
                    # Note: User is speaking with {detected_user_accent} accent, learning {target_accent}
                    if detected_user_accent:
                        logger.info(f"   User accent noted: {detected_user_accent} (target: {target_accent})")
                        
                except asyncio.TimeoutError:
                    step_times['accent_detection'] = time.time() - step_start
                    logger.warning(f"⚠️ STEP 2.5: Accent detection timed out after 2s ({step_times['accent_detection']:.2f}s) - continuing without accent detection")
                    detected_user_accent = None
                    accent_confidence = None
                except Exception as e:
                    step_times['accent_detection'] = time.time() - step_start
                    logger.warning(f"⚠️ STEP 2.5: Accent detection failed ({step_times['accent_detection']:.2f}s): {e} - continuing without accent detection")
                    detected_user_accent = None
                    accent_confidence = None
            else:
                step_times['accent_detection'] = 0
                logger.debug("⏭️ STEP 2.5: Accent detection disabled (set ENABLE_ACCENT_DETECTION=true to enable)")
        finally:
            # Clean up temporary file immediately after accent detection
            try:
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
                    logger.debug(f"Cleaned up temp file: {tmp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")
        
        # Step 3: Parse conversation history
        history = []
        if conversation_history:
            try:
                import json
                history_data = json.loads(conversation_history)
                
                # Check if history_data is None or not a list
                if history_data is None:
                    logger.warning("Conversation history parsed to None, using empty history")
                    history_data = []
                
                if not isinstance(history_data, list):
                    logger.warning(f"Conversation history is not a list: {type(history_data)}, using empty history")
                    history_data = []
                
                for msg in history_data:
                    if msg is None:
                        continue
                    if not isinstance(msg, dict):
                        logger.warning(f"History message is not a dict: {type(msg)}, skipping")
                        continue
                    history.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            except Exception as e:
                logger.warning(f"Failed to parse conversation history: {e}")
        
        # Hardcoded conversation for Beijing Mandarin
        target_accent_lower = target_accent.lower()
        is_beijing_mandarin = "beijing" in target_accent_lower and "mandarin" in target_accent_lower
        
        if is_beijing_mandarin:
            # Count assistant messages in history to determine which step we're on
            # Step 0: 0 assistant messages (intro)
            # Step 1: 1 assistant message (second response)
            # Step 2: 2 assistant messages (third response)
            assistant_message_count = sum(1 for msg in history if msg.get("role") == "assistant")
            
            # Step 0: Intro statement (no assistant messages yet - this is the first response)
            if assistant_message_count == 0:
                import asyncio
                await asyncio.sleep(3)  # 3 second delay
                
                hardcoded_response = "你好 (Nǐ hǎo)! I'm Wally — your AI accent coach. Would you like me to help you learn the Beijing Mandarin accent? It's famous for its clear tones and the \"儿化音\" — that charming -er sound at the end of words."
                
                # Generate TTS for the response
                audio_base64 = None
                accent_name = target_accent.lower().replace(' english', '').replace('english', '').strip()
                try:
                    audio_bytes = await text_to_speech(
                        text=hardcoded_response,
                        accent=accent_name,
                        robotic=True
                    )
                    if audio_bytes and len(audio_bytes) > 0:
                        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                except Exception as tts_error:
                    logger.warning(f"TTS generation failed for hardcoded response: {tts_error}")
                
                return {
                    "transcribed_text": transcribed_text,
                    "ai_message": hardcoded_response,
                    "pronunciation_score": None,
                    "pronunciation_feedback": None,
                    "struggle_areas": [],
                    "audio_base64": audio_base64,
                    "detected_user_accent": None,
                    "accent_confidence": None
                }
            
            # Step 1: Second response (1 assistant message - intro already sent)
            elif assistant_message_count == 1:
                import asyncio
                await asyncio.sleep(3)  # 3 second delay
                
                hardcoded_response = "太好了！(Tài hǎo le!) Awesome! Let's start simple.\n\nIn Beijing Mandarin, people might say:\n\n\"你吃饭了吗儿？\" (Nǐ chī fàn le ma'r? – \"Have you eaten?\")\n\nTry answering me in Mandarin — you can say whether you've eaten or not!"
                
                # Generate TTS for the response
                audio_base64 = None
                accent_name = target_accent.lower().replace(' english', '').replace('english', '').strip()
                try:
                    audio_bytes = await text_to_speech(
                        text=hardcoded_response,
                        accent=accent_name,
                        robotic=True
                    )
                    if audio_bytes and len(audio_bytes) > 0:
                        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                except Exception as tts_error:
                    logger.warning(f"TTS generation failed for hardcoded response: {tts_error}")
                
                return {
                    "transcribed_text": transcribed_text,
                    "ai_message": hardcoded_response,
                    "pronunciation_score": None,
                    "pronunciation_feedback": None,
                    "struggle_areas": [],
                    "audio_base64": audio_base64,
                    "detected_user_accent": None,
                    "accent_confidence": None
                }
            
            # Step 2: Third response (2 assistant messages - intro and second response already sent)
            elif assistant_message_count == 2:
                import asyncio
                await asyncio.sleep(3)  # 3 second delay
                
                hardcoded_response = "很好！(Hěn hǎo!) That's a great start! Your tone pattern is clear.\n\nBut in the Beijing accent, people often add that 儿 sound playfully. You could say:\n\n\"我吃了儿～\" (Wǒ chī le'r~)\n\nNotice how the -r rolls slightly at the end? That's the signature Beijing flavor!\n\nLet's try that together — slowly: chī le'r… chī le'r…"
                
                # Generate TTS for the response
                audio_base64 = None
                accent_name = target_accent.lower().replace(' english', '').replace('english', '').strip()
                try:
                    audio_bytes = await text_to_speech(
                        text=hardcoded_response,
                        accent=accent_name,
                        robotic=True
                    )
                    if audio_bytes and len(audio_bytes) > 0:
                        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                except Exception as tts_error:
                    logger.warning(f"TTS generation failed for hardcoded response: {tts_error}")
                
                return {
                    "transcribed_text": transcribed_text,
                    "ai_message": hardcoded_response,
                    "pronunciation_score": None,
                    "pronunciation_feedback": None,
                    "struggle_areas": [],
                    "audio_base64": audio_base64,
                    "detected_user_accent": None,
                    "accent_confidence": None
                }
        
        # Step 3: Use Gemini to analyze pronunciation and generate feedback
        # Include detected user accent in the analysis for better feedback
        step_start = time.time()
        logger.info("🔄 STEP 3: Starting pronunciation analysis with Gemini...")
        pronunciation_analysis = generate_pronunciation_feedback_with_gemini(
            transcribed_text=transcribed_text,
            target_accent=target_accent,
            conversation_history=history,
            detected_user_accent=detected_user_accent  # Pass detected accent for better analysis
        )
        step_times['pronunciation_analysis'] = time.time() - step_start
        logger.info(f"✅ STEP 3: Pronunciation analysis completed ({step_times['pronunciation_analysis']:.2f}s)")
        
        # Check if pronunciation_analysis is None or not a dict
        if pronunciation_analysis is None:
            logger.error("❌ STEP 3: Pronunciation analysis returned None")
            raise HTTPException(
                status_code=500,
                detail="Failed to analyze pronunciation. Please try again."
            )
        
        if not isinstance(pronunciation_analysis, dict):
            logger.error(f"❌ STEP 3: Pronunciation analysis is not a dict: {type(pronunciation_analysis)}")
            raise HTTPException(
                status_code=500,
                detail="Pronunciation analysis returned invalid format. Please try again."
            )
        
        pronunciation_score = pronunciation_analysis.get("pronunciation_score", 75.0)
        pronunciation_feedback = pronunciation_analysis.get("feedback", "")
        struggle_areas = pronunciation_analysis.get("struggle_areas", [])
        logger.info(f"   Pronunciation score: {pronunciation_score}, Struggle areas: {struggle_areas}")
        
        # Step 4: Generate conversational response with Gemini
        step_start = time.time()
        logger.info("🔄 STEP 4: Starting conversational response generation with Gemini...")
        logger.info(f"   User message (transcribed): '{transcribed_text}'")
        logger.info(f"   Conversation history length: {len(history)} messages")
        if history:
            logger.debug(f"   Recent history: {history[-3:]}")
        ai_message_raw = generate_conversational_response(
            user_message=transcribed_text,
            conversation_history=history,
            target_accent=target_accent,
            pronunciation_score=pronunciation_score,
            struggle_areas=struggle_areas
        )
        step_times['conversational_response'] = time.time() - step_start
        logger.info(f"✅ STEP 4: Conversational response generated ({step_times['conversational_response']:.2f}s)")
        
        # Remove asterisks from AI message
        ai_message = remove_asterisks(ai_message_raw) if ai_message_raw else None
        
        # Check if ai_message is None or not a string
        if ai_message is None:
            logger.error("generate_conversational_response returned None")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate AI response. Please try again."
            )
        
        if not isinstance(ai_message, str):
            logger.error(f"AI message is not a string: {type(ai_message)}")
            raise HTTPException(
                status_code=500,
                detail="AI response returned invalid format. Please try again."
            )
        
        if len(ai_message.strip()) == 0:
            logger.error("AI message is empty")
            raise HTTPException(
                status_code=500,
                detail="AI response was empty. Please try again."
            )
        
        logger.info(f"   Generated AI response: '{ai_message[:100]}...' (length: {len(ai_message)})")
        
        # Step 5: Generate TTS audio for response
        step_start = time.time()
        audio_base64 = None
        accent_name = target_accent.lower().replace(' english', '').replace('english', '').strip()
        
        logger.info("🔄 STEP 5: Starting TTS audio generation...")
        try:
            audio_bytes = await text_to_speech(
                text=ai_message,
                accent=accent_name,
                robotic=True  # Wally has a robotic voice
            )
            step_times['tts_generation'] = time.time() - step_start
            
            if audio_bytes and len(audio_bytes) > 0:
                audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                logger.info(f"✅ STEP 5: TTS audio generation completed ({step_times['tts_generation']:.2f}s)")
                logger.info(f"   Generated audio: {len(audio_bytes)} bytes, base64 length: {len(audio_base64)}")
            else:
                logger.warning(f"⚠️ STEP 5: TTS returned empty audio bytes ({step_times['tts_generation']:.2f}s)")
                audio_base64 = None
        except Exception as tts_error:
            step_times['tts_generation'] = time.time() - step_start
            logger.error(f"❌ STEP 5: TTS generation failed ({step_times['tts_generation']:.2f}s): {tts_error}", exc_info=True)
            audio_base64 = None
        
        total_time = time.time() - start_time
        step_times['total'] = total_time
        
        logger.info("=" * 80)
        logger.info(f"✅ CHAT REQUEST COMPLETED - Total time: {total_time:.2f}s")
        logger.info(f"   Step timings:")
        logger.info(f"     - Read audio: {step_times.get('read_audio', 0):.2f}s")
        logger.info(f"     - Whisper transcription: {step_times.get('whisper_transcription', 0):.2f}s")
        logger.info(f"     - Accent detection: {step_times.get('accent_detection', 0):.2f}s")
        logger.info(f"     - Pronunciation analysis: {step_times.get('pronunciation_analysis', 0):.2f}s")
        logger.info(f"     - Conversational response: {step_times.get('conversational_response', 0):.2f}s")
        logger.info(f"     - TTS generation: {step_times.get('tts_generation', 0):.2f}s")
        logger.info(f"   Response: {len(ai_message)} chars, Audio: {'Yes' if audio_base64 else 'No'}")
        logger.info("=" * 80)
        
        return {
            "transcribed_text": transcribed_text,
            "ai_message": ai_message,
            "pronunciation_score": pronunciation_score,
            "pronunciation_feedback": pronunciation_feedback,
            "struggle_areas": struggle_areas,
            "audio_base64": audio_base64,
            "detected_user_accent": detected_user_accent,  # Include detected accent in response
            "accent_confidence": accent_confidence
        }
        
    except HTTPException:
        total_time = time.time() - start_time if 'start_time' in locals() else 0
        logger.error("=" * 80)
        logger.error(f"❌ CHAT REQUEST FAILED (HTTPException) - Total time: {total_time:.2f}s")
        logger.error(f"   Step timings: {step_times if 'step_times' in locals() else 'N/A'}")
        logger.error("=" * 80)
        raise
    except Exception as e:
        total_time = time.time() - start_time if 'start_time' in locals() else 0
        logger.error("=" * 80)
        logger.error(f"❌ CHAT REQUEST FAILED (Exception) - Total time: {total_time:.2f}s")
        logger.error(f"   Error: {str(e)}")
        logger.error(f"   Error type: {type(e).__name__}")
        logger.error(f"   Step timings: {step_times if 'step_times' in locals() else 'N/A'}")
        logger.error("=" * 80)
        logger.error(f"Full exception traceback:", exc_info=True)
        # Ensure temp file is cleaned up even on error
        try:
            if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
        except:
            pass
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process audio: {str(e)}"
        )


@router.get("/status")
async def chat_status():
    """
    Check Gemini connection status
    """
    return {
        "gemini_available": GEMINI_AVAILABLE,
        "gemini_status": GEMINI_STATUS,
        "gemini_error": GEMINI_ERROR,
        "message": "connected" if GEMINI_AVAILABLE else f"not connected ({GEMINI_STATUS})"
    }

