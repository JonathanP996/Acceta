# Accent Scoring Pipeline - Complete Explanation

## Overview
This document explains step-by-step how accent scores are calculated from audio input.

---

## Step-by-Step Scoring Process

### **STEP 1: Audio Transcription (Whisper)**
- **Input**: Audio file (WAV format)
- **Process**: Whisper API transcribes speech to text
- **Output**: `transcribed_text` (e.g., "The quick brown fox jumps over the lazy dog")
- **Purpose**: Get the words the user said

---

### **STEP 2: Phoneme Alignment**
- **Input**: Transcribed text + audio file
- **Process**: 
  - Converts words to phonemes using dictionary (e.g., "the" → `['DH', 'AH']`)
  - Aligns phonemes to audio timeline (start/end times)
- **Output**: `phoneme_segments` - List of phonemes with timing
  ```python
  [
    {"phoneme": "DH", "start": 0.0, "end": 0.05, "duration": 0.05},
    {"phoneme": "AH", "start": 0.05, "end": 0.12, "duration": 0.07},
    ...
  ]
  ```
- **Purpose**: Break speech into individual sounds (phonemes) for analysis

---

### **STEP 3: Acoustic Feature Extraction (Librosa)**
- **Input**: Audio file + phoneme segments
- **Process**: For each phoneme segment, extract:
  - **MFCCs** (Mel-frequency cepstral coefficients) - 13 features describing spectral shape
  - **Pitch** (fundamental frequency) - Hz value
  - **Formants** (F1, F2, F3) - Vowel quality indicators
  - **Intensity** (RMS energy) - How loud
  - **Duration** - How long the phoneme lasts
- **Output**: `acoustic_features`
  ```python
  {
    "pitch_contour": [230.0, 225.0, 240.0, ...],  # Pitch over time
    "intensity": 0.0399,  # Average intensity
    "formant_ratios": [0.6, 1.2, 1.8],  # F1, F2, F3 ratios
    "per_phoneme_features": [
      {
        "phoneme": "DH",
        "pitch": 230.0,
        "intensity": 0.04,
        "duration": 0.05,
        "mfcc_mean": [12.5, -3.2, 1.8, ...]
      },
      ...
    ]
  }
  ```
- **Purpose**: Get measurable acoustic properties of each sound

---

