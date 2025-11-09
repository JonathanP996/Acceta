"""
Phoneme-Level Accent Feedback Route
Provides detailed phoneme-level pronunciation feedback
"""

import logging
import os
import time
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import google.generativeai as genai

from services.transcribe import transcribe_audio
from services.phoneme_analyzer import analyze_pronunciation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/phoneme-feedback", tags=["phoneme-feedback"])

# Initialize Gemini (reuse from chat.py setup)
GEMINI_AVAILABLE = False
GEMINI_STATUS = "not_configured"
GEMINI_ERROR = None
GEMINI_MODEL_NAME = "gemini-1.5-flash-latest"

try:
    # Try to reuse Gemini connection from chat.py if available
    try:
        from routes.chat import GEMINI_AVAILABLE as CHAT_GEMINI_AVAILABLE, GEMINI_MODEL_NAME as CHAT_MODEL_NAME
        if CHAT_GEMINI_AVAILABLE:
            GEMINI_AVAILABLE = True
            GEMINI_STATUS = "connected"
            GEMINI_MODEL_NAME = CHAT_MODEL_NAME
            logger.info(f"✓ Reusing Gemini connection from chat.py: {CHAT_MODEL_NAME}")
        else:
            logger.info("Chat.py Gemini not available, trying to initialize separately...")
    except ImportError:
        logger.debug("Could not import from chat.py, initializing separately...")
    
    # If chat.py doesn't have Gemini, try to initialize it here
    if not GEMINI_AVAILABLE:
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("OPENAI_API_KEY")
        if api_key and api_key != "YOUR_GOOGLE_API_KEY_HERE" and api_key.strip():
            genai.configure(api_key=api_key)
            model_names = [
                "models/gemini-2.5-flash",
                "models/gemini-2.0-flash",
                "models/gemini-flash-latest",
                "models/gemini-pro-latest",
            ]
            for model_name in model_names:
                try:
                    test_model = genai.GenerativeModel(model_name)
                    test_response = test_model.generate_content("Say 'connected' if you can read this.")
                    if test_response and test_response.text:
                        GEMINI_AVAILABLE = True
                        GEMINI_STATUS = "connected"
                        GEMINI_MODEL_NAME = model_name
                        logger.info(f"✓ Gemini API connected for phoneme feedback: {model_name}")
                        break
                except Exception as model_error:
                    logger.warning(f"Model {model_name} test failed: {str(model_error)[:100]}")
                    continue
            if not GEMINI_AVAILABLE:
                GEMINI_STATUS = "connection_failed"
                GEMINI_ERROR = f"None of the tested models worked. Tried: {', '.join(model_names)}"
                logger.warning(f"Gemini not available for phoneme feedback: {GEMINI_ERROR}")
        else:
            GEMINI_STATUS = "key_not_found"
            GEMINI_ERROR = "No API key found (GOOGLE_API_KEY or OPENAI_API_KEY)"
            logger.warning(f"Gemini not available for phoneme feedback: {GEMINI_ERROR}")
except Exception as e:
    GEMINI_AVAILABLE = False
    GEMINI_STATUS = "initialization_error"
    GEMINI_ERROR = str(e)
    logger.error(f"Gemini initialization failed: {e}", exc_info=True)


class PhonemeFeedbackResponse(BaseModel):
    """Response model for phoneme feedback"""
    target_text: str
    user_text: str
    target_phonemes: str
    user_phonemes: str
    similarity_score: float
    differences: List[Dict[str, Any]]
    feedback: str
    specific_improvements: List[str]
    confidence_score: float


