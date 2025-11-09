#!/usr/bin/env python3
"""
Test English accent evaluation score calculation
Tests 100 English files and shows:
- Predicted accent
- English confidence (from top predictions)
- Calculated accent evaluation score
- Whether the evaluation score makes sense
"""

import os
import sys
import re
import requests
from pathlib import Path
from collections import defaultdict

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

results = []
print(f"\n🧪 Testing {len(test_files)} English files with evaluation score calculation...\n")

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
            top_predictions = data.get('top_predictions', [])
            
            # Find English confidence from top predictions or predicted accent
            english_confidence = 0
            if predicted and 'english' in predicted.lower():
                english_confidence = confidence
            elif top_predictions:
                for pred in top_predictions:
                    accent_name = pred.get('accent', '')
                    if accent_name and 'english' in accent_name.lower():
                        english_confidence = pred.get('confidence', 0)
                        break
            
            # Calculate accent evaluation score (for English target: higher English confidence = better)
            # Since target is English, score = english_confidence
            evaluation_score = english_confidence
            
            is_correct = predicted.lower() == 'english'
            
            results.append({
                'file': filename,
                'predicted': predicted,
                'confidence': confidence,
                'english_confidence': english_confidence,
                'evaluation_score': evaluation_score,
                'correct': is_correct,
                'top_predictions': top_predictions
            })
            
            # Show status
            status = "✅" if is_correct else "❌"
            print(f"{status} [{i:3d}/{len(test_files)}] {filename:30s} | Predicted: {predicted:12s} ({confidence:5.1f}%) | English Conf: {english_confidence:5.1f}% | Eval Score: {evaluation_score:5.1f}%")
        else:
            print(f"❌ [{i:3d}/{len(test_files)}] {filename:30s} -> Error: {response.status_code}")
            results.append({
                'file': filename,
                'predicted': 'ERROR',
                'confidence': 0,
                'english_confidence': 0,
                'evaluation_score': 0,
                'correct': False
            })
    except Exception as e:
        print(f"❌ [{i:3d}/{len(test_files)}] {filename:30s} -> Exception: {str(e)}")
        results.append({
            'file': filename,
            'predicted': 'EXCEPTION',
            'confidence': 0,
            'english_confidence': 0,
            'evaluation_score': 0,
            'correct': False
        })

# Summary
print(f"\n{'='*100}")
print(f"📊 Test Results Summary")
print(f"{'='*100}")

correct = sum(1 for r in results if r['correct'])
incorrect = len(results) - correct

print(f"Total tested: {len(test_files)}")
print(f"✅ Correct (English): {correct}")
print(f"❌ Incorrect: {incorrect}")
print(f"📈 Accuracy: {correct/len(test_files)*100:.2f}%")

# Evaluation score statistics
eval_scores = [r['evaluation_score'] for r in results if r['evaluation_score'] > 0]
english_confs = [r['english_confidence'] for r in results if r['english_confidence'] > 0]

if eval_scores:
    print(f"\n📊 Accent Evaluation Score Statistics:")
    print(f"  Average: {sum(eval_scores)/len(eval_scores):.2f}%")
    print(f"  Min: {min(eval_scores):.2f}%")
    print(f"  Max: {max(eval_scores):.2f}%")
    print(f"  Median: {sorted(eval_scores)[len(eval_scores)//2]:.2f}%")

if english_confs:
    print(f"\n📊 English Confidence Statistics:")
    print(f"  Average: {sum(english_confs)/len(english_confs):.2f}%")
    print(f"  Min: {min(english_confs):.2f}%")
    print(f"  Max: {max(english_confs):.2f}%")
    print(f"  Median: {sorted(english_confs)[len(english_confs)//2]:.2f}%")

# Group by evaluation score ranges
score_ranges = {
    'Excellent (80-100%)': 0,
    'Good (60-79%)': 0,
    'Needs Improvement (40-59%)': 0,
    'Poor (<40%)': 0
}

for r in results:
    score = r['evaluation_score']
    if score >= 80:
        score_ranges['Excellent (80-100%)'] += 1
    elif score >= 60:
        score_ranges['Good (60-79%)'] += 1
    elif score >= 40:
        score_ranges['Needs Improvement (40-59%)'] += 1
    else:
        score_ranges['Poor (<40%)'] += 1

print(f"\n📊 Evaluation Score Distribution:")
for range_name, count in score_ranges.items():
    percentage = (count / len(results)) * 100
    print(f"  {range_name:30s}: {count:3d} files ({percentage:5.1f}%)")

# Show files with low evaluation scores (these would get poor accent replication scores)
print(f"\n⚠️  Files with Low Evaluation Scores (<60%):")
print(f"{'='*100}")
low_score_files = [r for r in results if r['evaluation_score'] < 60]
for r in sorted(low_score_files, key=lambda x: x['evaluation_score']):
    print(f"  {r['file']:30s} | Eval: {r['evaluation_score']:5.1f}% | English Conf: {r['english_confidence']:5.1f}% | Predicted: {r['predicted']:12s}")

# Show incorrect predictions with their English confidence
print(f"\n❌ Incorrect Predictions Analysis:")
print(f"{'='*100}")
incorrect_results = [r for r in results if not r['correct']]
for r in incorrect_results:
    print(f"  {r['file']:30s} | Predicted: {r['predicted']:12s} ({r['confidence']:5.1f}%) | English Conf: {r['english_confidence']:5.1f}% | Eval Score: {r['evaluation_score']:5.1f}%")
    if r.get('top_predictions'):
        print(f"    Top 3: ", end="")
        for pred in r['top_predictions'][:3]:
            print(f"{pred.get('accent', 'unknown')} ({pred.get('confidence', 0):.1f}%)", end=", ")
        print()

print(f"\n{'='*100}")

