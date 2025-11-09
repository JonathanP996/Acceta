# 🧠 Why Your .h5 Model Gives Different Results After Copying Projects

If your TensorFlow/Keras `.h5` model gives different predictions in a new project — even though you copied the same file — it's because **the environment or preprocessing pipeline isn't identical**.

Below are the main causes and fixes 👇

---

## ⚙️ 1. Different Preprocessing Pipeline

Your model expects audio features (MFCCs, mel spectrograms, normalization, etc.) in a **very specific format**.

If your new project uses:

- Different **sampling rate** (e.g., 16kHz vs 44.1kHz)
- Different **frame size** / **hop length**
- Different **feature normalization** or **scaling**
- Different **library version** (e.g., `librosa` 0.10 vs 0.8)
- Different **resampling algorithm** (e.g., `kaiser_fast` vs `kaiser_best`)

Then the input tensor changes, and so do results.

✅ **Fix:**

Copy the **exact same preprocessing code** from the training project — not just the model.

**Our Preprocessing Requirements:**
- Sample rate: **44100 Hz** (not 16kHz!)
- MFCC coefficients: **13** (`n_mfcc=13`)
- Audio duration: **First 5 seconds** (truncated if longer)
- Normalization: **Global mean/std normalization** of MFCC features
- Resampling: **Default** for MP3 files, **`kaiser_best`** for microphone recordings (WebM/OGG/WAV)
- Output shape: **(1, 13, 1)** - mean of MFCC coefficients across time, reshaped

---

## ⚙️ 2. Model Loading Differences

TensorFlow models can include:

- Custom layers
- Lambda functions
- Custom loss or activation functions

If those weren't declared on load, TensorFlow might silently replace them.

✅ **Fix:**

```python
from tensorflow.keras.models import load_model

# If you have custom objects, specify them:
# model = load_model("model.h5", custom_objects={'CustomLayer': CustomLayer})

# For our model, standard loading works:
model = load_model("cnn_tunning.h5")
```

---

## ⚙️ 3. TensorFlow Version Mismatch

Even minor version changes alter kernel math.

✅ **Fix:**

Match the original version used for training:

```bash
pip install tensorflow==2.13.0  # Or match your training environment
```

Check your `requirements.txt` for exact versions.

---

## ⚙️ 4. Normalization / Scaling Mismatch

Your training pipeline may have normalized MFCCs like:

```python
mfcc = (mfcc - np.mean(mfcc)) / np.std(mfcc)
```

If you skipped this or recomputed with different mean/std, the model's inputs are on the wrong scale.

✅ **Fix:**

Re-use the exact same feature normalization parameters.

**Our Normalization:**
```python
# Extract MFCC
mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)

# Normalize MFCC (GLOBAL normalization - mean/std of entire MFCC matrix)
mfcc = (mfcc - np.mean(mfcc)) / np.std(mfcc)

# Calculate mean across time (reduces from 2D to 1D)
mfcc_mean = np.mean(mfcc, axis=1)

# Reshape to match training: (1, n_features, 1)
mfcc_mean = mfcc_mean.reshape(1, -1, 1)
```

**⚠️ Critical:** The normalization is **global** (mean/std of entire MFCC matrix), not per-coefficient!

---

## ⚙️ 5. Dropout or BatchNorm Still Active

If dropout or batch normalization is still in *training mode*, inference will differ run-to-run.

✅ **Fix:**

Make sure you're in inference mode:

```python
import tensorflow as tf

# Set learning phase to 0 (inference mode)
tf.keras.backend.set_learning_phase(0)

# Or ensure dropout is off (our model handles this automatically)
model = load_model("cnn_tunning.h5")
model.evaluate()  # This sets inference mode
```

**Note:** Our model should handle this automatically, but if you see inconsistent results, explicitly set inference mode.

---

## ⚙️ 6. Audio Format or Resampling Differences

Even `.wav` encoding or resampling can alter raw waveform values.

