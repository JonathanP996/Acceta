# Accent Detection App - Flow & Libraries Explanation

## 📋 Overview

This is a **speech accent classification system** that identifies a speaker's accent from audio recordings. It uses a **Convolutional Neural Network (CNN)** trained on MFCC (Mel-Frequency Cepstral Coefficients) audio features to classify accents into 15 different languages.

---

## 🔄 Complete Application Flow

### **Step 1: Service Startup** (`app.py`)
```
1. Flask app initializes
2. AccentDetector class is instantiated (loads model & encoder once)
3. Service listens on http://localhost:5001
```

**What happens:**
- `AccentDetector.__init__()` is called
- Loads `cnn_tunning.h5` (trained CNN model) into memory
- Loads `label_encoder.pkl` (maps class indices → accent names)
- Model stays in memory for fast predictions

### **Step 2: API Request** (Node.js → Python Service)
```
POST /detect-accent
Content-Type: multipart/form-data
Body: audio file (mp3, wav, m4a, flac, webm, ogg, opus)
```

**What happens:**
- Flask receives the file upload
- Saves file temporarily to `/tmp/` (cross-platform safe)
- Calls `detector.predict(temp_path)`

### **Step 3: Audio Preprocessing** (`preprocess.py`)
```
Raw Audio File → MFCC Features → Normalized Array
```

**Detailed steps:**

1. **Load Audio** (using `librosa.load()`)
   - Reads audio file (any format: mp3, wav, webm, etc.)
   - Converts to mono (single channel)
   - Resamples to 44,100 Hz (standard sample rate)
   - Returns: `y` (audio samples array), `sr` (sample rate)

2. **Truncate to 5 seconds**
   - Takes first 5 seconds only (220,500 samples at 44.1kHz)
   - Model was trained on 5-second clips

3. **Extract MFCC Features** (using `librosa.feature.mfcc()`)
   - **MFCC** = Mel-Frequency Cepstral Coefficients
   - Captures spectral characteristics of speech
   - Extracts 13 MFCC coefficients (standard for speech)
   - Returns: 2D array (13 coefficients × time frames)

4. **Normalize MFCC**
   - Mean normalization: `(mfcc - mean) / std`
   - Ensures features are on similar scales
   - Critical for neural network performance

5. **Average Across Time**
   - Takes mean of each MFCC coefficient across all time frames
   - Reduces from (13 × time_frames) → (13,)
   - Creates a single feature vector per audio file

6. **Reshape for Model**
   - Reshapes to `(1, 13, 1)` - batch size 1, 13 features, 1 channel
   - Matches the input shape the CNN expects

**Output:** NumPy array shape `(1, 13, 1)` ready for model prediction

### **Step 4: Model Prediction** (`accent_detector.py`)
```
MFCC Features → CNN Model → Probability Scores → Accent Name
```

**Detailed steps:**

1. **Feed to CNN Model** (using `model.predict()`)
   - Input: `(1, 13, 1)` MFCC features
   - Model processes through convolutional layers
   - Output: Probability array shape `(1, 15)` - one probability per accent class

2. **Get Top Prediction**
   - `np.argmax()` finds index with highest probability
   - Example: Index 1 = "english" with 95.2% confidence

3. **Decode Class Name** (using `label_encoder`)
   - Converts index (e.g., 1) → accent name (e.g., "english")
   - Label encoder was saved during training

4. **Get Top N Predictions**
   - Sorts all probabilities
   - Returns top 3 (or N) with confidence scores
   - Example: ["english: 95.2%", "spanish: 3.1%", "french: 1.7%"]

**Output:** Dictionary with:
```python
{
    'accent': 'english',
    'confidence': 95.2,
    'top_n': [
        {'accent': 'english', 'confidence': 95.2},
        {'accent': 'spanish', 'confidence': 3.1},
        {'accent': 'french', 'confidence': 1.7}
    ]
}
```

### **Step 5: Response** (Python Service → Node.js)
```
JSON Response → Node.js Backend → Frontend
```

**What happens:**
- Flask returns JSON response
- Temporary audio file is deleted
- Node.js receives result and can display to user

