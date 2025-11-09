"""
Live Chat Routes
AI conversation endpoint for live chat mode
"""

import logging
import json
import re
import time
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import google.generativeai as genai
import os
import base64

from services.tts import text_to_speech
from services.transcribe import transcribe_audio

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
GEMINI_MODEL_NAME = "gemini-1.5-flash-latest"

try:
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("OPENAI_API_KEY")
    if api_key:
        if api_key == "YOUR_GOOGLE_API_KEY_HERE" or not api_key.strip():
            GEMINI_AVAILABLE = False
            GEMINI_STATUS = "key_not_set"
            logger.warning("Google API key is placeholder or empty - chat will use fallback responses")
        else:
            genai.configure(api_key=api_key)
            try:
                model_names = [
                    "models/gemini-2.5-flash",
                    "models/gemini-2.0-flash",
                    "models/gemini-flash-latest",
                    "models/gemini-1.5-flash",
                    "models/gemini-pro-latest",
                ]
                test_success = False
                
                for model_name in model_names:
                    try:
                        test_model = genai.GenerativeModel(model_name)
                        test_response = test_model.generate_content("Say 'connected' if you can read this.")
                        if test_response and test_response.text:
                            GEMINI_AVAILABLE = True
                            GEMINI_STATUS = "connected"
                            globals()['GEMINI_MODEL_NAME'] = model_name
                            test_success = True
                            logger.info(f"✓ Gemini API connected and working with model: {model_name}")
                            break
                    except Exception as model_error:
                        logger.debug(f"Model {model_name} failed: {model_error}")
                        continue
                
                if not test_success:
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


