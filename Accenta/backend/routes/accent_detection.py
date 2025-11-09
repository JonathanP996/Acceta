"""
Accent Detection Routes
FastAPI endpoints for accent detection from audio
"""

import logging
import tempfile
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Lazy import - only import when needed to avoid blocking server startup
# if TensorFlow is not installed
AccentDetector = None

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter(prefix="/api", tags=["accent-detection"])

# Initialize accent detector (singleton pattern - load once)
_detector_instance = None

def _import_accent_detector():
    """Lazy import of AccentDetector to avoid blocking server startup"""
    global AccentDetector
    if AccentDetector is None:
        try:
            from services.accent_detector import AccentDetector as AD
            AccentDetector = AD
        except ImportError as e:
            logger.error(f"Failed to import AccentDetector: {e}")
            logger.error("TensorFlow may not be installed. Install with: pip install tensorflow")
            raise
    return AccentDetector

def get_detector():
    """Get or create accent detector instance (lazy loading)"""
    global _detector_instance
    if _detector_instance is None:
        try:
            # Import only when needed
            AccentDetectorClass = _import_accent_detector()
            logger.info("Initializing accent detector...")
            _detector_instance = AccentDetectorClass()
            logger.info("✅ Accent detector initialized successfully")
        except ImportError as e:
            logger.error(f"❌ Failed to import accent detector: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Accent detection service unavailable: TensorFlow not installed. Please install with: pip install tensorflow"
            )
        except Exception as e:
            logger.error(f"❌ Failed to initialize accent detector: {e}", exc_info=True)
            _detector_instance = None  # Reset to allow retry
            raise HTTPException(
                status_code=503,
                detail=f"Accent detection service unavailable: {str(e)}"
            )
    return _detector_instance


@router.post("/detect_accent")
async def detect_accent(
    audio_file: UploadFile = File(...)
):
    """
    Detect accent from audio recording.
    
    Args:
        audio_file: Audio file (wav, mp3, webm, ogg, etc.)
    
    Returns:
        JSON with predicted accent, confidence, and top N predictions
    """
    try:
        logger.info(f"Received accent detection request: {audio_file.filename}")
        
        # Get detector instance
        detector = get_detector()
        
        # Read audio file
        audio_bytes = await audio_file.read()
        
        # Determine file extension from filename or content type
        # CRITICAL: Check content-type FIRST for browser recordings (WebM converted to WAV)
        # Browser sends WAV but it's actually converted from WebM, so we need to detect this
        content_type = audio_file.content_type or ''
        file_extension = os.path.splitext(audio_file.filename or 'audio.wav')[1]
        
        # Priority: content-type > filename (for browser recordings)
        if 'webm' in content_type.lower():
            file_extension = '.webm'
            logger.info("Detected WebM from content-type (browser recording)")
        elif 'ogg' in content_type.lower() or 'opus' in content_type.lower():
            file_extension = '.ogg'
            logger.info("Detected OGG/Opus from content-type (browser recording)")
        elif not file_extension or file_extension == '':
            # Fallback to content-type if no filename extension
            if 'wav' in content_type.lower():
                file_extension = '.wav'
            elif 'mp3' in content_type.lower():
                file_extension = '.mp3'
            else:
                # Default to wav if no extension
                file_extension = '.wav'
        # If filename has extension but content-type suggests browser recording, 
        # check if it's a converted file (recording.wav from browser = likely WebM source)
        elif file_extension == '.wav' and ('recording.wav' in (audio_file.filename or '') or len(audio_bytes) < 100000):
            # Small WAV files or files named "recording.wav" are likely browser recordings
            # Treat as WebM for better resampling quality
            file_extension = '.webm'
            logger.info(f"Detected browser recording (WAV converted from WebM): {audio_file.filename}")
        
        # Use predict_from_bytes method
        result = detector.predict_from_bytes(audio_bytes, file_extension=file_extension)
        
        logger.info(f"Accent detection result: {result['accent']} ({result['confidence']:.2f}%)")
        
        # English-specific confidence threshold (higher bar for English)
        ENGLISH_CONFIDENCE_THRESHOLD = 60.0  # English needs higher confidence
        GENERAL_CONFIDENCE_THRESHOLD = 50.0  # General threshold for other languages
        
        # Determine if prediction is uncertain
        if result['accent'] == 'english':
            # English requires higher confidence threshold
            is_uncertain = result['confidence'] < ENGLISH_CONFIDENCE_THRESHOLD
            confidence_threshold = ENGLISH_CONFIDENCE_THRESHOLD
        else:
            # Other languages use general threshold
            is_uncertain = result['confidence'] < GENERAL_CONFIDENCE_THRESHOLD
            confidence_threshold = GENERAL_CONFIDENCE_THRESHOLD
        
        # If confidence is very low, consider the top 2-3 predictions
        if is_uncertain and len(result['top_n']) > 1:
            # Check if top 2 predictions are close
            top_confidence = result['top_n'][0]['confidence']
            second_confidence = result['top_n'][1]['confidence'] if len(result['top_n']) > 1 else 0
            confidence_diff = top_confidence - second_confidence
            
            # If the difference is small (< 15% for English, < 10% for others), the model is uncertain
            diff_threshold = 15.0 if result['accent'] == 'english' else 10.0
            if confidence_diff < diff_threshold:
                logger.warning(f"Low confidence prediction: {result['accent']} ({result['confidence']:.2f}%) vs {result['top_n'][1]['accent']} ({second_confidence:.2f}%)")
        
        return JSONResponse({
            "success": True,
            "predicted_accent": result['accent'],
            "confidence": result['confidence'],
            "top_predictions": result['top_n'],
            "all_predictions": result['top_n'],  # For frontend display
            "is_uncertain": is_uncertain,  # Flag for low confidence
            "confidence_threshold": confidence_threshold
        })
        
    except FileNotFoundError as e:
        logger.error(f"Model file not found: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Accent detection model not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Accent detection failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Accent detection failed: {str(e)}"
        )


@router.get("/accent_detection/status")
async def accent_detection_status():
    """Check if accent detection model is loaded and ready"""
    try:
        detector = get_detector()
        supported_classes = detector.get_supported_classes()
        return {
            "status": "ready",
            "supported_accents": supported_classes,
            "model_loaded": detector.model is not None,
            "encoder_loaded": detector.label_encoder is not None
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "supported_accents": [],
            "model_loaded": False,
            "encoder_loaded": False
        }

