# Integration Guide: Speech Accent Detection

This guide explains how to integrate the accent detection model into your application.

## 📦 Required Files

Copy these files to your app directory:

### Essential Files (Required)
1. **`cnn_tunning.h5`** - The trained model (large file, ~50-100MB)
2. **`label_encoder.pkl`** - Label encoder mapping classes to indices
3. **`preprocess.py`** - Audio preprocessing function
4. **`accent_detector.py`** - Standalone detection module (NEW - use this!)

### Optional Files
- **`requirements.txt`** - Python dependencies
- **`app.py`** - Example Flask app (if you want to use as API)

## 🚀 Quick Start

### Option 1: Standalone Python Module (Recommended)

```python
from accent_detector import AccentDetector

# Initialize detector
detector = AccentDetector(
    model_path='cnn_tunning.h5',
    encoder_path='label_encoder.pkl'
)

# Predict accent from audio file
result = detector.predict('path/to/audio.mp3')
print(f"Accent: {result['accent']}")
print(f"Confidence: {result['confidence']}%")
print(f"Top 3: {result['top_n']}")
```

### Option 2: Flask API Integration

```python
from flask import Flask, request, jsonify
from accent_detector import AccentDetector

app = Flask(__name__)
detector = AccentDetector()

@app.route('/detect-accent', methods=['POST'])
def detect_accent():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    file.save('temp_audio.mp3')
    
    try:
        result = detector.predict('temp_audio.mp3')
        return jsonify(result)
    finally:
        os.remove('temp_audio.mp3')
```

### Option 3: Direct Integration (No Wrapper)

```python
import numpy as np
import pickle
from tensorflow.keras.models import load_model
from preprocess import preprocess_audio

# Load model and encoder
model = load_model('cnn_tunning.h5')
with open('label_encoder.pkl', 'rb') as f:
    label_encoder = pickle.load(f)

# Predict
audio_data = preprocess_audio('audio.mp3')
predictions = model.predict(audio_data, verbose=0)
predicted_idx = np.argmax(predictions, axis=1)[0]
accent = label_encoder.classes_[predicted_idx]
confidence = float(predictions[0][predicted_idx] * 100)
```

## 📋 Supported Audio Formats

- MP3
- WAV
- M4A
- FLAC
- WebM (browser recordings)
- OGG
- OPUS

## 🎯 Supported Accents (15 classes)

1. English
2. Mandarin
3. Japanese
4. Korean
5. Arabic
6. Hindi
7. Russian
8. Spanish
9. French
10. German
11. Italian
12. Thai
13. Thai
14. **Malayalam** (your accent)
15. **Tamil** (your accent)

## 📦 Dependencies

Install required packages:

```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install tensorflow>=2.13.0 numpy>=1.24.0 librosa>=0.10.0 soundfile>=0.12.0 scikit-learn>=1.3.0 scipy>=1.11.0
```

## 🔧 Integration Examples

### Example 1: Django Integration

```python
# views.py
from accent_detector import AccentDetector
from django.http import JsonResponse

detector = AccentDetector()

def detect_accent_view(request):
    if request.method == 'POST' and request.FILES.get('audio'):
        audio_file = request.FILES['audio']
        # Save temporarily
        with open('temp.mp3', 'wb') as f:
            f.write(audio_file.read())
        
        result = detector.predict('temp.mp3')
        os.remove('temp.mp3')
        return JsonResponse(result)
```

### Example 2: FastAPI Integration

```python
from fastapi import FastAPI, UploadFile, File
from accent_detector import AccentDetector

app = FastAPI()
detector = AccentDetector()

@app.post("/detect-accent")
async def detect_accent(audio: UploadFile = File(...)):
    # Save uploaded file
    with open('temp.mp3', 'wb') as f:
        f.write(await audio.read())
    
    result = detector.predict('temp.mp3')
    os.remove('temp.mp3')
    return result
```

### Example 3: React/JavaScript Frontend

```javascript
// Upload audio file to your backend API
const formData = new FormData();
formData.append('file', audioFile);

fetch('/api/detect-accent', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    console.log(`Accent: ${data.accent}`);
    console.log(`Confidence: ${data.confidence}%`);
});
```

## 📁 Directory Structure

Your app directory should look like:

```
your-app/
├── cnn_tunning.h5          # Model file
├── label_encoder.pkl       # Label encoder
├── preprocess.py           # Preprocessing function
├── accent_detector.py      # Detection module
├── your_app.py             # Your main app
└── requirements.txt        # Dependencies
```

## ⚠️ Important Notes

1. **Model File Size**: The `cnn_tunning.h5` file is large (~50-100MB). Make sure to include it in your deployment.

2. **Initialization**: The model loads once when `AccentDetector()` is created. Keep the instance alive for multiple predictions.

3. **Audio Length**: The model uses the first 5 seconds of audio. Longer files are automatically truncated.

4. **Sample Rate**: Audio is automatically resampled to 44.1kHz.

5. **Memory**: The model uses TensorFlow, which can be memory-intensive. Consider using GPU if available.

## 🐛 Troubleshooting

**Error: Model file not found**
- Ensure `cnn_tunning.h5` is in the same directory or provide full path

**Error: Label encoder not found**
- Ensure `label_encoder.pkl` is in the same directory or provide full path

**Error: Audio format not supported**
- Check that the file format is supported (MP3, WAV, etc.)
- For browser recordings, ensure WebM/OGG support is enabled

**Low accuracy**
- Ensure audio is clear and at least 1-2 seconds long
- Check that the audio contains speech (not silence)

## 📞 Support

If you encounter issues, check:
1. All required files are present
2. Dependencies are installed correctly
3. Audio file format is supported
4. Model and encoder files are not corrupted