def generate_conversational_response(
    user_message: str,
    conversation_history: List[Dict[str, str]],
    target_accent: str,
    target_language: str = "English",
    accent_feedback_hint: Optional[str] = None
) -> str:
    """
    Generate a friendly, conversational AI response using Gemini
    """
    if not GEMINI_AVAILABLE:
        logger.error("GEMINI_AVAILABLE is False - cannot generate responses!")
        raise HTTPException(
            status_code=503,
            detail=f"Gemini API is not available (status: {GEMINI_STATUS}, error: {GEMINI_ERROR})."
        )
    
    try:
        logger.info(f"Using Gemini model: {GEMINI_MODEL_NAME} to generate conversational response")
        logger.info(f"User message: '{user_message[:100] if user_message else '(greeting)'}...'")
        
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        
        # Build conversation history text
        conversation_context = ""
        if conversation_history:
            conversation_context = "\n\nHere is our conversation so far:\n"
            for msg in conversation_history[-10:]:  # Last 10 messages for context
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if content and content.strip():
                    if role == "user":
                        conversation_context += f"User: {content}\n"
                    else:
                        conversation_context += f"Wally: {content}\n"
        
        # Build the main prompt
        if user_message and user_message.strip():
            current_message_context = f"\n\nUser just said: \"{user_message}\""
        else:
            current_message_context = "\n\n(This is the start of our conversation - greet them naturally)"
        
        # Add accent feedback instruction if provided
        accent_instruction = ""
        if accent_feedback_hint:
            accent_instruction = f"\n\nCRITICAL: You MUST include accent feedback in your response. After your conversational response, you MUST naturally add this accent tip: \"{accent_feedback_hint}\" Make it flow naturally as part of your response, not as a separate statement. This is REQUIRED - do not skip it. The feedback should be integrated seamlessly into your response."
        
        # Build language-specific instructions
        language_instruction = ""
        if target_language in ["Mandarin Chinese", "Chinese"]:
            language_instruction = "\n\nCRITICAL FOR CHINESE: You MUST respond in Chinese (中文). You understand Chinese perfectly. When the user speaks Chinese, respond in Chinese. Use Chinese characters, not pinyin. Be natural and conversational in Chinese."
        elif target_language == "Japanese":
            language_instruction = "\n\nCRITICAL FOR JAPANESE: You MUST respond in Japanese (日本語). You understand Japanese perfectly. When the user speaks Japanese, respond in Japanese. Use Japanese characters (hiragana, katakana, kanji). Be natural and conversational in Japanese."
        
        full_prompt = f"""You are Wally, a friendly conversational AI assistant. You are having a natural, ongoing conversation with someone in {target_language}. You understand {target_language} perfectly and can have full conversations in it.

CRITICAL: You MUST ALWAYS respond ENTIRELY in {target_language}. Never use English unless {target_language} is English.

IMPORTANT: You understand and can process text in {target_language} perfectly. When the user writes or speaks in {target_language}, you understand it completely. You can read Chinese characters (中文), Japanese characters (日本語), and all other language scripts. Do not ask them to translate or repeat - you understand everything they say in {target_language}. If they say something in {target_language}, respond naturally in {target_language} as if you understood perfectly.{language_instruction}

You are having a REAL conversation - you understand context, remember what was said, and respond naturally. Be conversational and engaging like talking to a friend. Ask follow-up questions, show interest, keep the conversation flowing naturally.

{conversation_context}{current_message_context}{accent_instruction}

Now respond naturally in {target_language} as Wally. Continue the conversation - acknowledge what they said, respond appropriately, ask questions, share thoughts. Be a good conversational partner. Keep it natural and engaging (1-3 sentences typically)."""
        
        # Configure safety settings
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
        
        # Generate response with retry logic
        max_retries = 2
        response = None
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🔄 Attempting Gemini generation (attempt {attempt + 1}/{max_retries})...")
                response = model.generate_content(
                    full_prompt,
                    generation_config={
                        "temperature": 0.8,
                        "top_p": 0.95,
                        "top_k": 40,
                        "max_output_tokens": 500,
                    },
                    safety_settings=safety_settings
                )
                logger.info(f"✅ Gemini generation successful on attempt {attempt + 1}")
                break  # Success, exit retry loop
            except Exception as gen_error:
                last_error = gen_error
                logger.warning(f"⚠️ Gemini generation attempt {attempt + 1} failed: {gen_error}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(0.5)  # Brief delay before retry
                else:
                    logger.error(f"❌ All {max_retries} attempts failed. Last error: {gen_error}")
        
        if not response:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate response after {max_retries} attempts: {str(last_error) if last_error else 'Unknown error'}"
            )
        
        # Extract response text with detailed diagnostics
        ai_response_text = None
        
        # Check for finish_reason (safety blocks, etc.)
        finish_reason = None
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'finish_reason'):
                finish_reason = candidate.finish_reason
                logger.info(f"Gemini finish_reason: {finish_reason}")
            
            # Check if blocked by safety filters
            if finish_reason in [2, 3]:  # 2 = SAFETY, 3 = RECITATION
                logger.warning(f"⚠️ Gemini response blocked by safety filter (reason: {finish_reason})")
                # Try to get partial text if available
            if hasattr(candidate, 'content') and candidate.content:
                if hasattr(candidate.content, 'parts'):
                    parts_text = []
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            parts_text.append(part.text)
                    if parts_text:
                        ai_response_text = " ".join(parts_text).strip()
                        logger.info(f"✅ Extracted partial text despite safety block: '{ai_response_text[:50]}...'")
        
        # Try standard text extraction
        if not ai_response_text:
            try:
                if hasattr(response, 'text') and response.text:
                    ai_response_text = response.text.strip()
            except Exception as text_err:
                logger.debug(f"Quick text accessor failed: {text_err}")
        
        # Try extracting from candidates
        if not ai_response_text:
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts'):
                        parts_text = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                parts_text.append(part.text)
                        if parts_text:
                            ai_response_text = " ".join(parts_text).strip()
        
        # Try alternative extraction methods
        if not ai_response_text:
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                # Try direct text attribute
                if hasattr(candidate, 'text') and candidate.text:
                    ai_response_text = candidate.text.strip()
        
        # If still no text, log detailed diagnostics and provide fallback
        if not ai_response_text or len(ai_response_text.strip()) < 1:
            logger.error(f"❌ Gemini returned empty response. finish_reason: {finish_reason}")
            logger.error(f"   Response object: {type(response)}")
            logger.error(f"   Has candidates: {hasattr(response, 'candidates')}")
            if hasattr(response, 'candidates') and response.candidates:
                logger.error(f"   Candidate count: {len(response.candidates)}")
                candidate = response.candidates[0]
                logger.error(f"   Candidate type: {type(candidate)}")
                logger.error(f"   Candidate attributes: {dir(candidate)}")
            
            # Provide fallback response in target language
            if target_language == "Mandarin Chinese" or target_language == "Chinese":
                ai_response_text = "好的，我明白了。让我们继续聊天吧！"
            elif target_language == "Japanese":
                ai_response_text = "わかりました。会話を続けましょう！"
            elif target_language == "Spanish":
                ai_response_text = "Entendido, continuemos la conversación."
            elif target_language == "French":
                ai_response_text = "D'accord, continuons la conversation."
            elif target_language == "German":
                ai_response_text = "Verstanden, lass uns das Gespräch fortsetzen."
            elif target_language == "Italian":
                ai_response_text = "Capito, continuiamo la conversazione."
            elif target_language == "Portuguese":
                ai_response_text = "Entendido, vamos continuar a conversa."
            else:
                ai_response_text = "I understand. Let's continue our conversation."
            
            logger.warning(f"⚠️ Using fallback response: '{ai_response_text}'")
        
        ai_response_text = remove_asterisks(ai_response_text)
        logger.info(f"✅ Generated response: '{ai_response_text[:100]}...'")
        return ai_response_text
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CRITICAL: Gemini generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate response: {str(e)}"
        )


