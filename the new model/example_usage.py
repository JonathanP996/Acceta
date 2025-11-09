"""
Example usage of the AccentDetector module
Run this to test the integration
"""

from accent_detector import AccentDetector
import os

# Initialize detector
print("Initializing accent detector...")
detector = AccentDetector()

# Show supported classes
print(f"\nSupported accents: {detector.get_supported_classes()}")

# Example 1: Predict from file path
print("\n" + "="*60)
print("Example 1: Predict from file path")
print("="*60)

# Test with a Malayalam file (if available)
test_file = './archive/recordings/recordings/malayalam1.mp3'
if os.path.exists(test_file):
    result = detector.predict(test_file)
    print(f"File: {test_file}")
    print(f"Predicted Accent: {result['accent']}")
    print(f"Confidence: {result['confidence']}%")
    print(f"\nTop 3 predictions:")
    for i, pred in enumerate(result['top_n'], 1):
        print(f"  {i}. {pred['accent']:15s}: {pred['confidence']:.2f}%")
else:
    print(f"Test file not found: {test_file}")
    print("Please provide a path to an audio file to test.")

# Example 2: Predict with custom top N
print("\n" + "="*60)
print("Example 2: Get top 5 predictions")
print("="*60)

if os.path.exists(test_file):
    result = detector.predict(test_file, top_n=5)
    print(f"Top 5 predictions:")
    for i, pred in enumerate(result['top_n'], 1):
        print(f"  {i}. {pred['accent']:15s}: {pred['confidence']:.2f}%")

print("\n✅ Integration test complete!")

