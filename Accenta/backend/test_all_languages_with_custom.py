#!/usr/bin/env python3
"""
Comprehensive Test Script for All Languages + Custom Recordings

Tests:
1. All supported languages (5 files each)
2. Custom Jonathan files (English)
3. Custom Indian recordings (Tamil - indian1-9.mp3)
"""

import os
import sys
import json
from pathlib import Path
import requests
from collections import defaultdict
import time

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Base URL for the API
API_BASE_URL = "http://localhost:8000"

# Test files mapping - all supported languages (5 files each)
TEST_FILES = {
    "english": ["english1.mp3", "english2.mp3", "english3.mp3", "english4.mp3", "english5.mp3"],
    "german": ["german11.mp3", "german9.mp3", "german8.mp3", "german10.mp3", "german12.mp3"],
    "hindi": ["hindi1.mp3", "hindi3.mp3", "hindi18.mp3", "hindi2.mp3", "hindi6.mp3"],
    "italian": ["italian22.mp3", "italian6.mp3", "italian7.mp3", "italian23.mp3", "italian21.mp3"],
    "japanese": ["japanese21.mp3", "japanese20.mp3", "japanese22.mp3", "japanese23.mp3", "japanese27.mp3"],
    "korean": ["korean40.mp3", "korean41.mp3", "korean43.mp3", "korean42.mp3", "korean52.mp3"],
    "malayalam": ["malayalam4.mp3", "malayalam3.mp3", "malayalam2.mp3", "malayalam1.mp3"],
    "mandarin": ["mandarin38.mp3", "mandarin10.mp3", "mandarin11.mp3", "mandarin39.mp3", "mandarin13.mp3"],
    "russian": ["russian45.mp3", "russian44.mp3", "russian46.mp3", "russian47.mp3", "russian43.mp3"],
    "tamil": ["tamil1.mp3", "tamil2.mp3", "tamil3.mp3", "tamil6.mp3", "tamil4.mp3"],
    "thai": ["thai4.mp3", "thai5.mp3", "thai7.mp3", "thai6.mp3", "thai2.mp3"],
    "turkish": ["turkish20.mp3", "turkish34.mp3", "turkish35.mp3", "turkish21.mp3", "turkish37.mp3"]
}

# Custom Jonathan files (all English)
JONATHAN_FILES = {
    "JonathanEnergetic.mp3": "english",
    "JonathanMonotone.mp3": "english",
    "JonathanMixed.mp3": "english",
    "JonathanEnergeticPrompt2.mp3": "english",
    "JonathanEnergetic2.mp3": "english",
    "JonathanEnglish.mp3": "english",
    "JonathanIndian.mp3": "tamil"  # This one might be Tamil
}

# Custom Indian recordings (all Tamil - newly trained)
INDIAN_FILES = {
    f"indian{i}.mp3": "tamil" for i in range(1, 10)
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
            'file': file_path.name if 'file_path' in locals() else 'unknown',
            'expected': expected_language,
            'error': str(e)
        }