def generate_simple_accent_feedback(
    user_text: str,
    target_language: str,
    target_accent: str
) -> str:
    """
    Generate simple, brief accent feedback using Gemini
    No Whisper, no complex analysis - just a quick tip
    """
    if not GEMINI_AVAILABLE:
        return None
    
    try:
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        
        # Simple prompt for accent feedback
        feedback_prompt = f"""The user just said: "{user_text}"

They are practicing {target_language} with a {target_accent} accent.

Give ONE brief, specific tip to help them sound more like {target_accent}. Be very specific - mention a specific sound, word, or pronunciation pattern. Keep it to 1 sentence.

Example format: "Also, if you want to sound more like {target_accent}, try putting more emphasis on the 'er' sound in words like 'na er'."

Respond in {target_language}."""
        
        response = model.generate_content(
            feedback_prompt,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 100,  # Keep it brief
            }
        )
        
        feedback_text = None
        try:
            if hasattr(response, 'text') and response.text:
                feedback_text = response.text.strip()
        except:
            pass
        
        if not feedback_text:
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts'):
                        parts = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                parts.append(part.text)
                        if parts:
                            feedback_text = " ".join(parts).strip()
        
        if feedback_text:
            feedback_text = remove_asterisks(feedback_text)
            logger.info(f"✅ Generated accent feedback: '{feedback_text}'")
            return feedback_text
        else:
            return None
        
    except Exception as e:
        logger.warning(f"Failed to generate accent feedback: {e}")
        return None