---

## 📚 Libraries & Their Roles

### **Core Libraries (Actively Used)**

#### 1. **librosa** (`librosa>=0.10.0`)
**Purpose:** Audio processing and feature extraction

**Used for:**
- `librosa.load()` - Loads audio files in any format (mp3, wav, webm, ogg, opus, etc.)
  - Automatically resamples to target sample rate
  - Converts to mono channel
  - Handles different audio codecs
- `librosa.feature.mfcc()` - Extracts MFCC features from audio
  - Converts raw audio → spectral features
  - Captures speech characteristics (formants, pitch, etc.)
  - Returns 13 coefficients (standard for speech recognition)

**Why it's essential:** Without librosa, we'd need separate libraries for each audio format and manual MFCC calculation.

---

#### 2. **TensorFlow/Keras** (`tensorflow>=2.13.0`)
**Purpose:** Deep learning model loading and inference

**Used for:**
- `load_model()` - Loads the trained CNN model from `cnn_tunning.h5`
- `model.predict()` - Runs inference on preprocessed audio features
  - Processes MFCC features through convolutional layers
  - Returns probability distribution over 15 accent classes

**Model Architecture (what's inside `cnn_tunning.h5`):**
- 3 Conv1D layers (64, 128, 256 filters)
- BatchNormalization layers
- MaxPooling layers
- Dense layers (512, 256 neurons)
- Dropout for regularization
- Output: 15 classes (softmax activation)

**Why it's essential:** The entire accent classification happens inside this model.

---

#### 3. **NumPy** (`numpy>=1.24.0`)
**Purpose:** Numerical operations and array manipulation

**Used for:**
- Array operations on audio data
- MFCC normalization: `(mfcc - np.mean(mfcc)) / np.std(mfcc)`
- Averaging across time: `np.mean(mfcc, axis=1)`
- Reshaping arrays: `mfcc_mean.reshape(1, -1, 1)`
- Finding max probability: `np.argmax(predictions)`
- Sorting predictions: `np.argsort(predictions[0])`

**Why it's essential:** All audio data and model outputs are NumPy arrays. Required for mathematical operations.

---

#### 4. **Flask** (`flask>=3.0.0`)
**Purpose:** Web framework for REST API

**Used for:**
- Creating HTTP endpoints (`/health`, `/detect-accent`)
- Handling file uploads from Node.js backend
- Returning JSON responses
- CORS support for cross-origin requests

**Why it's essential:** Provides the API interface between Node.js and Python model.

---

#### 5. **flask-cors** (`flask-cors>=4.0.0`)
**Purpose:** Cross-Origin Resource Sharing support

**Used for:**
- Enabling CORS headers so Node.js backend can call Python service
- Prevents browser CORS errors

**Why it's essential:** Without it, Node.js requests from different ports would be blocked.

---

#### 6. **scikit-learn** (`scikit-learn>=1.3.0`)
**Purpose:** Machine learning utilities

**Used for:**
- `LabelEncoder` - Maps class indices ↔ accent names
  - During training: "english" → 1, "spanish" → 2, etc.
  - During inference: 1 → "english", 2 → "spanish", etc.
- Saved as `label_encoder.pkl` using pickle

**Why it's essential:** Converts model's numerical predictions back to human-readable accent names.

---

#### 7. **pickle** (built-in Python)
**Purpose:** Serialization/deserialization

**Used for:**
- Saving `LabelEncoder` object to `label_encoder.pkl`
- Loading `LabelEncoder` back from file

**Why it's essential:** Preserves the class-to-index mapping from training.

---

### **Supporting Libraries (Dependencies)**

#### 8. **soundfile** (`soundfile>=0.12.0`)
**Purpose:** Backend for librosa (reads certain audio formats)

**Note:** Not directly imported, but librosa uses it internally for reading WAV, FLAC files.

---

#### 9. **scipy** (`scipy>=1.11.0`)
**Purpose:** Scientific computing (used by librosa/numpy)

**Note:** Not directly used, but required by librosa for signal processing.

---

#### 10. **Werkzeug** (`Werkzeug>=3.0.0`)
**Purpose:** WSGI utility library (used by Flask)

**Note:** Flask dependency, handles HTTP request/response processing.

---

### **Optional Libraries (Not Used in Service)**

#### 11. **pandas** (`pandas>=2.0.0`)
**Status:** Not used in service code (only needed for training)

#### 12. **tqdm** (`tqdm>=4.66.0`)
**Status:** Not used in service code (only needed for training progress bars)

---

## 🎯 Data Flow Summary

```
┌─────────────────┐
│  Audio File     │  (mp3, wav, webm, etc.)
│  (Raw Audio)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  librosa.load() │  → Load & resample to 44.1kHz
│  (Preprocess)   │  → Convert to mono
└────────┬────────┘  → Truncate to 5 seconds
         │
         ▼
┌─────────────────┐
│  librosa.feature│  → Extract 13 MFCC coefficients
│  .mfcc()        │  → Normalize features
└────────┬────────┘  → Average across time
         │            → Reshape to (1, 13, 1)
         ▼
┌─────────────────┐
│  CNN Model      │  → Conv1D layers process features
│  (TensorFlow)   │  → Dense layers classify
└────────┬────────┘  → Output: 15 probabilities
         │
         ▼
┌─────────────────┐
│  Label Encoder  │  → Convert index → accent name
│  (scikit-learn) │  → Get top N predictions
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  JSON Response  │  → {accent, confidence, top_n}
└─────────────────┘
```

---

## 🔑 Key Concepts

### **MFCC (Mel-Frequency Cepstral Coefficients)**
- **What:** Mathematical representation of audio that captures speech characteristics
- **Why:** Neural networks work better on features than raw audio
- **How:** Converts audio → frequency domain → mel scale → cepstral coefficients
- **Result:** 13 numbers that represent the "accent fingerprint"

### **CNN (Convolutional Neural Network)**
- **What:** Deep learning model that learns patterns in MFCC features
- **Architecture:** 1D convolutions (because MFCC is 1D sequence)
- **Training:** Trained on thousands of audio samples from 15 accents
- **Output:** Probability distribution over 15 accent classes

### **Label Encoder**
- **What:** Maps between class indices (0-14) and accent names
- **Example:** 
  - Index 0 → "arabic"
  - Index 1 → "english"
  - Index 2 → "french"
  - etc.
- **Why:** Models output numbers, but we need human-readable names

---

## 📁 File Structure

```
python-service/
├── app.py                 # Flask API server
├── accent_detector.py     # Main detection class
├── preprocess.py          # Audio → MFCC conversion
├── cnn_tunning.h5        # Trained CNN model (7.6 MB)
├── label_encoder.pkl     # Class index → name mapping
└── requirements.txt      # Python dependencies
```

---

## 🚀 API Endpoints

### **GET /health**
- **Purpose:** Health check
- **Response:**
```json
{
  "status": "ok",
  "service": "accent-detection",
  "supported_classes": ["arabic", "english", "french", ...]
}
```

### **POST /detect-accent**
- **Purpose:** Detect accent from audio file
- **Request:** `multipart/form-data` with `file` field
- **Response:**
```json
{
  "accent": "english",
  "confidence": 95.2,
  "top_n": [
    {"accent": "english", "confidence": 95.2},
    {"accent": "spanish", "confidence": 3.1},
    {"accent": "french", "confidence": 1.7}
  ]
}
```

---

## 💡 Quick Summary for Another Prompt

**What it does:** Classifies speech accents from audio files using a CNN model.

**Key libraries:**
- **librosa** - Loads audio and extracts MFCC features
- **TensorFlow** - Runs the trained CNN model for classification
- **Flask** - Provides REST API endpoint
- **NumPy** - Handles all array operations
- **scikit-learn** - Maps predictions to accent names

**Flow:**
1. Audio file uploaded → Flask receives it
2. librosa loads audio → extracts MFCC features
3. CNN model processes MFCC → returns probabilities
4. Label encoder converts index → accent name
5. JSON response returned to Node.js

**No speech-to-text:** This is accent classification only, not transcription (no Whisper or similar).