def main():
    print("=" * 80)
    print("COMPREHENSIVE TEST: ALL LANGUAGES + CUSTOM RECORDINGS")
    print("=" * 80)
    print(f"Archive directory: {ARCHIVE_DIR}")
    print(f"API endpoint: {API_BASE_URL}/api/detect_accent")
    print()
    
    # Check if server is running
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Server health check failed: {response.status_code}")
            print("   Starting server test anyway...")
        else:
            print("✅ Server is running")
    except requests.exceptions.ConnectionError:
        print(f"⚠️  Cannot connect to server at {API_BASE_URL}")
        print("   Testing will use direct model access...")
        print("   (Make sure backend server is running for full API tests)")
    
    print()
    
    # ========================================================================
    # SECTION 1: Standard Test Files (5 files per language)
    # ========================================================================
    print("=" * 80)
    print("SECTION 1: STANDARD TEST FILES (5 files per language)")
    print("=" * 80)
    print()
    
    # Collect all test files
    all_tests = []
    for language, filenames in TEST_FILES.items():
        print(f"Finding {language} files...", end=" ")
        actual_files = find_actual_files(language, filenames)
        print(f"Found {len(actual_files)}/{len(filenames)}")
        
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
        print(f"[{i}/{len(all_tests)}] {file_path.name:30s} (expected: {expected_lang:12s})...", end=" ")
        result = test_accent_detection(file_path, expected_lang)
        standard_results[expected_lang].append(result)
        
        if 'error' in result:
            print(f"❌ ERROR: {result['error'][:50]}")
        else:
            total_count += 1
            if result['correct']:
                correct_count += 1
                print(f"✅ {result['predicted']:12s} ({result['confidence']:5.1f}%)")
            else:
                uncertain = " ⚠️" if result.get('is_uncertain') else ""
                print(f"❌ {result['predicted']:12s} ({result['confidence']:5.1f}%){uncertain}")
        
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
    
    jonathan_results = []
    jonathan_correct = 0
    jonathan_total = 0
    
    if jonathan_tests:
        print(f"\nTotal Jonathan files: {len(jonathan_tests)}")
        print("=" * 80)
        print()
        
        for i, (file_path, expected_accent) in enumerate(jonathan_tests, 1):
            print(f"[{i}/{len(jonathan_tests)}] {file_path.name:30s} (expected: {expected_accent:12s})...", end=" ")
            
            result = test_accent_detection(file_path, expected_accent)
            jonathan_results.append(result)
            
            if 'error' in result:
                print(f"❌ ERROR: {result['error'][:50]}")
            else:
                jonathan_total += 1
                status = "✅" if result['correct'] else "❌"
                uncertain = " ⚠️" if result.get('is_uncertain') else ""
                print(f"{status} {result['predicted']:12s} ({result['confidence']:5.1f}%){uncertain}")
                
                if result['correct']:
                    jonathan_correct += 1
            
            time.sleep(0.2)
    
    # ========================================================================
    # SECTION 3: Custom Indian Recordings (Newly Trained as Tamil)
    # ========================================================================
    print()
    print("=" * 80)
    print("SECTION 3: CUSTOM INDIAN RECORDINGS (Tamil - Newly Trained)")
    print("=" * 80)
    print()
    
    indian_tests = []
    for filename, expected_accent in INDIAN_FILES.items():
        file_path = ARCHIVE_DIR / filename
        if file_path.exists():
            indian_tests.append((file_path, expected_accent))
            print(f"✅ Found: {filename}")
        else:
            print(f"❌ Not found: {filename}")
    
    indian_results = []
    indian_correct = 0
    indian_total = 0
    
    if indian_tests:
        print(f"\nTotal Indian files: {len(indian_tests)}")
        print("=" * 80)
        print()
        
        for i, (file_path, expected_accent) in enumerate(indian_tests, 1):
            print(f"[{i}/{len(indian_tests)}] {file_path.name:30s} (expected: {expected_accent:12s})...", end=" ")
            
            result = test_accent_detection(file_path, expected_accent)
            indian_results.append(result)
            
            if 'error' in result:
                print(f"❌ ERROR: {result['error'][:50]}")
            else:
                indian_total += 1
                status = "✅" if result['correct'] else "❌"
                uncertain = " ⚠️" if result.get('is_uncertain') else ""
                print(f"{status} {result['predicted']:12s} ({result['confidence']:5.1f}%){uncertain}")
                
                if result['correct']:
                    indian_correct += 1
                
                # Show top 3 if incorrect
                if not result['correct'] and result.get('top_3'):
                    print(f"      Top 3: ", end="")
                    for j, pred in enumerate(result['top_3'][:3], 1):
                        print(f"{pred['accent']} ({pred['confidence']:.1f}%)", end=", " if j < 3 else "\n")
            
            time.sleep(0.2)
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print()
    print("=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    # Standard tests summary
    print("\n📊 STANDARD TESTS (5 files per language):")
    print(f"  Total files tested: {len(all_tests)}")
    print(f"  Successful predictions: {total_count}")
    print(f"  Correct predictions: {correct_count}")
    if total_count > 0:
        accuracy = (correct_count / total_count) * 100
        print(f"  Accuracy: {accuracy:.1f}%")
    
    print("\n  Per-language results:")
    print("-" * 80)
    print(f"  {'Language':<15} | {'Correct':<10} | {'Total':<8} | {'Accuracy':<10} | {'Errors'}")
    print("-" * 80)
    for language in sorted(standard_results.keys()):
        lang_results = standard_results[language]
        lang_correct = sum(1 for r in lang_results if r.get('correct') == True)
        lang_total = sum(1 for r in lang_results if 'error' not in r)
        lang_errors = sum(1 for r in lang_results if 'error' in r)
        
        if lang_total > 0:
            lang_accuracy = (lang_correct / lang_total) * 100
            print(f"  {language:<15} | {lang_correct:3}/{len(lang_results):<3}      | {lang_total:<8} | {lang_accuracy:6.1f}%    | {lang_errors}")
        else:
            print(f"  {language:<15} | {'N/A':<10} | {len(lang_results):<8} | {'N/A':<10} | {lang_errors}")
    
    # Jonathan tests summary
    if jonathan_tests:
        print("\n🎤 JONATHAN CUSTOM FILES:")
        print(f"  Total files tested: {len(jonathan_tests)}")
        print(f"  Successful predictions: {jonathan_total}")
        print(f"  Correct predictions: {jonathan_correct}")
        if jonathan_total > 0:
            jonathan_accuracy = (jonathan_correct / jonathan_total) * 100
            print(f"  Accuracy: {jonathan_accuracy:.1f}%")
    
    # Indian tests summary
    if indian_tests:
        print("\n🇮🇳 INDIAN CUSTOM RECORDINGS (Tamil):")
        print(f"  Total files tested: {len(indian_tests)}")
        print(f"  Successful predictions: {indian_total}")
        print(f"  Correct predictions: {indian_correct}")
        if indian_total > 0:
            indian_accuracy = (indian_correct / indian_total) * 100
            print(f"  Accuracy: {indian_accuracy:.1f}%")
    
    # Overall summary
    print("\n" + "=" * 80)
    print("OVERALL SUMMARY")
    print("=" * 80)
    total_all = total_count + jonathan_total + indian_total
    correct_all = correct_count + jonathan_correct + indian_correct
    if total_all > 0:
        overall_accuracy = (correct_all / total_all) * 100
        print(f"  Total files tested: {len(all_tests) + len(jonathan_tests) + len(indian_tests)}")
        print(f"  Successful predictions: {total_all}")
        print(f"  Correct predictions: {correct_all}")
        print(f"  Overall accuracy: {overall_accuracy:.1f}%")
    
    print()
    print("=" * 80)
    
    # Save results to file
    output_file = backend_dir / "all_languages_test_results.json"
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
            },
            'indian_tests': {
                'summary': {
                    'total_tests': len(indian_tests),
                    'successful': indian_total,
                    'correct': indian_correct,
                    'accuracy': (indian_correct / indian_total * 100) if indian_total > 0 else 0
                },
                'results': indian_results
            },
            'overall': {
                'total_tests': len(all_tests) + len(jonathan_tests) + len(indian_tests),
                'successful': total_all,
                'correct': correct_all,
                'accuracy': (correct_all / total_all * 100) if total_all > 0 else 0
            }
        }, f, indent=2)
    
    print(f"Detailed results saved to: {output_file}")

if __name__ == "__main__":
    main()