# Track active greeting requests to prevent duplicates
_active_greeting_requests = {}  # session_id -> timestamp

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
    Main chat endpoint: Process audio, generate conversational response + accent feedback
    
    Pipeline:
    1. If empty audio (first chat) -> Generate greeting in target language
    2. If user audio -> Transcribe, generate conversational response, add accent feedback
    """
    start_time = time.time()
    
    try:
        logger.info("=" * 80)
        logger.info(f"🔵 CHAT REQUEST - Session: {session_id}, User: {user_id}")
        logger.info(f"   Target accent: {target_accent}, Language: {language}")
        
        # Step 1: Read audio file
        audio_bytes = await audio_file.read()
        logger.info(f"✅ Read audio: {len(audio_bytes)} bytes")
        
        # Get target language name
        target_language_name = language
        if isinstance(language, dict):
            target_language_name = language.get('name', 'English')
        elif isinstance(language, str):
            language_map = {
                'english': 'English',
                'spanish': 'Spanish',
                'french': 'French',
                'german': 'German',
                'italian': 'Italian',
                'portuguese': 'Portuguese',
                'mandarin': 'Mandarin Chinese',
                'chinese': 'Mandarin Chinese',
                'japanese': 'Japanese'
            }
            target_language_name = language_map.get(language.lower(), language)
        
        # Handle empty audio (first chat) - generate greeting
        if len(audio_bytes) == 0:
            # CRITICAL: Check for duplicate greeting requests BEFORE doing any work
            current_time = time.time()
            if session_id in _active_greeting_requests:
                last_request_time = _active_greeting_requests[session_id]
                if current_time - last_request_time < 5.0:  # Within 5 seconds (increased from 2)
                    logger.warning(f"⚠️ Duplicate greeting request detected for session {session_id} - ignoring (last request {current_time - last_request_time:.2f}s ago)")
                raise HTTPException(
                        status_code=429,
                        detail="Greeting request already in progress. Please wait."
                    )
            
            # Mark this session as having an active greeting request IMMEDIATELY
            _active_greeting_requests[session_id] = current_time
            logger.info(f"🔵 Starting greeting generation for session {session_id}")
            
            try:
                greeting = generate_conversational_response(
                    user_message="",  # Empty triggers greeting
                    conversation_history=[],
                    target_accent=target_accent,
                    target_language=target_language_name
                )
                
                # Generate TTS for greeting - ONLY ONCE
                audio_base64 = None
                accent_name = target_accent.lower().replace(' english', '').replace('english', '').strip()
                logger.info(f"🎤 Generating TTS for greeting ({len(greeting)} chars)...")
                try:
                    audio_bytes_tts = await text_to_speech(
                        text=greeting,
                        accent=accent_name,
                        robotic=True
                    )
                    if audio_bytes_tts and len(audio_bytes_tts) > 0:
                        audio_base64 = base64.b64encode(audio_bytes_tts).decode('utf-8')
                        logger.info(f"✅ TTS generation successful for greeting ({len(audio_bytes_tts)} bytes)")
                    else:
                        logger.warning("⚠️ TTS returned empty audio for greeting")
                except Exception as tts_error:
                    logger.error(f"❌ TTS generation failed for greeting: {tts_error}", exc_info=True)
                    # Don't raise - continue without audio
                
                # Clean up the active request tracking after SUCCESS
                if session_id in _active_greeting_requests:
                    del _active_greeting_requests[session_id]
                    logger.info(f"✅ Greeting generation completed for session {session_id}")
                
                return {
                    "transcribed_text": "",
                    "ai_message": greeting,
                    "accent_feedback": None,  # No feedback for greeting
                    "audio_base64": audio_base64
                }
            except Exception as greeting_error:
                # Clean up on error
                if session_id in _active_greeting_requests:
                    del _active_greeting_requests[session_id]
                    logger.info(f"🧹 Cleaned up greeting request for session {session_id} after error")
                raise  # Re-raise the exception
        
        # Step 2: Transcribe user audio
        logger.info("🔄 Transcribing user audio...")
        # Normalize language for Whisper API (convert to ISO code)
        whisper_language = None
        if isinstance(language, str):
            language_lower = language.lower()
            # Map to Whisper language codes
            language_to_code = {
                'english': 'en',
                'spanish': 'es',
                'french': 'fr',
                'german': 'de',
                'italian': 'it',
                'portuguese': 'pt',
                'mandarin': 'zh',
                'chinese': 'zh',
                'japanese': 'ja'
            }
            whisper_language = language_to_code.get(language_lower, language_lower if len(language_lower) == 2 else None)
        elif isinstance(language, dict):
            # If language is a dict, extract the ID
            lang_id = language.get('id', 'english')
            language_lower = lang_id.lower()
            language_to_code = {
                'english': 'en',
                'spanish': 'es',
                'french': 'fr',
                'german': 'de',
                'italian': 'it',
                'portuguese': 'pt',
                'mandarin': 'zh',
                'chinese': 'zh',
                'japanese': 'ja'
            }
            whisper_language = language_to_code.get(language_lower, language_lower if len(language_lower) == 2 else None)
        
        logger.info(f"🔄 Transcribing with language hint: {whisper_language} (original: {language})")
        transcription_result = await transcribe_audio(audio_bytes, language=whisper_language)
        
        if not transcription_result or not isinstance(transcription_result, dict):
            raise HTTPException(status_code=500, detail="Whisper transcription failed")
        
        transcribed_text = transcription_result.get("transcribed_text", "")
        detected_language = transcription_result.get("language", whisper_language or "en")
        
        logger.info(f"✅ Transcription result: '{transcribed_text}' (detected: {detected_language})")
        
        if not transcribed_text or len(transcribed_text.strip()) < 1:
            # Generate unclear response in target language
            unclear_response = None
            if GEMINI_AVAILABLE:
                try:
                    unclear_prompt = f"""Generate a brief, friendly message in {target_language_name} asking the user to repeat what they said because you didn't catch it. Keep it to 1 sentence. Respond ONLY in {target_language_name}."""
                    model = genai.GenerativeModel(GEMINI_MODEL_NAME)
                    response = model.generate_content(unclear_prompt)
                    if response and response.text:
                        unclear_response = remove_asterisks(response.text.strip())
                except:
                    pass
            
            if not unclear_response:
                if target_language_name == 'English':
                    unclear_response = "Sorry, I didn't catch that. Could you say that again?"
                elif target_language_name == 'Mandarin Chinese':
                    unclear_response = "抱歉，我没听清楚。你能再说一遍吗？"
                else:
                    unclear_response = "Could you repeat that?"
                
                return {
                "transcribed_text": "",
                    "ai_message": unclear_response,
                "accent_feedback": None,
                "audio_base64": None
            }
        
        logger.info(f"✅ Transcribed: '{transcribed_text}'")
        
        # Step 3: Parse conversation history
        history = []
        if conversation_history:
            try:
                history_data = json.loads(conversation_history)
                if isinstance(history_data, list):
                    for msg in history_data:
                        if isinstance(msg, dict):
                            history.append({
                                "role": msg.get("role", "user"),
                                "content": msg.get("content", "")
                            })
            except Exception as e:
                logger.warning(f"Failed to parse conversation history: {e}")
        
        # Step 4: Generate simple accent feedback first (for context)
        logger.info("🔄 Generating accent feedback...")
        accent_feedback = generate_simple_accent_feedback(
            user_text=transcribed_text,
            target_language=target_language_name,
            target_accent=target_accent
        )
        
        # Ensure we always have accent feedback (fallback if generation fails)
        if not accent_feedback:
            logger.warning("⚠️ Accent feedback generation returned None, using fallback")
            # Generate dynamic fallback feedback based on accent and language
            accent_lower = target_accent.lower() if target_accent else ""
            is_american = "american" in accent_lower or "american english" in accent_lower
            
            # Generate a simple fallback feedback in target language
            if target_language_name in ["Mandarin Chinese", "Chinese"]:
                accent_feedback = f"另外，如果你想听起来更像{target_accent}，可以多注意一下发音的细节。"
            elif target_language_name == "Japanese":
                accent_feedback = f"また、{target_accent}のように聞こえるように、発音の細部に注意してください。"
            elif target_language_name == "Spanish":
                accent_feedback = f"Además, si quieres sonar más como {target_accent}, presta atención a los detalles de pronunciación."
            elif target_language_name == "French":
                accent_feedback = f"De plus, si vous voulez sonner plus comme {target_accent}, faites attention aux détails de prononciation."
            elif target_language_name == "German":
                accent_feedback = f"Außerdem, wenn Sie mehr wie {target_accent} klingen möchten, achten Sie auf Aussprachedetails."
            elif target_language_name == "Italian":
                accent_feedback = f"Inoltre, se vuoi suonare più come {target_accent}, presta attenzione ai dettagli della pronuncia."
            elif target_language_name == "Portuguese":
                accent_feedback = f"Além disso, se você quiser soar mais como {target_accent}, preste atenção aos detalhes da pronúncia."
            else:
                # English fallback - check for American English
                if is_american:
                    # American English-specific tips based on user's text
                    user_lower = transcribed_text.lower() if transcribed_text else ""
                    tips = []
                    
                    # Check for 'r' sounds (rhoticity)
                    if 'r' in user_lower or any(word in user_lower for word in ['car', 'far', 'water', 'better', 'butter']):
                        tips.append("pronounce all 'r' sounds clearly, like in 'car' and 'water'")
                    
                    # Check for 't' sounds (flapping)
                    if 't' in user_lower and any(word in user_lower for word in ['water', 'better', 'butter', 'matter']):
                        tips.append("remember that 't' between vowels sounds like 'd', so 'water' sounds like 'wader'")
                    
                    # Check for vowel sounds
                    if any(vowel in user_lower for vowel in 'aeiou'):
                        tips.append("make your vowel sounds more open and clear, like in 'can' and 'cat'")
                    
                    if tips:
                        accent_feedback = f"Also, if you want to sound more like {target_accent}, {tips[0]}."
                    else:
                        accent_feedback = f"Also, if you want to sound more like {target_accent}, practice pronouncing all 'r' sounds clearly and make your vowels more open."
                else:
                    accent_feedback = f"Also, if you want to sound more like {target_accent}, pay attention to pronunciation details."
        
        logger.info(f"✅ Accent feedback ready: '{accent_feedback[:50]}...'")
        
        # Step 5: Generate conversational response with accent feedback integrated
        logger.info("🔄 Generating conversational response...")
        ai_message = generate_conversational_response(
            user_message=transcribed_text,
            conversation_history=history,
            target_accent=target_accent,
            target_language=target_language_name,
            accent_feedback_hint=accent_feedback  # Pass feedback hint so Wally can include it naturally
        )
        
        # Step 6: Ensure accent feedback is included in the response
        # Simple check: if feedback exists and is not already at the end of the message, append it
        # We check if the feedback text (or a significant portion) appears in the message
        feedback_included = False
        if accent_feedback:
            # Check if a substantial portion of the feedback is already in the message
            # Use a more reliable check: see if at least 60% of the feedback words appear in the message
            feedback_words = set(word.lower() for word in accent_feedback.split() if len(word) > 2)
            message_words = set(word.lower() for word in ai_message.split())
            
            if feedback_words:
                overlap = len(feedback_words.intersection(message_words))
                overlap_ratio = overlap / len(feedback_words)
                feedback_included = overlap_ratio >= 0.6  # At least 60% of feedback words present
                
                # Also check if the feedback text itself appears (for exact matches)
                if not feedback_included:
                    feedback_included = accent_feedback.lower().strip() in ai_message.lower()
            
            if not feedback_included:
                # Append feedback only once - check we haven't already appended it
                if not ai_message.endswith(accent_feedback.strip()):
                    logger.info("📝 Appending accent feedback to response (not naturally included)")
                    ai_message = f"{ai_message} {accent_feedback}"
                else:
                    logger.info("✅ Accent feedback already appended to response")
            else:
                logger.info("✅ Accent feedback naturally included in response")
        
        # Step 7: Generate TTS for response (including accent feedback)
        # IMPORTANT: Only call TTS once per request
        audio_base64 = None
        accent_name = target_accent.lower().replace(' english', '').replace('english', '').strip()
        
        # Guard: Only generate TTS if we have a valid message
        if ai_message and len(ai_message.strip()) > 0:
            try:
                logger.info(f"🎤 Generating TTS for message ({len(ai_message)} chars)...")
                audio_bytes_tts = await text_to_speech(
                    text=ai_message,  # Use full message with feedback for TTS
                    accent=accent_name,
                    robotic=True
                )
                if audio_bytes_tts and len(audio_bytes_tts) > 0:
                    audio_base64 = base64.b64encode(audio_bytes_tts).decode('utf-8')
                    logger.info(f"✅ TTS generation successful ({len(audio_bytes_tts)} bytes)")
                else:
                    logger.warning("⚠️ TTS returned empty audio")
            except Exception as tts_error:
                logger.error(f"❌ TTS generation failed: {tts_error}", exc_info=True)
                # Don't raise - continue without audio
        else:
            logger.warning("⚠️ Skipping TTS generation - empty message")
        
        total_time = time.time() - start_time
        logger.info("=" * 80)
        logger.info(f"✅ CHAT REQUEST COMPLETED - Total time: {total_time:.2f}s")
        logger.info(f"   Response: {len(ai_message)} chars")
        logger.info(f"   Accent feedback: {accent_feedback[:50] if accent_feedback else 'None'}...")
        logger.info("=" * 80)
        
        return {
            "transcribed_text": transcribed_text,
            "ai_message": ai_message,
            "accent_feedback": accent_feedback,
            "audio_base64": audio_base64
        }
        
    except HTTPException:
        # Clean up on error
        if session_id in _active_greeting_requests:
            del _active_greeting_requests[session_id]
        raise
    except Exception as e:
        # Clean up on error
        if session_id in _active_greeting_requests:
            del _active_greeting_requests[session_id]
        logger.error(f"❌ CHAT REQUEST FAILED: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat: {str(e)}"
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
