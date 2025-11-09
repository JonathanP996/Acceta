# 🚀 Quick Start Guide

## For the Next Developer/Prompt

This folder contains everything needed to integrate accent detection into your application.

## ⚡ 3-Step Setup

### 1. Install Dependencies
```bash
cd accent-detection-service
pip install -r requirements.txt
```

### 2. Start the Service
```bash
python app.py
```

Service runs on: `http://localhost:5001`

### 3. Test It
```bash
# Health check
curl http://localhost:5001/health

# Or open test_microphone.html in browser
```

## 📁 What's Included

| File | Purpose |
|------|---------|
| `app.py` | Flask API server (handles file uploads AND microphone recordings) |
| `accent_detector.py` | Main detection module |
| `preprocess.py` | Audio preprocessing (handles webm/ogg/mp3/wav) |
| `cnn_tunning.h5` | Trained model (7.6 MB) |
| `label_encoder.pkl` | Maps predictions to accent names |
| `requirements.txt` | Python dependencies |
| `test_microphone.html` | Test page for microphone recording |

## 🎤 Microphone Recording Support

**IMPORTANT**: The service fully supports microphone recordings (WebM/OGG format).

- ✅ File uploads work (MP3, WAV, etc.)
- ✅ Microphone recordings work (WebM, OGG)
- ✅ Both use the same `/detect-accent` endpoint
- ✅ Automatic format detection

## 🔧 Integration

### Frontend (JavaScript)
```javascript
// Record from microphone
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
const recorder = new MediaRecorder(stream);
const chunks = [];

recorder.ondataavailable = e => chunks.push(e.data);
recorder.onstop = async () => {
  const blob = new Blob(chunks, { type: 'audio/webm' });
  const formData = new FormData();
  formData.append('file', blob, 'recording.webm');
  
  const res = await fetch('http://localhost:5001/detect-accent', {
    method: 'POST',
    body: formData
  });
  
  const result = await res.json();
  console.log('Accent:', result.accent, result.confidence + '%');
};

recorder.start();
setTimeout(() => recorder.stop(), 5000);
```

### Backend (Node.js/Express)
```javascript
const multer = require('multer');
const axios = require('axios');
const FormData = require('form-data');

app.post('/detect-accent', upload.single('file'), async (req, res) => {
  const formData = new FormData();
  formData.append('file', fs.createReadStream(req.file.path));
  
  const response = await axios.post(
    'http://localhost:5001/detect-accent',
    formData,
    { headers: formData.getHeaders() }
  );
  
  res.json(response.data);
});
```

## ⚠️ Common Issues

### "Microphone doesn't work"
- ✅ Make sure file is sent with `.webm` or `.ogg` extension
- ✅ Use `FormData` with field name `file`
- ✅ Service automatically detects WebM/OGG format

### "No file provided"
- ✅ Form field must be named `file` (not `audio` or `recording`)
- ✅ Use `formData.append('file', blob, 'filename.webm')`

### "Model not found"
- ✅ Ensure `cnn_tunning.h5` and `label_encoder.pkl` are in same directory as `app.py`

## 📚 Full Documentation

See `INTEGRATION_INSTRUCTIONS.md` for:
- Complete API documentation
- React examples
- Node.js examples
- Troubleshooting guide
- Testing instructions

## ✅ Ready to Use!

Everything is set up and ready. Just:
1. Install dependencies
2. Start the service
3. Integrate using the examples above

The service handles both file uploads and microphone recordings automatically! 🎉