✅ **Fix:**

Always standardize audio input:

```python
import librosa

# For standard files (MP3, etc.)
y, sr = librosa.load(audio_path, sr=44100)

# For microphone recordings (WebM/OGG converted to WAV)
y, sr = librosa.load(audio_path, sr=44100, res_type='kaiser_best')
```

**Our Resampling Strategy:**
- **MP3/Standard files:** Default librosa resampling (matches training)
- **Microphone recordings (WebM/OGG/WAV from browser):** `kaiser_best` resampling (handles conversion artifacts)

---

## ⚙️ 7. Label Encoder Mismatch

The model outputs class indices, not class names. You need the **exact same label encoder** used during training.

✅ **Fix:**

Copy `label_encoder.pkl` along with the model:

```python
import pickle

with open('label_encoder.pkl', 'rb') as f:
    label_encoder = pickle.load(f)

# Use it to decode predictions
predicted_class = label_encoder.classes_[predicted_class_idx]
```

**⚠️ Critical:** The label encoder must match the training order exactly!

---

## ⚙️ 8. Input Shape Mismatch

The model expects a specific input shape. If you reshape differently, predictions will be wrong.

✅ **Fix:**

Match the exact input shape from training:

```python
# Our model expects: (batch_size, 13, 1)
# Where 13 is the number of MFCC coefficients
# And we take the mean across time before reshaping

mfcc_mean = np.mean(mfcc, axis=1)  # Shape: (13,)
mfcc_mean = mfcc_mean.reshape(1, -1, 1)  # Shape: (1, 13, 1)
```

---

# 🧩 Diagnostic Script to Compare Projects

Use this to check whether your new project's preprocessing or inference differs from the original:

```python
import numpy as np
import librosa
from tensorflow.keras.models import load_model
import pickle

def extract_features(path, is_microphone=False):
    """
    Extract features EXACTLY as our preprocessing does.
    """
    target_sample_rate = 44100
    n_mfcc = 13
    
    # Load audio with correct resampling
    file_ext = os.path.splitext(path)[1].lower()
    if file_ext in ['.webm', '.ogg', '.opus'] or (file_ext == '.wav' and is_microphone):
        y, sr = librosa.load(path, sr=target_sample_rate, mono=True, res_type='kaiser_best')
    else:
        y, sr = librosa.load(path, sr=target_sample_rate)
    
    # Extract first 5 seconds
    samples_5_sec = target_sample_rate * 5
    if len(y) > samples_5_sec:
        y = y[:samples_5_sec]
    
    # Extract MFCC
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    
    # Normalize (GLOBAL normalization)
    mfcc = (mfcc - np.mean(mfcc)) / np.std(mfcc)
    
    # Mean across time
    mfcc_mean = np.mean(mfcc, axis=1)
    
    # Reshape
    mfcc_mean = mfcc_mean.reshape(1, -1, 1)
    
    return mfcc_mean

# Load models and encoders
orig_model = load_model("original/cnn_tunning.h5")
new_model = load_model("new/cnn_tunning.h5")

with open("original/label_encoder.pkl", 'rb') as f:
    orig_encoder = pickle.load(f)
with open("new/label_encoder.pkl", 'rb') as f:
    new_encoder = pickle.load(f)

# Test with same audio file
audio_path = "test_audio.mp3"

# Extract features
orig_features = extract_features(audio_path, is_microphone=False)
new_features = extract_features(audio_path, is_microphone=False)

# Compare features
features_match = np.allclose(orig_features, new_features, atol=1e-6)
print(f"✅ Same preprocessing? {features_match}")
if not features_match:
    print(f"   Max difference: {np.max(np.abs(orig_features - new_features))}")
    print(f"   Mean difference: {np.mean(np.abs(orig_features - new_features))}")

# Compare model outputs
orig_pred = orig_model.predict(orig_features, verbose=0)
new_pred = new_model.predict(new_features, verbose=0)

outputs_match = np.allclose(orig_pred, new_pred, atol=1e-6)
print(f"✅ Same outputs? {outputs_match}")
if not outputs_match:
    print(f"   Max difference: {np.max(np.abs(orig_pred - new_pred))}")
    print(f"   Mean difference: {np.mean(np.abs(orig_pred - new_pred))}")

# Compare predictions
orig_class_idx = np.argmax(orig_pred[0])
new_class_idx = np.argmax(new_pred[0])

orig_class = orig_encoder.classes_[orig_class_idx]
new_class = new_encoder.classes_[new_class_idx]

print(f"✅ Same prediction? {orig_class == new_class}")
print(f"   Original: {orig_class} ({orig_pred[0][orig_class_idx]*100:.2f}%)")
print(f"   New:      {new_class} ({new_pred[0][new_class_idx]*100:.2f}%)")

if not features_match or not outputs_match or orig_class != new_class:
    print("\n❌ Differences found! Check:")
    print("   1. Preprocessing code matches exactly")
    print("   2. TensorFlow version matches")
    print("   3. Librosa version matches")
    print("   4. Input shape matches")
    print("   5. Normalization method matches")
else:
    print("\n✅ Everything matches! Models should give identical results.")
```

