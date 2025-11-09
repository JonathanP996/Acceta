# Accent Detection Service - Integration Instructions

This package contains everything needed to integrate accent detection into your application.

## 📦 Contents

- `cnn_tunning.h5` - Trained CNN model (7.6 MB)
- `label_encoder.pkl` - Label encoder mapping classes to indices
- `preprocess.py` - Audio preprocessing function (handles all formats including webm/ogg)
- `accent_detector.py` - Main detection module
- `app.py` - Flask API server
- `requirements.txt` - Python dependencies

## 🚀 Quick Setup

### 1. Install Dependencies

```bash
cd accent-detection-service
pip install -r requirements.txt
```

### 2. Start the Service

```bash
python app.py
```

The service will start on `http://localhost:5001`

### 3. Test the Service

```bash
# Health check
curl http://localhost:5001/health

# Test with audio file
curl -X POST -F "file=@audio.mp3" http://localhost:5001/detect-accent
```

## 🔌 API Endpoints

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "service": "accent-detection",
  "supported_classes": ["arabic", "english", "french", ...]
}
```

### POST /detect-accent
Detect accent from audio file.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Field: `file` (audio file)

**Supported Formats:**
- ✅ MP3, WAV, M4A, FLAC (uploaded files)
- ✅ WebM, OGG, Opus (microphone recordings)

**Response:**
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

## 🎤 Frontend Integration (Microphone Recording)

### JavaScript Example

```javascript
// Record audio from microphone
async function recordAndDetectAccent() {
  try {
    // Request microphone access
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    
    // Create MediaRecorder (records as WebM)
    const mediaRecorder = new MediaRecorder(stream);
    const chunks = [];
    
    mediaRecorder.ondataavailable = (event) => {
      chunks.push(event.data);
    };
    
    mediaRecorder.onstop = async () => {
      // Create blob from recorded chunks
      const audioBlob = new Blob(chunks, { type: 'audio/webm' });
      
      // Create FormData
      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.webm');
      
      // Send to API
      const response = await fetch('http://localhost:5001/detect-accent', {
        method: 'POST',
        body: formData
      });
      
      const result = await response.json();
      console.log('Detected accent:', result.accent);
      console.log('Confidence:', result.confidence + '%');
      
      // Stop microphone
      stream.getTracks().forEach(track => track.stop());
    };
    
    // Start recording
    mediaRecorder.start();
    
    // Stop after 5 seconds (or user clicks stop)
    setTimeout(() => {
      mediaRecorder.stop();
    }, 5000);
    
  } catch (error) {
    console.error('Error accessing microphone:', error);
  }
}
```

### React Example

```jsx
import { useState, useRef } from 'react';

function AccentDetector() {
  const [accent, setAccent] = useState(null);
  const [confidence, setConfidence] = useState(null);
  const [recording, setRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        chunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
        await detectAccent(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  };

  const detectAccent = async (audioBlob) => {
    const formData = new FormData();
    formData.append('file', audioBlob, 'recording.webm');

    try {
      const response = await fetch('http://localhost:5001/detect-accent', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();
      setAccent(result.accent);
      setConfidence(result.confidence);
    } catch (error) {
      console.error('Error detecting accent:', error);
    }
  };

  return (
    <div>
      <button onClick={recording ? stopRecording : startRecording}>
        {recording ? 'Stop Recording' : 'Start Recording'}
      </button>
      {accent && (
        <div>
          <p>Accent: {accent}</p>
          <p>Confidence: {confidence}%</p>
        </div>
      )}
    </div>
  );
}
```

## 🔧 Node.js/Express Integration

```javascript
const express = require('express');
const multer = require('multer');
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

const app = express();
const upload = multer({ dest: 'uploads/' });

app.post('/detect-accent', upload.single('file'), async (req, res) => {
  try {
    const formData = new FormData();
    formData.append('file', fs.createReadStream(req.file.path), {
      filename: req.file.originalname,
      contentType: req.file.mimetype
    });

    const response = await axios.post(
      'http://localhost:5001/detect-accent',
      formData,
      {
        headers: formData.getHeaders()
      }
    );

    // Clean up uploaded file
    fs.unlinkSync(req.file.path);

    res.json(response.data);
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({ error: error.message });
  }
});
```

## ⚠️ Important Notes

### Microphone Recording Format
- **Browser recordings are typically WebM or OGG format**
- The service automatically detects and handles these formats
- No conversion needed - `preprocess.py` handles WebM/OGG natively using librosa

### File Upload vs Microphone
- **File uploads**: MP3, WAV, M4A, FLAC work perfectly
- **Microphone recordings**: WebM, OGG, Opus work perfectly
- Both use the same `/detect-accent` endpoint
- The service automatically detects the format from file extension or content type

### Common Issues

**Issue: Microphone recording doesn't work**
- ✅ **Solution**: Make sure you're sending the file with the correct extension (`.webm` or `.ogg`)
- ✅ **Solution**: If no extension, the service defaults to `.webm` for microphone recordings
- ✅ **Solution**: Ensure `Content-Type` header is set correctly

**Issue: "No file provided" error**
- ✅ **Solution**: Make sure the form field is named `file` (not `audio` or `recording`)
- ✅ **Solution**: Use `FormData` with `formData.append('file', blob, 'filename.webm')`

**Issue: Model not found**
- ✅ **Solution**: Ensure `cnn_tunning.h5` and `label_encoder.pkl` are in the same directory as `app.py`

## 📊 Supported Accents (15 classes)

1. Arabic
2. English ⭐
3. French
4. German
5. Hindi
6. Italian
7. Japanese
8. Korean
9. Malayalam
10. Mandarin
11. Russian
12. Spanish
13. Tamil
14. Thai
15. Turkish

## 🔍 Testing

### Test with cURL

```bash
# Test health endpoint
curl http://localhost:5001/health

# Test with MP3 file
curl -X POST -F "file=@test.mp3" http://localhost:5001/detect-accent

# Test with WebM file (microphone recording)
curl -X POST -F "file=@recording.webm" http://localhost:5001/detect-accent
```

### Test in Browser Console

```javascript
// Record 5 seconds of audio
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
const recorder = new MediaRecorder(stream);
const chunks = [];

recorder.ondataavailable = e => chunks.push(e.data);
recorder.onstop = async () => {
  const blob = new Blob(chunks, { type: 'audio/webm' });
  const formData = new FormData();
  formData.append('file', blob, 'test.webm');
  
  const res = await fetch('http://localhost:5001/detect-accent', {
    method: 'POST',
    body: formData
  });
  
  const result = await res.json();
  console.log(result);
};

recorder.start();
setTimeout(() => recorder.stop(), 5000);
```

## 🚨 Troubleshooting

### Service won't start
- Check if port 5001 is already in use
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check Python version (requires Python 3.8+)

### Predictions are inaccurate
- Ensure you're using the correct model files (`cnn_tunning.h5`, `label_encoder.pkl`)
- Verify audio is at least 1 second long (model trained on 5-second clips)
- Check that preprocessing matches training (handled automatically)

### CORS errors
- The service has CORS enabled for all origins
- If issues persist, check browser console for specific error messages

## 📝 Next Steps

1. **Start the service**: `python app.py`
2. **Test with a file**: Use the cURL command above
3. **Integrate into your app**: Use the JavaScript/React examples
4. **Handle microphone**: Use MediaRecorder API as shown

The service is ready to use! 🎉

