"""
Backend Testing Script
Tests database connection and basic API functionality
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_database_connection():
    """Test MongoDB connection"""
    print("Testing MongoDB connection...")
    try:
        from db import Database
        await Database.connect()
        print("✓ MongoDB connection successful")
        
        # Test a simple query
        test_collection = Database.get_collection("test")
        result = await test_collection.insert_one({"test": "connection", "timestamp": "now"})
        print(f"✓ Test document inserted: {result.inserted_id}")
        
        await Database.disconnect()
        return True
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
        return False


async def test_services():
    """Test individual services"""
    print("\nTesting services...")
    
    # Test transcription service (mock)
    try:
        from services.transcribe import transcribe_audio
        print("✓ Transcription service imported")
    except Exception as e:
        print(f"✗ Transcription service error: {e}")
    
    # Test alignment service
    try:
        from services.align import align_phonemes
        print("✓ Alignment service imported")
    except Exception as e:
        print(f"✗ Alignment service error: {e}")
    
    # Test feature extraction
    try:
        from services.features import extract_acoustic_features
        print("✓ Feature extraction service imported")
    except Exception as e:
        print(f"✗ Feature extraction error: {e}")
    
    # Test deviation model
    try:
        from services.deviation_model import compute_phoneme_deviations
        print("✓ Deviation model imported")
    except Exception as e:
        print(f"✗ Deviation model error: {e}")
    
    # Test TTS service
    try:
        from services.tts import text_to_speech
        print("✓ TTS service imported")
    except Exception as e:
        print(f"✗ TTS service error: {e}")
    
    # Test agent client
    try:
        from services.agent_client import call_accent_agent
        print("✓ Agent client imported")
    except Exception as e:
        print(f"✗ Agent client error: {e}")


def test_environment_variables():
    """Check if required environment variables are set"""
    print("\nChecking environment variables...")
    
    required_vars = [
        "MONGODB_URI",
        "GOOGLE_API_KEY",
    ]
    
    optional_vars = [
        "ELEVENLABS_API_KEY",
        "OPENAI_API_KEY",
        "VERTEX_PROJECT_ID",
    ]
    
    all_set = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✓ {var}: {'*' * min(20, len(value))}")
        else:
            print(f"✗ {var}: NOT SET (required)")
            all_set = False
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✓ {var}: {'*' * min(20, len(value))}")
        else:
            print(f"⚠ {var}: NOT SET (optional)")
    
    return all_set


async def test_agent():
    """Test the accent agent"""
    print("\nTesting AccentCoach agent...")
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "agent"))
        from accent_agent import run_accent_agent
        
        # Test data
        test_data = {
            "user_id": "test_user_123",
            "session_id": "test_session_001",
            "language": "English",
            "target_accent": "American",
            "phoneme_deviations": {
                "r": 0.72,
                "th": 0.65,
                "t": 0.15,
                "a": 0.90
            },
            "acoustic_features": {
                "mfcc_mean": [0.32, -0.12, 0.11],
                "pitch_contour": [200.0, 210.0, 205.0],
                "formant_ratios": [0.5, 1.0, 1.5]
            },
            "transcribed_text": "The quick brown fox jumps over the lazy dog",
            "user_history": {}
        }
        
        result = await run_accent_agent(test_data)
        print(f"✓ Agent executed successfully")
        print(f"  Accent Score: {result.get('accent_score', 'N/A')}")
        print(f"  Strengths: {len(result.get('strengths', []))} items")
        print(f"  Weaknesses: {len(result.get('weaknesses', []))} items")
        print(f"  Exercises: {len(result.get('personalized_exercises', []))} items")
        return True
    except Exception as e:
        print(f"✗ Agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Accenta Backend Testing")
    print("=" * 60)
    
    # Test environment variables
    env_ok = test_environment_variables()
    
    # Test database connection
    if env_ok:
        db_ok = await test_database_connection()
    else:
        print("\n⚠ Skipping database test (missing required env vars)")
        db_ok = False
    
    # Test services
    await test_services()
    
    # Test agent
    agent_ok = await test_agent()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Environment Variables: {'✓' if env_ok else '✗'}")
    print(f"Database Connection: {'✓' if db_ok else '✗'}")
    print(f"Agent: {'✓' if agent_ok else '✗'}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

