#!/usr/bin/env python3
"""
Test if normalization is causing all microphone input to be classified as English
"""

import sys
from pathlib import Path
import requests
import json

ARCHIVE_DIR = Path("/Users/jsmat/gaTech/AI@GT/archive/recordings/recordings")
API_URL = "http://localhost:8000/api/detect_accent"

# Test files - mix of English and non-English
TEST_FILES = [
    ("english1.mp3", "english"),
    ("mandarin1.mp3", "mandarin"),
    ("japanese1.mp3", "japanese"),
    ("german1.mp3", "german"),
    ("hindi1.mp3", "hindi"),
]

def test_accent_detection(file_path, expected_accent):
    """Test accent detection on a file"""
    try:
        with open(file_path, 'rb') as f:
            # Simulate microphone recording by using 'recording.wav' filename
            files = {'audio_file': ('recording.wav', f, 'audio/wav')}
            response = requests.post(API_URL, files=files, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return {
                'file': file_path.name,
                'expected': expected_accent,
                'predicted': result.get('predicted_accent', 'unknown'),
                'confidence': result.get('confidence', 0),
                'top_3': result.get('top_predictions', [])[:3],
                'is_correct': result.get('predicted_accent', '').lower() == expected_accent.lower()
            }
        else:
            return {'error': f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {'error': str(e)}

def main():
    print("=" * 80)
    print("TESTING NORMALIZATION ISSUE - All inputs classified as English?")
    print("=" * 80)
    print()
    print("Testing with microphone simulation (recording.wav filename)...")
    print()
    
    results = []
    
    for filename, expected in TEST_FILES:
        file_path = ARCHIVE_DIR / filename
        if not file_path.exists():
            print(f"⚠️  {filename} not found, skipping...")
            continue
        
        print(f"Testing {filename} (expected: {expected})...")
        result = test_accent_detection(file_path, expected)
        
        if 'error' in result:
            print(f"  ❌ Error: {result['error']}")
            continue
        
        status = "✅" if result['is_correct'] else "❌"
        print(f"  {status} Predicted: {result['predicted']} ({result['confidence']:.1f}%)")
        top3_str = ', '.join([f"{p['accent']} ({p['confidence']:.1f}%)" for p in result['top_3']])
        print(f"     Top 3: {top3_str}")
        print()
        
        results.append(result)
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if results:
        english_count = sum(1 for r in results if r['predicted'].lower() == 'english')
        correct_count = sum(1 for r in results if r['is_correct'])
        
        print(f"Files tested: {len(results)}")
        print(f"Predicted as English: {english_count}/{len(results)} ({100*english_count/len(results):.1f}%)")
        print(f"Correct predictions: {correct_count}/{len(results)} ({100*correct_count/len(results):.1f}%)")
        
        if english_count == len(results):
            print("\n⚠️  WARNING: All files predicted as English!")
            print("   This suggests normalization is too aggressive or incorrectly applied.")
        
        # Save results
        output_file = Path(__file__).parent / "normalization_issue_test.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n✅ Results saved to: {output_file}")

if __name__ == "__main__":
    main()

