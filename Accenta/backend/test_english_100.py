#!/usr/bin/env python3
"""
Test script for English accent detection - 100 files
"""

import os
import sys
import json
from pathlib import Path
import requests
from collections import defaultdict

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Base URL for the API
API_BASE_URL = "http://localhost:8000"

ARCHIVE_DIR = Path("/Users/jsmat/gaTech/AI@GT/archive/recordings/recordings")

def get_english_files(count=100):
    """Get first N English files sorted numerically"""
    all_files = sorted(ARCHIVE_DIR.glob("english*.mp3"), key=lambda x: int(''.join(filter(str.isdigit, x.stem)) or 0))
    return all_files[:count]

def test_accent_detection(file_path, expected_language="english"):
    """Test accent detection on a single file"""
    try:
        with open(file_path, 'rb') as f:
            files = {'audio_file': (file_path.name, f, 'audio/mpeg')}
            response = requests.post(
                f"{API_BASE_URL}/api/detect_accent",
                files=files,
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            predicted = result.get('predicted_accent', 'unknown')
            confidence = result.get('confidence', 0)
            top_predictions = result.get('top_predictions', [])
            is_uncertain = result.get('is_uncertain', False)
            
            is_correct = predicted.lower() == expected_language.lower()
            
            return {
                'file': file_path.name,
                'expected': expected_language,
                'predicted': predicted,
                'confidence': confidence,
                'correct': is_correct,
                'is_uncertain': is_uncertain,
                'top_3': top_predictions[:3]
            }
        else:
            return {
                'file': file_path.name,
                'expected': expected_language,
                'error': f"HTTP {response.status_code}: {response.text[:100]}"
            }
    except Exception as e:
        return {
            'file': file_path.name,
            'expected': expected_language,
            'error': str(e)
        }

def main():
    print("=" * 80)
    print("ENGLISH ACCENT DETECTION TEST - 100 FILES")
    print("=" * 80)
    print(f"Archive directory: {ARCHIVE_DIR}")
    print(f"API endpoint: {API_BASE_URL}/api/detect_accent")
    print()
    
    # Check if server is running
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Server health check failed: {response.status_code}")
            return
        print("✅ Server is running")
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {API_BASE_URL}")
        print("   Make sure the backend server is running")
        return
    
    print()
    
    # Get 100 English files
    print("Finding English files...")
    english_files = get_english_files(100)
    print(f"  Found {len(english_files)} English files")
    
    print(f"\nTotal test files: {len(english_files)}")
    print("=" * 80)
    print()
    
    # Run tests
    results = []
    correct_count = 0
    total_count = 0
    uncertain_count = 0
    
    for i, file_path in enumerate(english_files, 1):
        print(f"[{i}/{len(english_files)}] Testing {file_path.name}...", end=" ")
        result = test_accent_detection(file_path, "english")
        results.append(result)
        
        if 'error' in result:
            print(f"❌ ERROR: {result['error']}")
        else:
            total_count += 1
            if result.get('is_uncertain'):
                uncertain_count += 1
            if result['correct']:
                correct_count += 1
                print(f"✅ {result['predicted']} ({result['confidence']:.1f}%)")
            else:
                top3_str = ", ".join([f"{p['accent']} ({p['confidence']:.1f}%)" for p in result['top_3']])
                print(f"❌ Predicted: {result['predicted']} ({result['confidence']:.1f}%), Top 3: {top3_str}")
        
        # Small delay to avoid overwhelming the server
        import time
        time.sleep(0.1)
    
    # Print summary
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests: {len(english_files)}")
    print(f"Successful predictions: {total_count}")
    print(f"Correct predictions: {correct_count}")
    print(f"Uncertain predictions: {uncertain_count}")
    if total_count > 0:
        accuracy = (correct_count / total_count) * 100
        print(f"Accuracy: {accuracy:.1f}%")
    print()
    
    # Analyze failures
    failed = [r for r in results if not r.get('correct', False) and 'error' not in r]
    if failed:
        print("=" * 80)
        print("FAILURE ANALYSIS")
        print("=" * 80)
        print(f"Failed predictions: {len(failed)}")
        
        # Group by predicted accent
        misclassifications = defaultdict(int)
        for r in failed:
            misclassifications[r['predicted']] += 1
        
        print("\nMisclassified as:")
        for accent, count in sorted(misclassifications.items(), key=lambda x: -x[1]):
            print(f"  {accent:12} : {count:3} files")
        
        # Show files where English is in top 3
        english_in_top3 = [r for r in failed if any(p['accent'].lower() == 'english' for p in r.get('top_3', []))]
        if english_in_top3:
            print(f"\nEnglish in top 3 but not #1: {len(english_in_top3)} files")
            for r in english_in_top3[:10]:  # Show first 10
                english_pos = next((i for i, p in enumerate(r['top_3']) if p['accent'].lower() == 'english'), -1)
                english_conf = r['top_3'][english_pos]['confidence'] if english_pos >= 0 else 0
                print(f"  {r['file']}: Predicted {r['predicted']} ({r['confidence']:.1f}%), English #{english_pos+1} ({english_conf:.1f}%)")
        
        # Show files where English is not in top 3
        english_not_in_top3 = [r for r in failed if not any(p['accent'].lower() == 'english' for p in r.get('top_3', []))]
        if english_not_in_top3:
            print(f"\nEnglish NOT in top 3: {len(english_not_in_top3)} files")
            for r in english_not_in_top3[:10]:  # Show first 10
                print(f"  {r['file']}: Predicted {r['predicted']} ({r['confidence']:.1f}%)")
    
    print()
    print("=" * 80)
    
    # Save detailed results to file
    output_file = backend_dir / "english_test_100_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'summary': {
                'total_tests': len(english_files),
                'successful': total_count,
                'correct': correct_count,
                'uncertain': uncertain_count,
                'accuracy': (correct_count / total_count * 100) if total_count > 0 else 0
            },
            'results': results
        }, f, indent=2)
    
    print(f"Detailed results saved to: {output_file}")

if __name__ == "__main__":
    main()

