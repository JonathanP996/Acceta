#!/usr/bin/env python3
"""
Test script for accent detection using MP3 files from archives
Tests 20 English files and 5 files for each other supported language
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

# Test files mapping - using actual files found
TEST_FILES = {
    "english": [
        "english368.mp3", "english340.mp3", "english426.mp3", "english432.mp3",
        "english354.mp3", "english383.mp3", "english397.mp3", "english142.mp3",
        "english156.mp3", "english181.mp3"
    ],
    "arabic": ["arabic16.mp3", "arabic17.mp3", "arabic29.mp3", "arabic15.mp3", "arabic8.mp3"],
    "french": ["french57.mp3", "french43.mp3", "french42.mp3", "french56.mp3", "french40.mp3"],
    "german": ["german11.mp3", "german9.mp3", "german8.mp3", "german10.mp3", "german12.mp3"],
    "hindi": ["hindi1.mp3", "hindi3.mp3", "hindi18.mp3", "hindi2.mp3", "hindi6.mp3"],
    "italian": ["italian22.mp3", "italian6.mp3", "italian7.mp3", "italian23.mp3", "italian21.mp3"],
    "japanese": ["japanese21.mp3", "japanese20.mp3", "japanese22.mp3", "japanese23.mp3", "japanese27.mp3"],
    "korean": ["korean40.mp3", "korean41.mp3", "korean43.mp3", "korean42.mp3", "korean52.mp3"],
    "malayalam": ["malayalam4.mp3", "malayalam3.mp3", "malayalam2.mp3", "malayalam1.mp3", "malayalam5.mp3"],
    "mandarin": ["mandarin38.mp3", "mandarin10.mp3", "mandarin11.mp3", "mandarin39.mp3", "mandarin13.mp3"],
    "russian": ["russian45.mp3", "russian44.mp3", "russian46.mp3", "russian47.mp3", "russian43.mp3"],
    "spanish": ["spanish135.mp3", "spanish121.mp3", "spanish109.mp3", "spanish91.mp3", "spanish85.mp3"],
    "tamil": ["tamil1.mp3", "tamil2.mp3", "tamil3.mp3", "tamil6.mp3", "tamil4.mp3"],
    "thai": ["thai4.mp3", "thai5.mp3", "thai7.mp3", "thai6.mp3", "thai2.mp3"],
    "turkish": ["turkish20.mp3", "turkish34.mp3", "turkish35.mp3", "turkish21.mp3", "turkish37.mp3"]
}

ARCHIVE_DIR = Path("/Users/jsmat/gaTech/AI@GT/archive/recordings/recordings")

def find_actual_files(language, filenames):
    """Find actual files that exist"""
    found_files = []
    for filename in filenames:
        file_path = ARCHIVE_DIR / filename
        if file_path.exists():
            found_files.append(file_path)
        else:
            print(f"  Warning: {filename} not found")
    return found_files

def test_accent_detection(file_path, expected_language=None):
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
            
            is_correct = predicted.lower() == expected_language.lower() if expected_language else None
            
            return {
                'file': file_path.name,
                'expected': expected_language,
                'predicted': predicted,
                'confidence': confidence,
                'correct': is_correct,
                'top_3': top_predictions
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
    print("ACCENT DETECTION TEST SUITE")
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
        print("   Make sure the backend server is running:")
        print("   cd Accenta && source venv/bin/activate && cd backend && python app.py")
        return
    
    print()
    
    # Collect all test files
    all_tests = []
    for language, filenames in TEST_FILES.items():
        print(f"Finding {language} files...")
        actual_files = find_actual_files(language, filenames)
        print(f"  Found {len(actual_files)}/{len(filenames)} files")
        
        for file_path in actual_files:
            all_tests.append((file_path, language))
    
    print(f"\nTotal test files: {len(all_tests)}")
    print("=" * 80)
    print()
    
    # Run tests
    results = defaultdict(list)
    correct_count = 0
    total_count = 0
    
    for i, (file_path, expected_lang) in enumerate(all_tests, 1):
        print(f"[{i}/{len(all_tests)}] Testing {file_path.name} (expected: {expected_lang})...", end=" ")
        result = test_accent_detection(file_path, expected_lang)
        results[expected_lang].append(result)
        
        if 'error' in result:
            print(f"❌ ERROR: {result['error']}")
        else:
            total_count += 1
            if result['correct']:
                correct_count += 1
                print(f"✅ {result['predicted']} ({result['confidence']:.1f}%)")
            else:
                print(f"❌ Predicted: {result['predicted']} ({result['confidence']:.1f}%), Expected: {expected_lang}")
        
        # Small delay to avoid overwhelming the server
        import time
        time.sleep(0.1)
    
    # Print summary
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests: {len(all_tests)}")
    print(f"Successful predictions: {total_count}")
    print(f"Correct predictions: {correct_count}")
    if total_count > 0:
        accuracy = (correct_count / total_count) * 100
        print(f"Accuracy: {accuracy:.1f}%")
    print()
    
    # Per-language breakdown
    print("Per-language results:")
    print("-" * 80)
    for language in sorted(results.keys()):
        lang_results = results[language]
        lang_correct = sum(1 for r in lang_results if r.get('correct') == True)
        lang_total = sum(1 for r in lang_results if 'error' not in r)
        lang_errors = sum(1 for r in lang_results if 'error' in r)
        
        if lang_total > 0:
            lang_accuracy = (lang_correct / lang_total) * 100
            print(f"{language:12} | Correct: {lang_correct:2}/{lang_total:2} ({lang_accuracy:5.1f}%) | Errors: {lang_errors}")
        else:
            print(f"{language:12} | No successful tests | Errors: {lang_errors}")
    
    print()
    print("=" * 80)
    
    # Save detailed results to file
    output_file = backend_dir / "accent_detection_test_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'summary': {
                'total_tests': len(all_tests),
                'successful': total_count,
                'correct': correct_count,
                'accuracy': (correct_count / total_count * 100) if total_count > 0 else 0
            },
            'results': {lang: results[lang] for lang in sorted(results.keys())}
        }, f, indent=2)
    
    print(f"Detailed results saved to: {output_file}")

if __name__ == "__main__":
    main()