@router.post("/analyze", response_model=PhonemeFeedbackResponse)
async def analyze_phoneme_pronunciation(
    reference_audio: UploadFile = File(..., description="Reference/TTS audio file"),
    user_audio: UploadFile = File(..., description="User's spoken audio file"),
    target_text: str = Form(..., description="Expected text (what should be said)"),
    language: Optional[str] = Form(None, description="Language code (e.g., 'en')")
):
    """
    Analyze pronunciation at phoneme level by comparing reference and user audio
    
    Pipeline:
    1. Transcribe both reference and user audio with Whisper
    2. Extract phonemes from both transcriptions
    3. Compare phonemes to find differences
    4. Generate constructive feedback with Gemini
    
    Args:
        reference_audio: Reference/TTS audio (target pronunciation)
        user_audio: User's spoken audio
        target_text: Expected text (what should be said)
        language: Optional language code
    
    Returns:
        Detailed phoneme-level feedback
    """
    start_time = time.time()
    step_times = {}
    
    try:
        logger.info("🎯 Starting phoneme-level accent analysis")
        
        # Step 1: Read audio files
        step_start = time.time()
        reference_bytes = await reference_audio.read()
        user_bytes = await user_audio.read()
        step_times['read_audio'] = time.time() - step_start
        
        if not reference_bytes or not user_bytes:
            raise HTTPException(status_code=400, detail="Empty audio files")
        
        logger.info(f"✅ Read audio files ({step_times['read_audio']:.2f}s)")
        
        # Step 2: Transcribe both audios
        step_start = time.time()
        logger.info("🔄 Transcribing reference audio...")
        reference_transcription = await transcribe_audio(reference_bytes, language=language)
        reference_text = reference_transcription.get("transcribed_text", "")
        
        logger.info("🔄 Transcribing user audio...")
        user_transcription = await transcribe_audio(user_bytes, language=language)
        user_text = user_transcription.get("transcribed_text", "")
        step_times['transcription'] = time.time() - step_start
        
        if not reference_text or not user_text:
            raise HTTPException(
                status_code=400,
                detail="Could not transcribe one or both audio files"
            )
        
        logger.info(f"✅ Transcribed: Reference='{reference_text}', User='{user_text}' ({step_times['transcription']:.2f}s)")
        
        # Step 3: Extract phonemes and compare
        step_start = time.time()
        logger.info("🔄 Extracting and comparing phonemes...")
        phoneme_analysis = await analyze_pronunciation(
            target_text=target_text,
            user_text=user_text,
            language=language or "en"
        )
        step_times['phoneme_analysis'] = time.time() - step_start
        
        logger.info(f"✅ Phoneme analysis complete (similarity: {phoneme_analysis['similarity_score']:.2f}) ({step_times['phoneme_analysis']:.2f}s)")
        
        # Step 4: Generate feedback with Gemini (or fallback)
        step_start = time.time()
        logger.info("🔄 Generating phoneme-level feedback...")
        
        # Try to initialize Gemini if not available (in case it was a transient error)
        gemini_available_now = GEMINI_AVAILABLE
        gemini_model_name_now = GEMINI_MODEL_NAME
        if not GEMINI_AVAILABLE:
            logger.info("Gemini not available at startup, attempting to initialize now...")
            try:
                api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("OPENAI_API_KEY")
                logger.info(f"API key present: {bool(api_key and api_key != 'YOUR_GOOGLE_API_KEY_HERE' and api_key.strip())}")
                if api_key and api_key != "YOUR_GOOGLE_API_KEY_HERE" and api_key.strip():
                    genai.configure(api_key=api_key)
                    model_names = [
                        "models/gemini-2.5-flash",
                        "models/gemini-2.0-flash",
                        "models/gemini-flash-latest",
                        "models/gemini-pro-latest",
                    ]
                    logger.info(f"Testing {len(model_names)} Gemini models...")
                    for model_name in model_names:
                        try:
                            logger.debug(f"Testing model: {model_name}")
                            test_model = genai.GenerativeModel(model_name)
                            test_response = test_model.generate_content("test")
                            if test_response and test_response.text:
                                gemini_available_now = True
                                gemini_model_name_now = model_name
                                logger.info(f"✓ Gemini API now available: {model_name}")
                                break
                        except Exception as model_error:
                            error_msg = str(model_error)
                            # Check if it's a quota error
                            if "429" in error_msg or "quota" in error_msg.lower():
                                logger.warning(f"Model {model_name} quota exceeded - will use fallback feedback")
                            elif "404" in error_msg:
                                logger.debug(f"Model {model_name} not found (404)")
                            else:
                                logger.warning(f"Model {model_name} failed: {error_msg[:200]}")
                            continue
                    if not gemini_available_now:
                        logger.warning(f"All {len(model_names)} Gemini models failed to initialize")
                else:
                    logger.warning("No valid API key found for Gemini initialization")
            except Exception as e:
                logger.error(f"Gemini initialization retry failed with exception: {e}", exc_info=True)
        
        # Use gemini_available_now instead of GEMINI_AVAILABLE
        if not gemini_available_now:
            logger.warning("Gemini not available - using fallback feedback generation")
            # Generate basic feedback from phoneme analysis
            full_feedback = f"""**Overall Assessment**
Your pronunciation of "{target_text}" was transcribed as "{user_text}". 

"""
            
            if phoneme_analysis['similarity_score'] >= 0.9:
                full_feedback += "Excellent work! Your pronunciation is very close to the target accent. "
            elif phoneme_analysis['similarity_score'] >= 0.7:
                full_feedback += "Good pronunciation! You're making progress. "
            elif phoneme_analysis['similarity_score'] >= 0.5:
                full_feedback += "Keep practicing! There are some differences to work on. "
            else:
                full_feedback += "There are noticeable differences from the target pronunciation. "
            
            full_feedback += f"Your phoneme similarity score is {phoneme_analysis['similarity_score']*100:.1f}%.\n\n"
            
            # Add specific differences
            if phoneme_analysis['differences']:
                full_feedback += "**Specific Phoneme Issues**\n"
                for diff in phoneme_analysis['differences'][:5]:
                    if diff.get('type') == 'phoneme_mismatch':
                        full_feedback += f"- The phoneme '{diff.get('target_phonemes', '')}' should be pronounced, but you said '{diff.get('user_phonemes', '')}'. "
                    elif diff.get('type') == 'missing_phoneme':
                        full_feedback += f"- You're missing the phoneme '{diff.get('target_phonemes', '')}'. "
                    elif diff.get('type') == 'extra_phoneme':
                        full_feedback += f"- You added an extra phoneme '{diff.get('user_phonemes', '')}'. "
                full_feedback += "\n\n"
            
            full_feedback += "**Practice Recommendations**\n"
            full_feedback += "- Listen to the reference audio carefully and try to match the sounds.\n"
            full_feedback += "- Practice saying the phrase slowly, focusing on each sound.\n"
            full_feedback += "- Record yourself again and compare with the reference."
            
            # Extract improvements from differences
            specific_improvements = []
            for diff in phoneme_analysis['differences'][:5]:
                if diff.get('issue'):
                    specific_improvements.append(diff.get('issue'))
            
            if len(specific_improvements) == 0:
                specific_improvements = [
                    "Focus on matching the target phonemes",
                    "Practice the specific sounds that differ",
                    "Listen carefully to the reference pronunciation"
                ]
            
            step_times['gemini_feedback'] = time.time() - step_start
            logger.info(f"✅ Generated fallback feedback ({step_times['gemini_feedback']:.2f}s)")
        else:
            # Use Gemini for detailed feedback
            logger.info("Using Gemini for detailed phoneme feedback...")
            # Build structured data for Gemini
            differences_summary = []
            for diff in phoneme_analysis['differences'][:10]:  # Limit to top 10 differences
                differences_summary.append({
                    "phoneme": f"{diff.get('target_phonemes', '')}→{diff.get('user_phonemes', '')}",
                    "issue": diff.get('issue', ''),
                    "type": diff.get('type', 'unknown')
                })
            
            structured_data = {
                "target_sentence": target_text,
                "target_phonemes": phoneme_analysis['target_phonemes'],
                "user_phonemes": phoneme_analysis['user_phonemes'],
                "differences": differences_summary,
                "confidence_score": phoneme_analysis['similarity_score']
            }
            
            # Create prompt for Gemini - conversational, script-like feedback for TTS
            prompt = f"""You are a friendly pronunciation coach. The user said "{user_text}" but should have said "{target_text}".

Analyze the differences and provide natural, conversational feedback that sounds like you're speaking directly to them. Write it as a script for text-to-speech - no markdown, just natural speech.

Focus on specific words they mispronounced. For example, if they said "gahn" instead of "can", say: "You said 'gahn' instead of 'can'. Try saying 'can' with a clear 'k' sound at the beginning."

Structure your response as natural speech:
1. Start with overall assessment (1-2 sentences)
2. Point out specific word mistakes with examples (2-4 specific corrections)
3. Give 2-3 simple practice tips

Keep it encouraging, conversational, and easy to understand. Write as if you're speaking to them, not writing a document."""

            try:
                model = genai.GenerativeModel(gemini_model_name_now)
                generation_config = {
                    "temperature": 0.7,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 500,
                }
                response = model.generate_content(prompt, generation_config=generation_config)
                
                # Check for safety filter blocks
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if candidate.finish_reason == 2:  # SAFETY - blocked by safety filters
                        logger.warning("Gemini response blocked by safety filters - using fallback")
                        raise Exception("Response blocked by safety filters")
                    elif candidate.finish_reason == 3:  # RECITATION - blocked for recitation
                        logger.warning("Gemini response blocked for recitation concerns - using fallback")
                        raise Exception("Response blocked for recitation concerns")
                
                # Try to get text, handle case where response.text might fail
                try:
                    full_feedback = response.text.strip() if response.text else ""
                except (ValueError, AttributeError) as text_error:
                    # If response.text fails, try to get content from parts
                    if response.candidates and len(response.candidates) > 0:
                        candidate = response.candidates[0]
                        if candidate.content and candidate.content.parts:
                            full_feedback = " ".join([part.text for part in candidate.content.parts if hasattr(part, 'text') and part.text]).strip()
                        else:
                            raise Exception(f"Could not extract text from response: {text_error}")
                    else:
                        raise Exception(f"Could not extract text from response: {text_error}")
                
                if not full_feedback:
                    raise Exception("Gemini returned empty response")
            except Exception as gemini_error:
                logger.error(f"Gemini API call failed: {gemini_error}", exc_info=True)
                # Fall back to basic feedback if Gemini call fails
                logger.warning("Falling back to basic feedback due to Gemini error")
                # Generate fallback feedback (same as the else branch)
                full_feedback = f"""**Overall Assessment**
Your pronunciation of "{target_text}" was transcribed as "{user_text}". 

"""
                
                if phoneme_analysis['similarity_score'] >= 0.9:
                    full_feedback += "Excellent work! Your pronunciation is very close to the target accent. "
                elif phoneme_analysis['similarity_score'] >= 0.7:
                    full_feedback += "Good pronunciation! You're making progress. "
                elif phoneme_analysis['similarity_score'] >= 0.5:
                    full_feedback += "Keep practicing! There are some differences to work on. "
                else:
                    full_feedback += "There are noticeable differences from the target pronunciation. "
                
                full_feedback += f"Your phoneme similarity score is {phoneme_analysis['similarity_score']*100:.1f}%.\n\n"
                
                # Add specific differences
                if phoneme_analysis['differences']:
                    full_feedback += "**Specific Phoneme Issues**\n"
                    for diff in phoneme_analysis['differences'][:5]:
                        if diff.get('type') == 'phoneme_mismatch':
                            full_feedback += f"- The phoneme '{diff.get('target_phonemes', '')}' should be pronounced, but you said '{diff.get('user_phonemes', '')}'. "
                        elif diff.get('type') == 'missing_phoneme':
                            full_feedback += f"- You're missing the phoneme '{diff.get('target_phonemes', '')}'. "
                        elif diff.get('type') == 'extra_phoneme':
                            full_feedback += f"- You added an extra phoneme '{diff.get('user_phonemes', '')}'. "
                    full_feedback += "\n\n"
                
                full_feedback += "**Practice Recommendations**\n"
                full_feedback += "- Listen to the reference audio carefully and try to match the sounds.\n"
                full_feedback += "- Practice saying the phrase slowly, focusing on each sound.\n"
                full_feedback += "- Record yourself again and compare with the reference."
                
                # Set improvements from differences
                specific_improvements = []
                for diff in phoneme_analysis['differences'][:5]:
                    if diff.get('issue'):
                        specific_improvements.append(diff.get('issue'))
                
                if len(specific_improvements) == 0:
                    specific_improvements = [
                        "Focus on matching the target phonemes",
                        "Practice the specific sounds that differ",
                        "Listen carefully to the reference pronunciation"
                    ]
                
                step_times['gemini_feedback'] = time.time() - step_start
                logger.info(f"✅ Generated fallback feedback after Gemini error ({step_times['gemini_feedback']:.2f}s)")
                # Skip to response building
                return PhonemeFeedbackResponse(
                    target_text=target_text,
                    user_text=user_text,
                    target_phonemes=phoneme_analysis['target_phonemes'],
                    user_phonemes=phoneme_analysis['user_phonemes'],
                    similarity_score=phoneme_analysis['similarity_score'],
                    differences=phoneme_analysis['differences'],
                    feedback=full_feedback,
                    specific_improvements=specific_improvements[:5],
                    confidence_score=phoneme_analysis['confidence_score']
                )
            
            # Extract specific improvements from conversational feedback
            # Look for sentences that mention specific words or sounds
            specific_improvements = []
            sentences = [s.strip() for s in full_feedback.replace('!', '.').replace('?', '.').split('.') if s.strip()]
            
            # Look for sentences that contain specific corrections (mentions of words, sounds, or practice tips)
            for sentence in sentences:
                sentence_lower = sentence.lower()
                # Look for sentences that mention specific words, sounds, or give practice advice
                if any(keyword in sentence_lower for keyword in ['instead of', 'try saying', 'practice', 'focus on', 'work on', 'sound', 'pronounce']):
                    if len(sentence) > 15 and len(sentence) < 200:  # Reasonable length for TTS
                        specific_improvements.append(sentence)
                        if len(specific_improvements) >= 5:
                            break
            
            # If we don't have enough, add other meaningful sentences
            if len(specific_improvements) < 3:
                for sentence in sentences:
                    if sentence not in specific_improvements and len(sentence) > 20 and len(sentence) < 150:
                        specific_improvements.append(sentence)
                        if len(specific_improvements) >= 5:
                            break
            
            step_times['gemini_feedback'] = time.time() - step_start
            logger.info(f"✅ Generated feedback ({step_times['gemini_feedback']:.2f}s)")
        
        # Build response
        total_time = time.time() - start_time
        step_times['total'] = total_time
        
        logger.info("=" * 80)
        logger.info(f"✅ Phoneme feedback analysis complete")
        logger.info(f"⏱️  TIMING: Total={total_time:.2f}s | Transcription={step_times['transcription']:.2f}s | Phoneme={step_times['phoneme_analysis']:.2f}s | Gemini={step_times['gemini_feedback']:.2f}s")
        logger.info("=" * 80)
        
        return PhonemeFeedbackResponse(
            target_text=target_text,
            user_text=user_text,
            target_phonemes=phoneme_analysis['target_phonemes'],
            user_phonemes=phoneme_analysis['user_phonemes'],
            similarity_score=phoneme_analysis['similarity_score'],
            differences=phoneme_analysis['differences'],
            feedback=full_feedback,
            specific_improvements=specific_improvements[:5],
            confidence_score=phoneme_analysis['confidence_score']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in phoneme feedback analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze phoneme pronunciation: {str(e)}"
        )

