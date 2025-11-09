#!/usr/bin/env python3
"""
Comprehensive Test Script for Accent Detection

Tests:
1. 100 English files
2. 5 files for each other supported class
3. Custom Jonathan files (separate section)
"""

import os
import sys
import json
from pathlib import Path
import requests
from collections import defaultdict
import re

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Base URL for the API
API_BASE_URL = "http://localhost:8000"

# Generate English file list (1-100)
english_files = [f"english{i}.mp3" for i in range(1, 101)]

# Test files mapping
TEST_FILES = {
    "english": english_files,
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

# Custom Jonathan files
JONATHAN_FILES = {
    "JonathanEnergetic.mp3": "english",
    "JonathanMonotone.mp3": "english",
    "JonathanMixed.mp3": "english",
    "JonathanEnergeticPrompt2.mp3": "english",
    "JonathanEnergetic2.mp3": "english",
    "JonathanEnglish.mp3": "english",
    "JonathanIndian.mp3": "indian"  # Note: indian might not be in model classes
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
    print("COMPREHENSIVE ACCENT DETECTION TEST SUITE")
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
    
    # ========================================================================
    # SECTION 1: Standard Test Files (100 English, 5 each for others)
    # ========================================================================
    print("=" * 80)
    print("SECTION 1: STANDARD TEST FILES")
    print("=" * 80)
    print()
    
    # Collect all test files
    all_tests = []
    for language, filenames in TEST_FILES.items():
        print(f"Finding {language} files...")
        actual_files = find_actual_files(language, filenames)
        print(f"  Found {len(actual_files)}/{len(filenames)} files")
        
        for file_path in actual_files:
            all_tests.append((file_path, language))
    
    print(f"\nTotal standard test files: {len(all_tests)}")
    print("=" * 80)
    print()
    
    # Run standard tests
    standard_results = defaultdict(list)
    correct_count = 0
    total_count = 0
    
    for i, (file_path, expected_lang) in enumerate(all_tests, 1):
        print(f"[{i}/{len(all_tests)}] Testing {file_path.name} (expected: {expected_lang})...", end=" ")
        result = test_accent_detection(file_path, expected_lang)
        standard_results[expected_lang].append(result)
        
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
    
    # ========================================================================
    # SECTION 2: Custom Jonathan Files
    # ========================================================================
    print()
    print("=" * 80)
    print("SECTION 2: CUSTOM JONATHAN FILES")
    print("=" * 80)
    print()
    
    jonathan_tests = []
    for filename, expected_accent in JONATHAN_FILES.items():
        file_path = ARCHIVE_DIR / filename
        if file_path.exists():
            jonathan_tests.append((file_path, expected_accent))
            print(f"✅ Found: {filename}")
        else:
            print(f"❌ Not found: {filename}")
    
    if not jonathan_tests:
        print("\n❌ No Jonathan files found!")
    else:
        print(f"\nTotal Jonathan files: {len(jonathan_tests)}")
        print("=" * 80)
        print()
        
        # Run Jonathan tests
        jonathan_results = []
        jonathan_correct = 0
        jonathan_total = 0
        
        for i, (file_path, expected_accent) in enumerate(jonathan_tests, 1):
            print(f"[{i}/{len(jonathan_tests)}] Testing {file_path.name}")
            print(f"  Expected accent: {expected_accent}")
            print("  Processing...", end=" ")
            
            result = test_accent_detection(file_path, expected_accent)
            jonathan_results.append(result)
            
            if 'error' in result:
                print(f"❌ ERROR: {result['error']}")
            else:
                jonathan_total += 1
                status = "✅" if result['correct'] else "❌"
                uncertain = " (UNCERTAIN)" if result.get('is_uncertain') else ""
                print(f"{status} Predicted: {result['predicted']} ({result['confidence']:.1f}%){uncertain}")
                
                if result['correct']:
                    jonathan_correct += 1
                
                # Show top 3 predictions
                if result.get('top_3'):
                    print("  Top 3 predictions:")
                    for j, pred in enumerate(result['top_3'][:3], 1):
                        print(f"    {j}. {pred['accent']}: {pred['confidence']:.1f}%")
            
            print()
            
            # Small delay
            import time
            time.sleep(0.2)
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print()
    print("=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    # Standard tests summary
    print("\n📊 STANDARD TESTS:")
    print(f"  Total files tested: {len(all_tests)}")
    print(f"  Successful predictions: {total_count}")
    print(f"  Correct predictions: {correct_count}")
    if total_count > 0:
        accuracy = (correct_count / total_count) * 100
        print(f"  Accuracy: {accuracy:.1f}%")
    
    print("\n  Per-language results:")
    print("-" * 80)
    for language in sorted(standard_results.keys()):
        lang_results = standard_results[language]
        lang_correct = sum(1 for r in lang_results if r.get('correct') == True)
        lang_total = sum(1 for r in lang_results if 'error' not in r)
        lang_errors = sum(1 for r in lang_results if 'error' in r)
        
        if lang_total > 0:
            lang_accuracy = (lang_correct / lang_total) * 100
            print(f"  {language:12} | Correct: {lang_correct:3}/{lang_total:3} ({lang_accuracy:5.1f}%) | Errors: {lang_errors}")
        else:
            print(f"  {language:12} | No successful tests | Errors: {lang_errors}")
    
    # Jonathan tests summary
    if jonathan_tests:
        print("\n🎤 JONATHAN CUSTOM FILES:")
        print(f"  Total files tested: {len(jonathan_tests)}")
        print(f"  Successful predictions: {jonathan_total}")
        print(f"  Correct predictions: {jonathan_correct}")
        if jonathan_total > 0:
            jonathan_accuracy = (jonathan_correct / jonathan_total) * 100
            print(f"  Accuracy: {jonathan_accuracy:.1f}%")
        
        print("\n  Detailed results:")
        print("-" * 80)
        for result in jonathan_results:
            if 'error' in result:
                print(f"  ❌ {result['file']}: ERROR - {result['error']}")
            else:
                status = "✅" if result['correct'] else "❌"
                print(f"  {status} {result['file']}")
                print(f"     Expected: {result['expected']}")
                print(f"     Predicted: {result['predicted']} ({result['confidence']:.1f}%)")
                if result.get('is_uncertain'):
                    print(f"     ⚠️  Low confidence - prediction is uncertain")
    
    print()
    print("=" * 80)
    
    # Save results to file
    output_file = backend_dir / "comprehensive_test_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'standard_tests': {
                'summary': {
                    'total_tests': len(all_tests),
                    'successful': total_count,
                    'correct': correct_count,
                    'accuracy': (correct_count / total_count * 100) if total_count > 0 else 0
                },
                'results': {lang: standard_results[lang] for lang in sorted(standard_results.keys())}
            },
            'jonathan_tests': {
                'summary': {
                    'total_tests': len(jonathan_tests),
                    'successful': jonathan_total,
                    'correct': jonathan_correct,
                    'accuracy': (jonathan_correct / jonathan_total * 100) if jonathan_total > 0 else 0
                },
                'results': jonathan_results
            }
        }, f, indent=2)
    
    print(f"Detailed results saved to: {output_file}")

if __name__ == "__main__":
    main()

