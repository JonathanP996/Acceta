#!/usr/bin/env python3
"""
Test script for accent detection on Jonathan and Benji files
Tests 4 files total:
- JonathanIndian.mp3
- JonathanEnglish.mp3
- BenjiEnglish.mp3
- BenjiBritish.mp3
"""

import os
import sys
import json
from pathlib import Path
import requests

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Base URL for the API
API_BASE_URL = "http://localhost:8000"

# Test files with expected accents
TEST_FILES = {
    "JonathanIndian.mp3": "indian",
    "JonathanEnglish.mp3": "english",
    "BenjiEnglish.mp3": "english",
    "BenjiBritish.mp3": "british"
}

ARCHIVE_DIR = Path("/Users/jsmat/gaTech/AI@GT/archive/recordings/recordings")

def test_accent_detection(file_path, expected_accent=None):
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
            
            is_correct = predicted.lower() == expected_accent.lower() if expected_accent else None
            
            return {
                'file': file_path.name,
                'expected': expected_accent,
                'predicted': predicted,
                'confidence': confidence,
                'correct': is_correct,
                'is_uncertain': is_uncertain,
                'top_3': top_predictions
            }
        else:
            return {
                'file': file_path.name,
                'expected': expected_accent,
                'error': f"HTTP {response.status_code}: {response.text[:100]}"
            }
    except Exception as e:
        return {
            'file': file_path.name,
            'expected': expected_accent,
            'error': str(e)
        }

def main():
    print("=" * 80)
    print("ACCENT DETECTION TEST - JONATHAN & BENJI FILES")
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
        print("   cd Accenta/backend && python app.py")
        return
    
    print()
    
    # Find all test files
    all_tests = []
    for filename, expected_accent in TEST_FILES.items():
        file_path = ARCHIVE_DIR / filename
        if file_path.exists():
            all_tests.append((file_path, expected_accent))
            print(f"✅ Found: {filename}")
        else:
            print(f"❌ Not found: {filename}")
    
    if not all_tests:
        print("\n❌ No test files found!")
        return
    
    print(f"\nTotal test files: {len(all_tests)}")
    print("=" * 80)
    print()
    
    # Run tests
    results = []
    correct_count = 0
    total_count = 0
    
    for i, (file_path, expected_accent) in enumerate(all_tests, 1):
        print(f"[{i}/{len(all_tests)}] Testing {file_path.name}")
        print(f"  Expected accent: {expected_accent}")
        print("  Processing...", end=" ")
        
        result = test_accent_detection(file_path, expected_accent)
        results.append(result)
        
        if 'error' in result:
            print(f"❌ ERROR: {result['error']}")
        else:
            total_count += 1
            status = "✅" if result['correct'] else "❌"
            uncertain = " (UNCERTAIN)" if result.get('is_uncertain') else ""
            print(f"{status} Predicted: {result['predicted']} ({result['confidence']:.1f}%){uncertain}")
            
            if result['correct']:
                correct_count += 1
            
            # Show top 3 predictions
            if result.get('top_3'):
                print("  Top 3 predictions:")
                for j, pred in enumerate(result['top_3'][:3], 1):
                    print(f"    {j}. {pred['accent']}: {pred['confidence']:.1f}%")
        
        print()
        
        # Small delay to avoid overwhelming the server
        import time
        time.sleep(0.2)
    
    # Print summary
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total files tested: {len(all_tests)}")
    print(f"Successful predictions: {total_count}")
    print(f"Correct predictions: {correct_count}")
    if total_count > 0:
        accuracy = (correct_count / total_count) * 100
        print(f"Accuracy: {accuracy:.1f}%")
    print()
    
    # Detailed results
    print("Detailed Results:")
    print("-" * 80)
    for result in results:
        if 'error' in result:
            print(f"❌ {result['file']}: ERROR - {result['error']}")
        else:
            status = "✅" if result['correct'] else "❌"
            print(f"{status} {result['file']}")
            print(f"   Expected: {result['expected']}")
            print(f"   Predicted: {result['predicted']} ({result['confidence']:.1f}%)")
            if result.get('is_uncertain'):
                print(f"   ⚠️  Low confidence - prediction is uncertain")
    
    print()
    print("=" * 80)
    
    # Save results to file
    output_file = backend_dir / "jonathan_benji_test_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'summary': {
                'total_tests': len(all_tests),
                'successful': total_count,
                'correct': correct_count,
                'accuracy': (correct_count / total_count * 100) if total_count > 0 else 0
            },
            'results': results
        }, f, indent=2)
    
    print(f"Detailed results saved to: {output_file}")

if __name__ == "__main__":
    main()

