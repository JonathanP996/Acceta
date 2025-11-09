#!/usr/bin/env python3
"""
Test if normalization improves accuracy on Jonathan's microphone files
"""

import sys
from pathlib import Path
import requests
import json

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

ARCHIVE_DIR = Path("/Users/jsmat/gaTech/AI@GT/archive/recordings/recordings")
API_URL = "http://localhost:8000/api/detect_accent"

# Jonathan's microphone files (first 3)
JONATHAN_MIC_FILES = [
    "JonathanEnergetic.mp3",
    "JonathanMonotone.mp3",
    "JonathanMixed.mp3"
]

def test_accent_detection(file_path):
    """Test accent detection on a file"""
    try:
        with open(file_path, 'rb') as f:
            files = {'audio_file': (file_path.name, f, 'audio/mpeg')}
            response = requests.post(API_URL, files=files, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {'error': f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {'error': str(e)}

def main():
    print("=" * 80)
    print("TESTING NORMALIZATION IMPROVEMENT ON JONATHAN'S MICROPHONE FILES")
    print("=" * 80)
    print()
    
    results = []
    
    for filename in JONATHAN_MIC_FILES:
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
        
        # Check if English is in top 3
        is_english_in_top3 = any(p['accent'] == 'english' for p in top_3[:3])
        english_confidence = next((p['confidence'] for p in top_3 if p['accent'] == 'english'), 0)
        
        is_correct = predicted == 'english'
        
        results.append({
            'file': filename,
            'predicted': predicted,
            'confidence': confidence,
            'is_correct': is_correct,
            'english_in_top3': is_english_in_top3,
            'english_confidence': english_confidence,
            'top_3': top_3[:3]
        })
        
        status = "✅" if is_correct else "❌"
        print(f"  {status} Predicted: {predicted} ({confidence:.1f}%)")
        if is_english_in_top3:
            print(f"     ✓ English in top 3: {english_confidence:.1f}%")
        top3_str = ', '.join([f"{p['accent']} ({p['confidence']:.1f}%)" for p in top_3[:3]])
        print(f"     Top 3: {top3_str}")
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if results:
        correct = sum(1 for r in results if r['is_correct'])
        english_in_top3_count = sum(1 for r in results if r['english_in_top3'])
        avg_confidence = sum(r['confidence'] for r in results) / len(results)
        avg_english_confidence = sum(r['english_confidence'] for r in results if r['english_confidence'] > 0) / max(1, english_in_top3_count)
        
        print(f"Files tested: {len(results)}")
        print(f"Correct predictions (English): {correct}/{len(results)} ({100*correct/len(results):.1f}%)")
        print(f"English in top 3: {english_in_top3_count}/{len(results)} ({100*english_in_top3_count/len(results):.1f}%)")
        print(f"Average confidence: {avg_confidence:.1f}%")
        if english_in_top3_count > 0:
            print(f"Average English confidence (when in top 3): {avg_english_confidence:.1f}%")
        
        # Save results
        output_file = Path(__file__).parent / "normalization_test_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n✅ Results saved to: {output_file}")
    else:
        print("No results to summarize")

if __name__ == "__main__":
    main()

