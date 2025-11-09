#!/usr/bin/env python3
"""
Test script to check if Gemini API is working
"""

import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
    load_dotenv()

print("=" * 80)
print("Testing Gemini API Connection")
print("=" * 80)

# Check for API key
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("OPENAI_API_KEY")
print(f"\n1. API Key Check:")
print(f"   GOOGLE_API_KEY: {'Present' if os.getenv('GOOGLE_API_KEY') else 'Not found'}")
print(f"   OPENAI_API_KEY: {'Present' if os.getenv('OPENAI_API_KEY') else 'Not found'}")
print(f"   Using key: {'Yes' if api_key else 'No'}")

if not api_key or api_key == "YOUR_GOOGLE_API_KEY_HERE" or not api_key.strip():
    print("\n❌ ERROR: No valid API key found!")
    print("   Please set GOOGLE_API_KEY or OPENAI_API_KEY in your .env file")
    sys.exit(1)

print(f"   Key length: {len(api_key)} characters")
print(f"   Key starts with: {api_key[:10]}...")

# Configure Gemini
print(f"\n2. Configuring Gemini...")
try:
    genai.configure(api_key=api_key)
    print("   ✓ Configuration successful")
except Exception as e:
    print(f"   ❌ Configuration failed: {e}")
    sys.exit(1)

# Test models
print(f"\n3. Testing Gemini Models:")
model_names = [
    "models/gemini-2.5-flash",
    "models/gemini-2.0-flash",
    "models/gemini-flash-latest",
    "models/gemini-1.5-flash",
    "models/gemini-pro-latest",
]

success = False
for model_name in model_names:
    print(f"\n   Testing {model_name}...")
    try:
        model = genai.GenerativeModel(model_name)
        print(f"      ✓ Model created")
        
        # Try a simple test
        print(f"      Sending test prompt...")
        response = model.generate_content("Say 'connected' if you can read this.")
        
        if response and response.text:
            print(f"      ✓ Response received: {response.text[:50]}...")
            print(f"\n✅ SUCCESS! Gemini API is working with {model_name}")
            success = True
            break
        else:
            print(f"      ❌ Empty response")
    except Exception as e:
        error_msg = str(e)
        print(f"      ❌ Error: {error_msg[:200]}")
        if "quota" in error_msg.lower() or "limit" in error_msg.lower():
            print(f"      ⚠️  This looks like a quota/limit issue")
        elif "permission" in error_msg.lower() or "unauthorized" in error_msg.lower():
            print(f"      ⚠️  This looks like an authentication issue")
        elif "api key" in error_msg.lower():
            print(f"      ⚠️  This looks like an API key issue")
        continue

if not success:
    print(f"\n❌ FAILED: None of the models worked")
    print(f"\nTroubleshooting:")
    print(f"   1. Check your API key is valid at: https://aistudio.google.com/apikey")
    print(f"   2. Ensure the API key has proper permissions")
    print(f"   3. Check if you've exceeded quota/rate limits")
    print(f"   4. Verify network connectivity")
    sys.exit(1)

print("\n" + "=" * 80)
