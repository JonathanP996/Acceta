# Microphone Audio Normalization

## Problem
Microphone recordings were being misclassified because they have different spectral characteristics than the training files:
- **26.6% lower spectral centroid** (less high-frequency content)
- **32.2% less high-frequency energy** (>4kHz: 20.1% vs 29.7%)
- **34.4% more low-frequency energy** (<1kHz: 58.4% vs 43.5%)
- **20% less mid-frequency energy** (1-4kHz: 21.5% vs 26.9%)

## Solution
Created `normalize_microphone_audio()` function in `preprocess.py` that:
1. **Reduces low-frequency emphasis** (< 1 kHz) using a high-pass filter
2. **Boosts mid-frequencies** (1-4 kHz) by adding 25% of bandpass-filtered content
3. **Boosts high-frequencies** (2-8 kHz) by adding 50% of bandpass-filtered content
4. **Normalizes RMS** to match training file average (0.092223)
5. **Prevents clipping** with soft limiting

## Implementation
The normalization is automatically applied when `is_microphone_recording=True` is passed to `preprocess_audio()`. The `accent_detection.py` route automatically detects microphone recordings and applies normalization.

## Results
**Before normalization:**
- JonathanEnergetic.mp3: ❌ Arabic (high confidence)
- JonathanMonotone.mp3: ❌ Arabic (high confidence)
- JonathanMixed.mp3: ❌ Arabic (high confidence)
- **Accuracy: 0%**

**After normalization:**
- JonathanEnergetic.mp3: ✅ English (99.4%)
- JonathanMonotone.mp3: ✅ English (95.8%)
- JonathanMixed.mp3: ⚠️ Mandarin (53.0%) but English is 2nd (47.0%)
- **Accuracy: 66.7%**
- **English in top 3: 100%**

## Technical Details
- Uses `scipy.signal.butter` and `filtfilt` for frequency-domain filtering
- 2nd-order Butterworth filters for smooth frequency response
- Normalization applied BEFORE MFCC extraction (critical for model accuracy)
- Preserves audio quality while matching training distribution

## Files Modified
- `backend/services/preprocess.py`: Added `normalize_microphone_audio()` function
- `backend/services/preprocess.py`: Modified `preprocess_audio()` to apply normalization for microphone recordings
- `backend/analyze_audio_metadata_comparison.py`: Analysis script to identify differences
- `backend/test_normalization_improvement.py`: Test script to verify improvements

## Next Steps (Optional Improvements)
1. Fine-tune filter parameters if needed (currently using conservative values)
2. Consider adaptive normalization based on detected spectral characteristics
3. Test on more microphone recordings to validate robustness