---

# 📋 Summary Checklist

| Issue | Fix | Our Specific Values |
|-------|-----|---------------------|
| Different MFCC params | Copy preprocessing code exactly | `n_mfcc=13`, `sr=44100` |
| Different TF version | Match TensorFlow versions | `tensorflow>=2.13.0` |
| Custom layers missing | Use `custom_objects` when loading | Not needed for our model |
| Feature normalization mismatch | Use same mean/std values | Global normalization: `(mfcc - mean) / std` |
| Dropout or BatchNorm active | Set inference mode | Model handles automatically |
| Audio format mismatch | Resample & normalize audio consistently | `sr=44100`, `res_type='kaiser_best'` for mic |
| Label encoder missing | Copy `label_encoder.pkl` | Must match training order |
| Input shape mismatch | Match exact shape | `(1, 13, 1)` |
| Sample rate mismatch | Use 44100 Hz | **Not 16kHz!** |
| Resampling algorithm | Match resampling type | Default for MP3, `kaiser_best` for mic |

---

# 📦 Required Files for Model Consistency

When copying the model to a new project, you **MUST** include:

1. ✅ **`cnn_tunning.h5`** - The trained model
2. ✅ **`label_encoder.pkl`** - The label encoder (maps indices to class names)
3. ✅ **`preprocess.py`** - The exact preprocessing function
4. ✅ **`requirements.txt`** - Exact library versions

**Do NOT:**
- ❌ Change preprocessing parameters
- ❌ Use different sample rates
- ❌ Skip normalization
- ❌ Use different resampling algorithms
- ❌ Reshape features differently

---

# 💡 Best Practice: Package Everything Together

Always package your trained model **together with its preprocessing pipeline**:

```
accent-detection-model/
├── cnn_tunning.h5              # Model file
├── label_encoder.pkl            # Label encoder
├── preprocess.py                # Preprocessing function (EXACT copy)
├── accent_detector.py           # Wrapper class (optional but recommended)
├── requirements.txt             # Exact library versions
└── README.md                    # Usage instructions
```

**Example `accent_detector.py` wrapper:**

```python
from accent_detector import AccentDetector

# This ensures consistent preprocessing
detector = AccentDetector(
    model_path='cnn_tunning.h5',
    encoder_path='label_encoder.pkl'
)

result = detector.predict('audio.mp3')
print(f"Accent: {result['accent']}, Confidence: {result['confidence']}%")
```

---

# 🔍 Quick Debugging Steps

If predictions are different:

1. **Check preprocessing output shape:**
   ```python
   features = preprocess_audio('test.mp3')
   print(f"Shape: {features.shape}")  # Should be (1, 13, 1)
   ```

