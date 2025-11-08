"""Test Gemini API connection and list available models"""
import os
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env file
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"Loaded .env from: {env_path}")
else:
    load_dotenv()
    print("Using default .env loading")

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("ERROR: GOOGLE_API_KEY not found in environment")
    exit(1)

print(f"API Key found: {api_key[:10]}...{api_key[-5:] if len(api_key) > 15 else '***'}")

try:
    genai.configure(api_key=api_key)
    print("\n[OK] Gemini configured successfully")
    
    # List available models
    print("\n=== Listing Available Models ===")
    try:
        models = genai.list_models()
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                print(f"  - {model.name}")
    except Exception as e:
        print(f"Error listing models: {e}")
    
    # Try to test with a simple model
    print("\n=== Testing Model Connection ===")
    test_models = [
        "models/gemini-2.5-flash",  # Latest fast model
        "models/gemini-2.0-flash",  # Fast model
        "models/gemini-flash-latest",  # Latest flash
        "models/gemini-pro-latest",  # Latest pro
    ]
    
    for model_name in test_models:
        try:
            print(f"\nTrying: {model_name}")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Say 'hello'")
            if response and response.text:
                print(f"[SUCCESS] {model_name}")
                print(f"  Response: {response.text[:100]}")
                break
        except Exception as e:
            print(f"  [FAILED] {str(e)[:100]}")
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()

