#!/usr/bin/env python3
"""
Test Malayalam audio through microphone simulation
"""

import sys
from pathlib import Path
import requests
import json

ARCHIVE_DIR = Path("/Users/jsmat/gaTech/AI@GT/archive/recordings/recordings")
API_URL = "http://localhost:8000/api/detect_accent"

# Test Malayalam files
MALAYALAM_FILES = [
    "malayalam1.mp3",
    "malayalam2.mp3",
    "malayalam3.mp3",
    "malayalam4.mp3",
    "malayalam5.mp3",
]

def test_accent_detection(file_path):
    """Test accent detection on a file"""
    try:
        with open(file_path, 'rb') as f:
            # Simulate microphone recording
            files = {'audio_file': ('recording.wav', f, 'audio/wav')}
            response = requests.post(API_URL, files=files, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {'error': f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {'error': str(e)}

def main():
    print("=" * 80)
    print("TESTING MALAYALAM THROUGH MICROPHONE SIMULATION")
    print("=" * 80)
    print()
    
    results = []
    
    for filename in MALAYALAM_FILES:
        file_path = ARCHIVE_DIR / filename
        if not file_path.exists():
            print(f"⚠️  {filename} not found, skipping...")
            continue
        
        print(f"Testing {filename}...")
        result = test_accent_detection(file_path)
        
        if 'error' in result:
            print(f"  ❌ Error: {result['error']}")
            continue
        
        predicted = result.get('predicted_accent', 'unknown')
        confidence = result.get('confidence', 0)
        top_3 = result.get('top_predictions', [])
        
        is_correct = predicted.lower() == 'malayalam'
        is_english = predicted.lower() == 'english'
        
        results.append({
            'file': filename,
            'predicted': predicted,
            'confidence': confidence,
            'is_correct': is_correct,
            'is_english': is_english,
            'top_3': top_3[:3]
        })
        
        status = "✅" if is_correct else ("❌" if is_english else "⚠️")
        print(f"  {status} Predicted: {predicted} ({confidence:.1f}%)")
        top3_str = ', '.join([f"{p['accent']} ({p['confidence']:.1f}%)" for p in top_3[:3]])
        print(f"     Top 3: {top3_str}")
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if results:
        correct = sum(1 for r in results if r['is_correct'])
        english_count = sum(1 for r in results if r['is_english'])
        
        print(f"Files tested: {len(results)}")
        print(f"Correct predictions (Malayalam): {correct}/{len(results)} ({100*correct/len(results):.1f}%)")
        print(f"Predicted as English: {english_count}/{len(results)} ({100*english_count/len(results):.1f}%)")
        
        if english_count == len(results):
            print("\n⚠️  WARNING: All files predicted as English!")
            print("   This suggests the model is not recognizing Malayalam through microphone.")
        
        # Save results
        output_file = Path(__file__).parent / "malayalam_mic_test.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n✅ Results saved to: {output_file}")

if __name__ == "__main__":
    main()

