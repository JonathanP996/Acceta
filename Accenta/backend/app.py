import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from db import Database

# Load environment variables
load_dotenv()

# Configure logging - ensure INFO level and format
# Set DEBUG level for routes.chat to see detailed conversation logs
import sys
from pathlib import Path

# Create logs directory if it doesn't exist
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

# Log file path
log_file = log_dir / "backend.log"

# Configure logging with both file and console handlers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
# Enable DEBUG logging for chat routes to see full prompts and responses
logging.getLogger('routes.chat').setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)
logger.info(f"Logging to file: {log_file}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Accenta backend...")
    try:
        await Database.connect()
        logger.info("✓ Database connected")
    except Exception as e:
        logger.warning(f"Database connection failed (continuing anyway): {e}")
        # Don't raise - allow app to start without DB for testing
        # Set client to None explicitly to avoid truth value testing errors
        Database.client = None
        Database.db = None
    
    yield
    
    # Shutdown
    logger.info("Shutting down Accenta backend...")
    await Database.disconnect()
    logger.info("✓ Database disconnected")


# Create FastAPI app
app = FastAPI(
    title="Accenta API",
    description="AI-powered accent learning platform backend",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - MUST be added before routes
# FastAPI automatically handles OPTIONS preflight requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # In case frontend runs on different port
        "http://127.0.0.1:3001",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods including OPTIONS
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Accenta API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test database connection
        if Database.client is None:
            db_status = "not connected"
        else:
            await Database.client.admin.command('ping')
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Check Gemini status
    try:
        from routes.chat import GEMINI_AVAILABLE, GEMINI_STATUS, GEMINI_ERROR
        gemini_status = {
            "available": GEMINI_AVAILABLE,
            "status": GEMINI_STATUS,
            "error": GEMINI_ERROR
        }
    except Exception as e:
        gemini_status = {
            "available": False,
            "status": "unknown",
            "error": str(e)
        }
    
    return {
        "status": "healthy",
        "database": db_status,
        "gemini": gemini_status,
        "services": {
            "database": "MongoDB Atlas",
            "ai_agent": "Gemini" if gemini_status.get("available") else "Fallback",
            "tts": "ElevenLabs",
            "transcription": "Whisper"
        }
    }


# Import routes AFTER CORS middleware is configured
from routes import auth, practice, tts, chat, onboarding, accent_detection, phoneme_feedback

# Register routes
app.include_router(auth.router)
app.include_router(practice.router)
app.include_router(tts.router)
app.include_router(chat.router)
app.include_router(onboarding.router)  # Onboarding endpoint
app.include_router(accent_detection.router)
app.include_router(phoneme_feedback.router)  # Accent detection endpoint

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=os.getenv("FASTAPI_HOST", "0.0.0.0"),
        port=int(os.getenv("FASTAPI_PORT", 8000)),
        reload=True
    )
