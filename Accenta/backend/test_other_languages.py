#!/usr/bin/env python3
"""
Test script for other languages (5 files each)
Tests the newly trained model (12 classes, no Arabic/Spanish/French)
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

# Test files mapping (5 files per language)
# Excluding: english (tested separately), arabic, spanish, french (removed from model)
TEST_FILES = {
    "mandarin": ["mandarin38.mp3", "mandarin10.mp3", "mandarin11.mp3", "mandarin39.mp3", "mandarin13.mp3"],
    "japanese": ["japanese21.mp3", "japanese20.mp3", "japanese22.mp3", "japanese23.mp3", "japanese27.mp3"],
    "korean": ["korean40.mp3", "korean41.mp3", "korean43.mp3", "korean42.mp3", "korean52.mp3"],
    "hindi": ["hindi1.mp3", "hindi3.mp3", "hindi18.mp3", "hindi2.mp3", "hindi6.mp3"],
    "russian": ["russian45.mp3", "russian44.mp3", "russian46.mp3", "russian47.mp3", "russian43.mp3"],
    "german": ["german11.mp3", "german9.mp3", "german8.mp3", "german10.mp3", "german12.mp3"],
    "italian": ["italian22.mp3", "italian6.mp3", "italian7.mp3", "italian23.mp3", "italian21.mp3"],
    "thai": ["thai4.mp3", "thai5.mp3", "thai7.mp3", "thai6.mp3", "thai2.mp3"],
    "turkish": ["turkish20.mp3", "turkish34.mp3", "turkish35.mp3", "turkish21.mp3", "turkish37.mp3"],
    "malayalam": ["malayalam4.mp3", "malayalam3.mp3", "malayalam2.mp3", "malayalam1.mp3", "malayalam5.mp3"],
    "tamil": ["tamil1.mp3", "tamil2.mp3", "tamil3.mp3", "tamil6.mp3", "tamil4.mp3"]
}

ARCHIVE_DIR = Path("/Users/jsmat/gaTech/AI@GT/archive/recordings/recordings")

def find_actual_files(language, filenames):
    """Find actual files that exist"""
    found_files = []
    for filename in filenames:
        file_path = ARCHIVE_DIR / filename
        if file_path.exists():
            found_files.append(file_path)
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
            is_uncertain = result.get('is_uncertain', False)
            
            is_correct = predicted.lower() == expected_language.lower() if expected_language else None
            
            return {
                'file': file_path.name,
                'expected': expected_language,
                'predicted': predicted,
                'confidence': confidence,
                'correct': is_correct,
                'is_uncertain': is_uncertain,
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
    print("TESTING OTHER LANGUAGES (5 files each)")
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
    results_by_language = defaultdict(list)
    correct_count = 0
    total_count = 0
    
    for i, (file_path, expected_lang) in enumerate(all_tests, 1):
        print(f"[{i}/{len(all_tests)}] Testing {file_path.name} (expected: {expected_lang})...", end=" ")
        result = test_accent_detection(file_path, expected_lang)
        results_by_language[expected_lang].append(result)
        
        if 'error' in result:
            print(f"❌ ERROR: {result['error']}")
        else:
            total_count += 1
            if result['correct']:
                correct_count += 1
                print(f"✅ {result['predicted']} ({result['confidence']:.1f}%)")
            else:
                uncertain = " (UNCERTAIN)" if result.get('is_uncertain') else ""
                print(f"❌ {result['predicted']} ({result['confidence']:.1f}%){uncertain}")
        
        # Small delay to avoid overwhelming the server
        import time
        time.sleep(0.1)
    
    # Summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total files tested: {len(all_tests)}")
    print(f"Successful predictions: {total_count}")
    print(f"Correct predictions: {correct_count}")
    if total_count > 0:
        accuracy = (correct_count / total_count) * 100
        print(f"Overall Accuracy: {accuracy:.1f}%")
    
    print("\nPer-language results:")
    print("-" * 80)
    print(f"{'Language':<15} | {'Correct':<10} | {'Total':<8} | {'Accuracy':<10} | {'Errors'}")
    print("-" * 80)
    
    for language in sorted(results_by_language.keys()):
        lang_results = results_by_language[language]
        lang_correct = sum(1 for r in lang_results if r.get('correct') == True)
        lang_total = sum(1 for r in lang_results if 'error' not in r)
        lang_errors = sum(1 for r in lang_results if 'error' in r)
        
        if lang_total > 0:
            lang_accuracy = (lang_correct / lang_total) * 100
            print(f"{language:<15} | {lang_correct:3}/{lang_total:3}      | {lang_total:3}      | {lang_accuracy:6.1f}%    | {lang_errors}")
        else:
            print(f"{language:<15} | {'N/A':<10} | {lang_total:3}      | {'N/A':<10} | {lang_errors}")
    
    print()
    print("=" * 80)
    
    # Show incorrect predictions
    incorrect = []
    for language, lang_results in results_by_language.items():
        for result in lang_results:
            if 'error' not in result and not result.get('correct'):
                incorrect.append(result)
    
    if incorrect:
        print("\n❌ Incorrect Predictions:")
        print("-" * 80)
        for result in incorrect:
            print(f"  {result['file']}")
            print(f"    Expected: {result['expected']}")
            print(f"    Predicted: {result['predicted']} ({result['confidence']:.1f}%)")
            if result.get('top_3'):
                top3_str = ', '.join([f"{p['accent']} ({p['confidence']:.1f}%)" for p in result['top_3'][:3]])
                print(f"    Top 3: {top3_str}")
            print()
    
    # Save results
    output_file = backend_dir / "other_languages_test_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'summary': {
                'total_tests': len(all_tests),
                'successful': total_count,
                'correct': correct_count,
                'accuracy': (correct_count / total_count * 100) if total_count > 0 else 0
            },
            'results_by_language': {lang: results_by_language[lang] for lang in sorted(results_by_language.keys())}
        }, f, indent=2)
    
    print(f"Detailed results saved to: {output_file}")

if __name__ == "__main__":
    main()

