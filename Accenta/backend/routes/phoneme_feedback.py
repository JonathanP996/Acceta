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
    language: Optional[str] = Form(None, description="Language code (e.g., 'en')"),
    accent_evaluation_score: Optional[float] = Form(None, description="Accent evaluation score (0-100)")
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
        
        # Always try to use Gemini - initialize if needed
        gemini_available_now = GEMINI_AVAILABLE
        gemini_model_name_now = GEMINI_MODEL_NAME
        
        # Try to initialize Gemini if not available (in case it was a transient error)
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
                                logger.warning(f"Model {model_name} quota exceeded - will try others")
                            elif "404" in error_msg:
                                logger.debug(f"Model {model_name} not found (404)")
                            else:
                                logger.warning(f"Model {model_name} failed: {error_msg[:200]}")
                            continue
                    if not gemini_available_now:
                        logger.warning(f"All {len(model_names)} Gemini models failed to initialize, but will still attempt call")
                else:
                    logger.warning("No valid API key found for Gemini initialization, but will still attempt call")
            except Exception as e:
                logger.error(f"Gemini initialization retry failed with exception: {e}", exc_info=True)
                logger.info("Will still attempt Gemini call despite initialization error")
        
        # ALWAYS attempt Gemini call first, regardless of initialization status
        # Only use fallback if the actual API call fails
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("OPENAI_API_KEY")
        gemini_call_successful = False
        full_feedback = None
        specific_improvements = []
        
        # Try Gemini call if we have an API key (even if initialization seemed to fail)
        if api_key and api_key != "YOUR_GOOGLE_API_KEY_HERE" and api_key.strip():
            logger.info("Attempting Gemini API call for feedback generation...")
            try:
                # Ensure Gemini is configured
                if not gemini_available_now:
                    try:
                        genai.configure(api_key=api_key)
                        # Try to find a working model
                        model_names = [
                            "models/gemini-2.5-flash",
                            "models/gemini-2.0-flash",
                            "models/gemini-flash-latest",
                            "models/gemini-pro-latest",
                        ]
                        for model_name in model_names:
                            try:
                                test_model = genai.GenerativeModel(model_name)
                                test_response = test_model.generate_content("test")
                                if test_response and test_response.text:
                                    gemini_model_name_now = model_name
                                    logger.info(f"✓ Found working Gemini model: {model_name}")
                                    break
                            except:
                                continue
                    except:
                        pass  # Will try anyway with default model
                
                # Build structured data for Gemini
                differences_summary = []
                for diff in phoneme_analysis['differences'][:10]:  # Limit to top 10 differences
                    differences_summary.append({
                        "phoneme": f"{diff.get('target_phonemes', '')}→{diff.get('user_phonemes', '')}",
                        "issue": diff.get('issue', ''),
                        "type": diff.get('type', 'unknown')
                    })
                
                # Create prompt for Gemini - conversational, script-like feedback for TTS
                accent_score_context = ""
                if accent_evaluation_score is not None:
                    if accent_evaluation_score >= 85:
                        accent_score_context = f"Great news! Your accent evaluation score is {accent_evaluation_score:.0f}% - that's excellent! Acknowledge this achievement, but still provide specific phoneme-level feedback to help them maintain or improve further."
                    elif accent_evaluation_score >= 70:
                        accent_score_context = f"Your accent evaluation score is {accent_evaluation_score:.0f}% - that's good progress! Acknowledge this, but provide specific advice on how to improve further."
                    elif accent_evaluation_score >= 50:
                        accent_score_context = f"Your accent evaluation score is {accent_evaluation_score:.0f}% - there's room for improvement. Address this directly and provide specific advice on how to improve your accent replication."
                    else:
                        accent_score_context = f"Your accent evaluation score is {accent_evaluation_score:.0f}% - this needs significant improvement. Address this directly and provide specific, actionable advice on how to better replicate the target accent."
                
                prompt = f"""You are a friendly pronunciation coach. The user said "{user_text}" but should have said "{target_text}".

{accent_score_context}

Analyze the differences and provide natural, conversational feedback that sounds like you're speaking directly to them. Write it as a script for text-to-speech - no markdown, just natural speech.

Your feedback should address BOTH:
1. The overall accent evaluation score (if provided) - acknowledge good work or provide encouragement for improvement
2. Specific phoneme-level word mistakes - point out exact words they mispronounced

For example, if they said "gahn" instead of "can", say: "You said 'gahn' instead of 'can'. Try saying 'can' with a clear 'k' sound at the beginning."

IMPORTANT: Even if phoneme similarity is 100%, still provide dynamic feedback based on:
- The accent evaluation score (acknowledge good work or provide improvement advice)
- Any subtle differences in pronunciation, rhythm, or accent characteristics
- Specific words or sounds that could be improved even if phonemes match

Structure your response as natural speech:
1. Start with accent evaluation acknowledgment (if score provided) - 1-2 sentences about their overall accent performance
2. Address phoneme-level details - even if similarity is high, point out any subtle differences or areas for improvement
3. Point out specific word mistakes with examples (2-4 specific corrections) - be specific about which words and sounds
4. Give 2-3 simple practice tips that address both accent replication and phoneme accuracy

Keep it encouraging, conversational, and easy to understand. Write as if you're speaking to them, not writing a document. Always provide specific, actionable feedback even when scores are high."""

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
                
                # Extract specific improvements from conversational feedback
                sentences = [s.strip() for s in full_feedback.replace('!', '.').replace('?', '.').split('.') if s.strip()]
                for sentence in sentences:
                    sentence_lower = sentence.lower()
                    if any(keyword in sentence_lower for keyword in ['instead of', 'try saying', 'practice', 'focus on', 'work on', 'sound', 'pronounce']):
                        if len(sentence) > 15 and len(sentence) < 200:
                            specific_improvements.append(sentence)
                            if len(specific_improvements) >= 5:
                                break
                
                if len(specific_improvements) < 3:
                    for sentence in sentences:
                        if sentence not in specific_improvements and len(sentence) > 20 and len(sentence) < 150:
                            specific_improvements.append(sentence)
                            if len(specific_improvements) >= 5:
                                break
                
                gemini_call_successful = True
                step_times['gemini_feedback'] = time.time() - step_start
                logger.info(f"✅ Generated Gemini feedback ({step_times['gemini_feedback']:.2f}s)")
                
            except Exception as gemini_error:
                logger.error(f"Gemini API call failed: {gemini_error}", exc_info=True)
                logger.warning("Falling back to dynamic feedback due to Gemini error")
                gemini_call_successful = False
        
        # Use fallback only if Gemini call failed
        if not gemini_call_successful:
            logger.info("Using dynamic fallback feedback generation")
            # Generate dynamic feedback from phoneme analysis and accent score
            full_feedback = ""
            
            # Address accent evaluation score if provided
            if accent_evaluation_score is not None:
                if accent_evaluation_score >= 85:
                    full_feedback += f"Great work on your accent! Your accent evaluation score is {accent_evaluation_score:.0f}%, which shows you're doing an excellent job replicating the target accent. "
                elif accent_evaluation_score >= 70:
                    full_feedback += f"Your accent evaluation score is {accent_evaluation_score:.0f}% - that's good progress! Keep working on matching the target accent more closely. "
                elif accent_evaluation_score >= 50:
                    full_feedback += f"Your accent evaluation score is {accent_evaluation_score:.0f}% - there's room for improvement in replicating the target accent. Focus on matching the accent characteristics more closely. "
                else:
                    full_feedback += f"Your accent evaluation score is {accent_evaluation_score:.0f}% - this needs significant improvement. Work on better replicating the target accent's characteristics. "
            
            # Address phoneme-level differences
            full_feedback += f"Your pronunciation of \"{target_text}\" was transcribed as \"{user_text}\". "
            
            if phoneme_analysis['similarity_score'] >= 0.95:
                full_feedback += "Your phoneme accuracy is excellent - the sounds match very closely. "
            elif phoneme_analysis['similarity_score'] >= 0.8:
                full_feedback += "Your phoneme accuracy is good, with just minor differences. "
            elif phoneme_analysis['similarity_score'] >= 0.6:
                full_feedback += "There are some phoneme differences to work on. "
            else:
                full_feedback += "There are noticeable phoneme differences that need attention. "
            
            full_feedback += f"Your phoneme similarity score is {phoneme_analysis['similarity_score']*100:.1f}%.\n\n"
            
            # Add specific phoneme differences with word-level context
            if phoneme_analysis['differences']:
                full_feedback += "**Specific Issues to Address**\n"
                for diff in phoneme_analysis['differences'][:5]:
                    target_ph = diff.get('target_phonemes', '').strip()
                    user_ph = diff.get('user_phonemes', '').strip()
                    if diff.get('type') == 'phoneme_mismatch' and target_ph and user_ph:
                        # Try to identify which word this might be from
                        full_feedback += f"You pronounced the sound '{user_ph}' instead of '{target_ph}'. "
                    elif diff.get('type') == 'missing_phoneme' and target_ph:
                        full_feedback += f"You're missing the sound '{target_ph}'. Make sure to include all the sounds in each word. "
                    elif diff.get('type') == 'extra_phoneme' and user_ph:
                        full_feedback += f"You added an extra sound '{user_ph}' that shouldn't be there. "
                full_feedback += "\n\n"
            else:
                if phoneme_analysis['similarity_score'] >= 0.95:
                    full_feedback += "Your phoneme accuracy is spot-on! All the sounds match perfectly.\n\n"
            
            # Practice recommendations removed per user request
            
            # Extract improvements from differences
            specific_improvements = []
            for diff in phoneme_analysis['differences'][:5]:
                if diff.get('issue'):
                    specific_improvements.append(diff.get('issue'))
            
            if len(specific_improvements) == 0:
                if accent_evaluation_score is not None and accent_evaluation_score < 85:
                    specific_improvements.append(f"Work on improving your accent evaluation score from {accent_evaluation_score:.0f}% to 85%+")
                if phoneme_analysis['similarity_score'] < 0.95:
                    specific_improvements.append("Focus on matching the exact phonemes in each word")
                specific_improvements.append("Listen carefully to the reference pronunciation and practice matching it")
            
            step_times['gemini_feedback'] = time.time() - step_start
            logger.info(f"✅ Generated dynamic fallback feedback ({step_times['gemini_feedback']:.2f}s)")
        
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

