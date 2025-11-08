"""
Live Chat Routes
AI conversation endpoint for live chat mode
"""

import logging
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import google.generativeai as genai
import os

from services.tts import text_to_speech

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Initialize Gemini for conversational AI
GEMINI_AVAILABLE = False
GEMINI_STATUS = "not_configured"
GEMINI_ERROR = None

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
                test_model = genai.GenerativeModel("gemini-1.5-flash")
                test_response = test_model.generate_content("Say 'connected' if you can read this.")
                if test_response and test_response.text:
                    GEMINI_AVAILABLE = True
                    GEMINI_STATUS = "connected"
                    logger.info("✓ Gemini API connected and working")
                else:
                    GEMINI_AVAILABLE = False
                    GEMINI_STATUS = "connection_failed"
                    logger.warning("Gemini API key configured but test failed")
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
    # Handle initial greeting - let Gemini generate it dynamically
    if not user_message or user_message.strip() == "":
        # Use Gemini to generate a natural greeting
        if GEMINI_AVAILABLE:
            try:
                greeting_prompt = f"""You are Wally, a warm, friendly AI language coach. Generate a brief, natural greeting for a student practicing their {target_accent} accent. Keep it short (1-2 sentences), friendly, and ask them what they're passionate about. Don't be overly excited or use exclamation marks excessively."""
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(greeting_prompt)
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                logger.error(f"Failed to generate greeting with Gemini: {e}")
        
        # Simple fallback if Gemini fails
        return f"Hi! I'm Wally. I'm here to help you practice your {target_accent} accent. What are you passionate about?"
    
    # Build conversation context
    history_text = ""
    if conversation_history:
        for msg in conversation_history[-5:]:  # Last 5 messages for context
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_text += f"{role.capitalize()}: {content}\n"
    
    # Create system prompt for friendly conversation
    system_prompt = f"""You are Wally, a warm, friendly, and supportive AI language coach having a natural conversation with a student practicing their {target_accent} accent.

Your name is Wally. Always refer to yourself as Wally in conversations.

Your personality:
- Very friendly, warm, and genuinely interested in the student's personal life
- Ask follow-up questions to keep the conversation flowing naturally
- Show genuine curiosity about their experiences, hobbies, interests, and daily life
- Be conversational and natural, not robotic or formal
- Use a warm, encouraging tone
- Be enthusiastic and supportive

The student just said: "{user_message}"
"""
    
    # Add pronunciation feedback if available
    if pronunciation_score is not None:
        if pronunciation_score >= 80:
            system_prompt += f"\nTheir pronunciation was excellent ({pronunciation_score:.1f}%)! Give them positive reinforcement while continuing the conversation naturally."
        elif pronunciation_score >= 60:
            system_prompt += f"\nTheir pronunciation was good ({pronunciation_score:.1f}%)! Give them encouragement and continue the conversation."
        else:
            system_prompt += f"\nTheir pronunciation needs work ({pronunciation_score:.1f}%). Give them supportive, gentle feedback with one specific tip, then continue the conversation naturally."
    
    if struggle_areas:
        system_prompt += f"\nThey struggle with: {', '.join(struggle_areas)}. You can mention this gently if relevant."
    
    system_prompt += "\n\nRespond naturally as if continuing a friendly conversation. Ask a follow-up question or share something related to what they said. Keep it warm, engaging, and conversational. Don't be overly formal or robotic."
    
    # Use Gemini if available - use cheaper/faster model
    if GEMINI_AVAILABLE:
        try:
            # Use gemini-1.5-flash for faster, cheaper responses
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            # Build full prompt
            full_prompt = f"{system_prompt}\n\nConversation history:\n{history_text}\n\nYour response:"
            
            # Use faster generation config
            generation_config = {
                "temperature": 0.7,  # Balanced creativity
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": 200,  # Keep responses concise for speed
            }
            
            response = model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            # Fall through to fallback
    
    # Fallback: Generate friendly response
    return generate_fallback_response(user_message, pronunciation_score)


def generate_fallback_response(user_message: str, pronunciation_score: Optional[float] = None) -> str:
    """Generate a friendly fallback response"""
    responses = [
        f"That's really interesting! I'd love to hear more about that. {get_pronunciation_comment(pronunciation_score)} What got you interested in that?",
        f"Oh, that sounds fascinating! {get_pronunciation_comment(pronunciation_score)} Tell me more - I'm genuinely curious!",
        f"I love hearing about that! {get_pronunciation_comment(pronunciation_score)} What's the most challenging part about it?",
        f"That's so cool! {get_pronunciation_comment(pronunciation_score)} How long have you been doing that?",
        f"Wow, that's wonderful! {get_pronunciation_comment(pronunciation_score)} What's something you've learned from that experience?",
    ]
    
    import random
    return random.choice(responses)


def get_pronunciation_comment(score: Optional[float]) -> str:
    """Get a pronunciation comment based on score"""
    if score is None:
        return ""
    if score >= 80:
        return "Your pronunciation is really coming along nicely, by the way!"
    elif score >= 60:
        return "You're doing great with your pronunciation!"
    else:
        return "Keep practicing - you're making progress!"


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
                pronunciation_feedback = f"Try focusing on the '{request.struggle_areas[0]}' sound - you're doing great overall!"
            else:
                pronunciation_feedback = "Keep practicing - you're making progress!"
        
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
        logger.error(f"Chat with audio generation failed: {e}")
        # Return response even if there's an error, so frontend can handle it
        return {
            "ai_message": "I'm having trouble right now, but I'm here to help! - Wally",
            "pronunciation_feedback": None,
            "audio_base64": None,
        }


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

