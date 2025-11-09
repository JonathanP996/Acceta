#!/usr/bin/env python3
"""
Test what format the microphone recording actually is when received
"""

import sys
from pathlib import Path
import requests
import tempfile
import os

ARCHIVE_DIR = Path("/Users/jsmat/gaTech/AI@GT/archive/recordings/recordings")
API_URL = "http://localhost:8000/api/detect_accent"

# Test with a real file to see what format it's processed as
TEST_FILE = ARCHIVE_DIR / "english1.mp3"

def test_format_detection():
    """Test what format the backend detects"""
    print("=" * 80)
    print("TESTING FORMAT DETECTION")
    print("=" * 80)
    print()
    
    # Read the file
    with open(TEST_FILE, 'rb') as f:
        audio_bytes = f.read()
    
    # Test 1: Send as recording.wav (simulating microphone)
    print("Test 1: Sending as 'recording.wav' (microphone simulation)...")
    files = {'audio_file': ('recording.wav', audio_bytes, 'audio/wav')}
    response = requests.post(API_URL, files=files, timeout=30)
    if response.status_code == 200:
        result = response.json()
        print(f"  ✅ Predicted: {result.get('predicted_accent')} ({result.get('confidence', 0):.1f}%)")
    else:
        print(f"  ❌ Error: {response.status_code}")
    print()
    
    # Test 2: Send as recording.webm (simulating browser recording)
    print("Test 2: Sending as 'recording.webm' (browser recording)...")
    files = {'audio_file': ('recording.webm', audio_bytes, 'audio/webm')}
    response = requests.post(API_URL, files=files, timeout=30)
    if response.status_code == 200:
        result = response.json()
        print(f"  ✅ Predicted: {result.get('predicted_accent')} ({result.get('confidence', 0):.1f}%)")
    else:
        print(f"  ❌ Error: {response.status_code}")
    print()
    
    # Test 3: Send as regular file upload
    print("Test 3: Sending as regular file 'english1.mp3'...")
    files = {'audio_file': ('english1.mp3', audio_bytes, 'audio/mpeg')}
    response = requests.post(API_URL, files=files, timeout=30)
    if response.status_code == 200:
        result = response.json()
        print(f"  ✅ Predicted: {result.get('predicted_accent')} ({result.get('confidence', 0):.1f}%)")
    else:
        print(f"  ❌ Error: {response.status_code}")
    print()

if __name__ == "__main__":
    test_format_detection()