2. **Check model input shape:**
   ```python
   print(model.input_shape)  # Should match your preprocessing output
   ```

3. **Compare feature values:**
   ```python
   # In original project
   orig_features = preprocess_audio('test.mp3')
   print(orig_features.flatten())
   
   # In new project
   new_features = preprocess_audio('test.mp3')
   print(new_features.flatten())
   
   # Should be identical!
   ```

4. **Check library versions:**
   ```bash
   pip list | grep -E "tensorflow|librosa|numpy"
   ```

5. **Verify label encoder:**
   ```python
   print(list(label_encoder.classes_))  # Should match training classes
   ```

---

# ✅ Our Exact Preprocessing Code

Here's the **exact** preprocessing function that must be used:

```python
import numpy as np
import librosa
import os

def preprocess_audio(file_path, target_sample_rate=44100, n_mfcc=13, is_microphone_recording=False):
    """
    Preprocess audio file for accent classification.
    EXACTLY matches the preprocess_audio function from training.
    
    Args:
        file_path: Path to the audio file
        target_sample_rate: Target sample rate (default 44100)
        n_mfcc: Number of MFCC coefficients (default 13)
        is_microphone_recording: If True, uses high-quality resampling for microphone recordings
    
    Returns:
        Preprocessed MFCC features ready for model prediction
    """
    # Check file extension to determine reading method
    file_ext = os.path.splitext(file_path)[1].lower()
    
    # For webm/ogg/opus files (browser recordings), use librosa directly with high-quality resampling
    # For WAV files from microphone (converted from WebM), also use high-quality resampling
    # For other formats (MP3, etc.), use default resampling to match training
    if file_ext in ['.webm', '.ogg', '.opus']:
        # Browser recordings - use high-quality resampling
        y, sr = librosa.load(file_path, sr=target_sample_rate, mono=True, res_type='kaiser_best')
    elif file_ext == '.wav' and is_microphone_recording:
        # WAV files from microphone (converted from WebM) - use high-quality resampling
        y, sr = librosa.load(file_path, sr=target_sample_rate, mono=True, res_type='kaiser_best')
    else:
        # Match training exactly: use librosa.load() which automatically resamples to target_sample_rate
        # Default resampling for MP3 and other file uploads (matches training)
        y, sr = librosa.load(file_path, sr=target_sample_rate)
    
    # Extract the first 5 seconds (matching training exactly)
    samples_5_sec = target_sample_rate * 5
    if len(y) > samples_5_sec:
        y = y[:samples_5_sec]
    
    # Extract MFCC (matching training exactly)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    
    # Normalize MFCC (GLOBAL normalization - matching training exactly)
    mfcc = (mfcc - np.mean(mfcc)) / np.std(mfcc)
    
    # Calculate mean of each MFCC coefficient across time (same as in training)
    mfcc_mean = np.mean(mfcc, axis=1)
    
    # Reshape to match training data format: (1, n_features, 1)
    mfcc_mean = mfcc_mean.reshape(1, -1, 1)
    
    return mfcc_mean
```

**⚠️ DO NOT MODIFY THIS CODE!** Any changes will break model consistency.

---

# 🎯 Final Checklist Before Deployment

- [ ] Copied `cnn_tunning.h5` model file
- [ ] Copied `label_encoder.pkl` encoder file
- [ ] Copied `preprocess.py` with exact same code
- [ ] Installed exact library versions from `requirements.txt`
- [ ] Verified TensorFlow version matches training environment
- [ ] Verified Librosa version matches training environment
- [ ] Tested preprocessing output shape: `(1, 13, 1)`
- [ ] Tested with same audio file in both projects
- [ ] Verified predictions match between projects
- [ ] Set inference mode (if needed)
- [ ] Handled microphone recordings correctly (if applicable)

---

**💡 Remember:** The model file alone is not enough. The preprocessing pipeline is **equally critical** for consistent results!

