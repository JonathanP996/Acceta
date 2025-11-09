# Microphone Input Issues - Detailed Analysis

## Problem Statement
- **Test Files (MP3)**: 81% accuracy ✅
- **Microphone Input**: Inaccurate predictions ❌
- **Other Model**: Same test accuracy but works with microphone ✅

## Root Cause Analysis - Each Difference

### ✅ FIXED: #1 Audio Format & Conversion Chain
**Issue**: WebM → WAV conversion in browser
**Status**: Fixed - Backend now detects browser recordings and uses `kaiser_best` resampling

### 🔴 CRITICAL: #2 Sample Rate Handling
**Issue**: 
- Frontend requests 16kHz in `getUserMedia` constraints (line 36)
- AudioContext ignores this and uses native rate (44.1kHz, 48kHz, etc.) (line 56)
- WAV file created with `buffer.sampleRate` = AudioContext rate (line 207, 225)
- Backend expects 44.1kHz and resamples
- **Result**: Double resampling (native → 44.1kHz) causes artifacts

**Fix Applied**: Frontend now resamples to 44.1kHz before creating WAV

### ✅ FIXED: #3 Resampling Quality
**Issue**: Different resampling for browser vs test files
**Status**: Fixed - Browser recordings now use `kaiser_best`

### ✅ FIXED: #4 File Extension Detection
**Issue**: Backend checked filename before content-type
**Status**: Fixed - Now checks content-type first, detects browser recordings

### ⚠️ POTENTIAL: #5 Audio Duration
**Issue**: Training uses exactly 5 seconds, microphone is variable
**Impact**: Low - Backend takes first 5 seconds if longer, uses all if shorter
**Status**: Working as designed

### ⚠️ POTENTIAL: #6 Audio Quality & Noise
**Issue**: Real-time recording has noise, echo cancellation artifacts
**Impact**: Medium - Could affect accuracy
**Status**: Cannot be fixed in preprocessing, but model should handle it

### ✅ FEATURE: #7 Top N Predictions Display
**Issue**: This model shows all 15 classes, other might not
**Impact**: Positive - User can see correct prediction even if not #1
**Status**: Feature, not a bug

### ✅ FEATURE: #8 Uncertainty Detection
**Issue**: This model flags low confidence
**Impact**: Positive - Warns user when uncertain
**Status**: Feature, not a bug

### ✅ WORKING: #9 Model Singleton Pattern
**Issue**: Model loads once, cached
**Status**: Working correctly

### ✅ WORKING: #10 Audio Normalization
**Issue**: Global mean/std normalization
**Status**: Matches training exactly

### ✅ WORKING: #11 MFCC Feature Extraction
**Issue**: Must match training parameters
**Status**: Matches training exactly (n_mfcc=13, sr=44100)

### 🔴 CRITICAL: #12 Audio Buffer Conversion
**Issue**: 
- Frontend: Float32 samples → 16-bit PCM
- Quantization: `sample * 0x8000` for negative, `sample * 0x7FFF` for positive
- **Problem**: Asymmetric quantization! Negative values use full range (-32768 to 0), positive use (0 to 32767)
- This creates a DC bias and distorts the audio

**Fix Needed**: Use symmetric quantization

### ✅ FIXED: #13 Content-Type vs Filename
**Status**: Fixed - Backend now checks content-type first

### 🔴 CRITICAL: #14 Audio Context Sample Rate
**Issue**: 
- Frontend requests 16kHz but AudioContext uses native (48kHz typical)
- WAV created at AudioContext rate
- Backend resamples to 44.1kHz
- **Result**: Inconsistent sample rates cause MFCC differences

**Fix Applied**: Frontend now resamples to 44.1kHz before creating WAV

### ⚠️ POTENTIAL: #15 Recording Constraints
**Issue**: Echo cancellation, noise suppression may alter audio
**Impact**: Medium - Could affect features
**Status**: Cannot be disabled (browser requirement), but model should handle it

## Summary of Critical Issues

1. **Sample Rate Mismatch** (FIXED) - Frontend now resamples to 44.1kHz
2. **Asymmetric Quantization** (NEEDS FIX) - 16-bit PCM conversion is asymmetric
3. **Resampling Quality** (FIXED) - Now uses `kaiser_best` for browser recordings

## Next Fix: Asymmetric Quantization

The 16-bit PCM conversion uses:
- Negative: `sample * 0x8000` (range: -32768 to 0)
- Positive: `sample * 0x7FFF` (range: 0 to 32767)

This creates a DC bias. Should use symmetric quantization:
- Both: `sample * 32767` then clamp to [-32768, 32767]

