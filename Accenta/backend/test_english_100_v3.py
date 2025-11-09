"""
Test the newly retrained model on 100 English audio files
"""

import os
import sys
import re
import requests
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

# Find archive directory
archive_paths = [
    '../../archive/recordings/recordings',
    '../archive/recordings/recordings',
    '/Users/jsmat/gaTech/AI@GT/archive/recordings/recordings'
]

ARCHIVE_DIR = None
for path in archive_paths:
    if os.path.exists(path):
        ARCHIVE_DIR = path
        break

if not ARCHIVE_DIR:
    print("❌ Archive directory not found!")
    sys.exit(1)

print(f"📂 Using archive: {ARCHIVE_DIR}")

# Find all English MP3 files
all_files = [f for f in os.listdir(ARCHIVE_DIR) if f.endswith('.mp3')]
english_files = [f for f in all_files if re.match(r'^english\d+\.mp3$', f, re.IGNORECASE)]

print(f"Found {len(english_files)} English MP3 files")

if len(english_files) < 100:
    print(f"⚠️  Only {len(english_files)} English files found, testing all of them")
    test_files = english_files
else:
    # Take first 100
    test_files = sorted(english_files)[:100]
    print(f"Testing first 100 English files")

# Test each file
API_URL = "http://localhost:8000/api/detect_accent"

correct = 0
incorrect = 0
results = []

print(f"\n🧪 Testing {len(test_files)} English files...\n")

for i, filename in enumerate(test_files, 1):
    file_path = os.path.join(ARCHIVE_DIR, filename)
    
    try:
        with open(file_path, 'rb') as f:
            files = {'audio_file': (filename, f, 'audio/mpeg')}
            response = requests.post(API_URL, files=files, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            predicted = data.get('predicted_accent', 'unknown')
            confidence = data.get('confidence', 0)
            
            is_correct = predicted.lower() == 'english'
            
            if is_correct:
                correct += 1
                status = "✅"
            else:
                incorrect += 1
                status = "❌"
            
            results.append({
                'file': filename,
                'predicted': predicted,
                'confidence': confidence,
                'correct': is_correct
            })
            
            print(f"{status} [{i:3d}/{len(test_files)}] {filename:30s} -> {predicted:15s} ({confidence:5.1f}%)")
        else:
            print(f"❌ [{i:3d}/{len(test_files)}] {filename:30s} -> Error: {response.status_code}")
            incorrect += 1
            results.append({
                'file': filename,
                'predicted': 'ERROR',
                'confidence': 0,
                'correct': False
            })
    except Exception as e:
        print(f"❌ [{i:3d}/{len(test_files)}] {filename:30s} -> Exception: {str(e)}")
        incorrect += 1
        results.append({
            'file': filename,
            'predicted': 'EXCEPTION',
            'confidence': 0,
            'correct': False
        })

# Summary
print(f"\n{'='*70}")
print(f"📊 Test Results Summary")
print(f"{'='*70}")
print(f"Total tested: {len(test_files)}")
print(f"✅ Correct (English): {correct}")
print(f"❌ Incorrect: {incorrect}")
print(f"📈 Accuracy: {correct/len(test_files)*100:.2f}%")
print(f"{'='*70}")

# Show incorrect predictions
if incorrect > 0:
    print(f"\n❌ Incorrect Predictions ({incorrect}):")
    print(f"{'='*70}")
    for result in results:
        if not result['correct']:
            print(f"  {result['file']:30s} -> {result['predicted']:15s} ({result['confidence']:5.1f}%)")

# Confidence statistics
confidences = [r['confidence'] for r in results if r['correct']]
if confidences:
    print(f"\n📊 Confidence Statistics (for correct predictions):")
    print(f"  Average: {sum(confidences)/len(confidences):.2f}%")
    print(f"  Min: {min(confidences):.2f}%")
    print(f"  Max: {max(confidences):.2f}%")