### **STEP 4: Feature Normalization**
- **Input**: Raw acoustic features
- **Process**: Normalize to remove personal voice characteristics:
  - **Pitch normalization**: Convert to relative pitch (deviation from speaker's mean)
    - Example: If your mean pitch is 230Hz, normalize to relative deviations
  - **Intensity normalization**: Map to 0-1 scale (more lenient: `(intensity - 0.01) / 0.99`)
- **Output**: Normalized features
- **Purpose**: Focus on accent patterns, not voice identity

---

### **STEP 5: Reference Distribution Lookup**
- **Input**: Target accent (e.g., "american")
- **Process**: Get reference statistics for that accent:
  ```python
  {
    "pitch": {
      "mean": 180.0,      # Average pitch for American English
      "std": 30.0,        # Standard deviation
      "min": 120.0,       # Acceptable range
      "max": 280.0
    },
    "intensity": {
      "mean": 0.6,
      "std": 0.2,
      "min": 0.2,
      "max": 1.0
    },
    "vowel_duration": {
      "mean": 0.15,
      "std": 0.05,
      "min": 0.08,
      "max": 0.25
    },
    ...
  }
  ```
- **Purpose**: Know what "correct" sounds like for the target accent

---

### **STEP 6: Per-Phoneme Deviation Calculation**
For EACH phoneme, calculate how well it matches the target accent:

#### 6a. Pitch Probability
- **Your pitch**: e.g., 230 Hz
- **Reference range**: 120-280 Hz (American)
- **Calculation**:
  - If within range → High probability (0.7-1.0)
    - `pitch_prob = max(0.7, 1.0 - (distance_from_mean / max_distance) * 0.3)`
  - If outside range → Lower probability based on z-score
    - `pitch_prob = max(0.0, 1.0 - min(1.0, z_score / 2.0))`

#### 6b. Intensity Probability
- **Your intensity**: e.g., 0.04 (normalized)
- **Calculation**:
  - If intensity > 0.1 → `intensity_prob = 0.8` (default high)
  - If very low → `intensity_prob = max(0.5, ...)` (minimum 0.5)

#### 6c. Duration Probability
- **Your duration**: e.g., 0.05 seconds
- **Reference**: Vowels: 0.08-0.25s, Consonants: 0.05-0.15s
- **Calculation**:
  - If within range → High probability (0.7-0.85)
  - If outside → Lower probability based on z-score

#### 6d. MFCC Probability
- **Your MFCCs**: 13 coefficients
- **Calculation**: Default `mfcc_prob = 0.8` (very lenient)
  - Only reduces to 0.6 if extremely different

#### 6e. Formant Probability
- **Your formants**: [0.6, 1.2, 1.8]
- **Reference formants**: [0.6, 1.2, 1.8] (American)
- **Calculation**: Compare each formant, take minimum

#### 6f. Combine Probabilities
```python
combined_prob = (
    pitch_prob * 0.25 +      # 25% weight
    intensity_prob * 0.15 +   # 15% weight
    duration_prob * 0.20 +    # 20% weight
    mfcc_prob * 0.20 +        # 20% weight
    formant_match_prob * 0.20 # 20% weight
)
```

#### 6g. Boosts Applied
- If `combined_prob < 0.5` but valid speech → Boost by 50% (minimum 0.5)
- If pitch AND duration both within range → Extra 10% boost

#### 6h. Convert to Deviation
```python
deviation = 1.0 - combined_prob
# deviation = 0.0 means perfect match
# deviation = 1.0 means completely wrong
```

---

### **STEP 7: Final Score Adjustments**

#### 7a. Native Boost (if average deviation < 0.5)
```python
if avg_deviation < 0.5:
    boost_factor = 0.6 if avg_dev < 0.3 else 0.7
    # Multiply all deviations by boost_factor (reduces them)
    deviations[phoneme] = deviations[phoneme] * boost_factor
```

#### 7b. Pitch Range Boost (if pitch within native range)
```python
if pitch_within_range:
    # Additional 15% reduction
    deviations[phoneme] = deviations[phoneme] * 0.85
```

#### 7c. Calculate Final Score
```python
avg_deviation = sum(all_deviations) / len(deviations)
final_accent_score = (1.0 - avg_deviation) * 100
```

---

## Example Calculation

Let's say you said "the" and your features are:
- **Pitch**: 230 Hz (within 120-280 range ✅)
- **Intensity**: 0.04 (normalized: 0.0302)
- **Duration**: 0.05s (consonant, within 0.05-0.15 range ✅)

### Step-by-step:
1. **Pitch prob**: 230Hz is within range → `pitch_prob = 0.85` (high)
2. **Intensity prob**: 0.0302 < 0.1 → `intensity_prob = 0.5` (minimum)
3. **Duration prob**: 0.05s is within range → `duration_prob = 0.85` (high)
4. **MFCC prob**: Default → `mfcc_prob = 0.8`
5. **Formant prob**: Assume good → `formant_prob = 0.8`

6. **Combine**:
   ```
   combined = 0.85*0.25 + 0.5*0.15 + 0.85*0.20 + 0.8*0.20 + 0.8*0.20
            = 0.2125 + 0.075 + 0.17 + 0.16 + 0.16
            = 0.7775
   ```

7. **Boost check**: 0.7775 > 0.5, but let's check if both pitch and duration are good:
   - Pitch good ✅, Duration good ✅ → Extra 10% boost
   - `combined = 0.7775 * 1.1 = 0.855`

8. **Deviation**: `deviation = 1.0 - 0.855 = 0.145`

9. **Native boost**: avg_dev < 0.5 → Apply boost factor 0.7
   - `deviation = 0.145 * 0.7 = 0.1015`

10. **Pitch boost**: Pitch within range → Additional 15% reduction
    - `deviation = 0.1015 * 0.85 = 0.0863`

11. **Final score**: `score = (1.0 - 0.0863) * 100 = 91.37%`

---

## Potential Issues Identified

### Issue 1: Intensity Normalization Too Strict
- **Problem**: Intensity of 0.04 normalizes to 0.0302, which triggers minimum probability (0.5)
- **Impact**: Even with good pitch/duration, intensity drags down the score
- **Fix Needed**: Intensity should be less penalized or normalized differently

### Issue 2: Per-Phoneme Features May Not Match Phonemes
- **Problem**: If `per_phoneme_features` array doesn't align with `phoneme_segments`, wrong features are used
- **Impact**: Phoneme "DH" might get features from phoneme "AH"
- **Fix Needed**: Ensure alignment is correct

### Issue 3: Global Formant Probability Applied to All Phonemes
- **Problem**: `formant_match_prob` is calculated globally but applied to each phoneme
- **Impact**: Vowel formants affect consonant scores (shouldn't)
- **Fix Needed**: Only apply formants to vowels

### Issue 4: Intensity Minimum Too Low
- **Problem**: Minimum intensity probability is 0.5, but it's weighted at 15%
- **Impact**: Even with good pronunciation, low intensity reduces score
- **Fix Needed**: Increase minimum or reduce weight further

### Issue 5: Combined Probability Boost May Not Be Enough
- **Problem**: Boost only applies if `combined_prob < 0.5`
- **Impact**: Scores between 0.5-0.7 don't get boosted even if features are good
- **Fix Needed**: Apply boost more broadly

---

## Current Formula Summary

```
For each phoneme:
  1. Calculate pitch_prob (0.0-1.0)
  2. Calculate intensity_prob (0.0-1.0, minimum 0.5)
  3. Calculate duration_prob (0.0-1.0)
  4. Calculate mfcc_prob (default 0.8)
  5. Calculate formant_prob (global, 0.0-1.0)
  
  6. combined_prob = weighted_average(above)
  7. Apply boosts if conditions met
  8. deviation = 1.0 - combined_prob
  
After all phonemes:
  9. avg_deviation = mean(all_deviations)
  10. Apply native boost (if avg < 0.5)
  11. Apply pitch boost (if pitch in range)
  12. final_score = (1.0 - avg_deviation) * 100
```

---

## Recommendations for Fixing Low Scores

1. **Increase intensity minimum probability** from 0.5 to 0.7
2. **Reduce intensity weight** from 15% to 10%
3. **Apply formant probability only to vowels**, not consonants
4. **Widen boost conditions** - apply boost if `combined_prob < 0.7` instead of 0.5
5. **Check phoneme-feature alignment** - ensure features match correct phonemes
6. **Add logging** to show which features are causing low scores

