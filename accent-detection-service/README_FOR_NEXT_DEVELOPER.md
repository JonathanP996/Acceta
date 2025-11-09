# 📦 Accent Detection Service - Complete Package

## ✅ Everything You Need is Here

This folder contains **everything** needed to integrate accent detection into your application. No additional files needed!

## 🎯 The Problem You're Solving

**Issue**: Microphone recordings (WebM/OGG) weren't working, only file uploads worked.

**Solution**: This package includes an improved Flask app that:
- ✅ Automatically detects WebM/OGG format from microphone recordings
- ✅ Handles file extension detection (even if missing)
- ✅ Uses proper content-type detection
- ✅ Works with both file uploads AND microphone recordings

## 📁 Files Included

| File | Size | Purpose |
|------|------|---------|
| `app.py` | 2.7 KB | **Flask API server** - Handles both file uploads and microphone recordings |
| `accent_detector.py` | 4.6 KB | Main detection module |
| `preprocess.py` | 2.0 KB | Audio preprocessing (handles webm/ogg/mp3/wav) |
| `cnn_tunning.h5` | 7.6 MB | Trained CNN model |
| `label_encoder.pkl` | 386 B | Maps predictions to accent names |
| `requirements.txt` | 158 B | Python dependencies |
| `test_microphone.html` | 5.4 KB | Test page for microphone recording |
| `INTEGRATION_INSTRUCTIONS.md` | 9.1 KB | Complete integration guide |
| `QUICK_START.md` | 3.3 KB | Quick setup guide |

## 🚀 Quick Start (3 Steps)

```bash
# 1. Install dependencies
cd accent-detection-service
pip install -r requirements.txt

# 2. Start the service
python app.py

# 3. Test it (open in browser)
open test_microphone.html
```

Service runs on: `http://localhost:5001`

## 🎤 Microphone Recording - How It Works

The key fix is in `app.py`:

```python
# Automatically detects format
file_ext = os.path.splitext(file.filename)[1].lower()

# If no extension, detect from content type
if not file_ext:
    content_type = file.content_type or ''
    if 'webm' in content_type:
        file_ext = '.webm'  # Microphone recording
    # ... other formats
    else:
        file_ext = '.webm'  # Default for microphone
```

**Why this works:**
- Browser microphone recordings are typically WebM or OGG
- The service now automatically detects these formats
- `preprocess.py` handles WebM/OGG natively using librosa
- No conversion needed!

## 🔌 API Usage

### Endpoint: `POST /detect-accent`

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Field name: `file` (must be exactly "file")
- Formats: MP3, WAV, M4A, FLAC, **WebM, OGG, Opus**

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

## 💻 Frontend Integration

### JavaScript (Microphone Recording)

```javascript
// Record from microphone
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
const recorder = new MediaRecorder(stream);
const chunks = [];

recorder.ondataavailable = e => chunks.push(e.data);
recorder.onstop = async () => {
  const blob = new Blob(chunks, { type: 'audio/webm' });
  const formData = new FormData();
  
  // IMPORTANT: Field name must be "file"
  formData.append('file', blob, 'recording.webm');
  
  const res = await fetch('http://localhost:5001/detect-accent', {
    method: 'POST',
    body: formData
  });
  
  const result = await res.json();
  console.log('Accent:', result.accent);
  console.log('Confidence:', result.confidence + '%');
};

recorder.start();
setTimeout(() => recorder.stop(), 5000);
```

### React Example

See `INTEGRATION_INSTRUCTIONS.md` for complete React example.

## 🔧 Backend Integration (Node.js/Express)

```javascript
const multer = require('multer');
const axios = require('axios');
const FormData = require('form-data');

const upload = multer({ dest: 'uploads/' });

app.post('/detect-accent', upload.single('file'), async (req, res) => {
  const formData = new FormData();
  formData.append('file', fs.createReadStream(req.file.path), {
    filename: req.file.originalname,
    contentType: req.file.mimetype
  });

  const response = await axios.post(
    'http://localhost:5001/detect-accent',
    formData,
    { headers: formData.getHeaders() }
  );

  res.json(response.data);
});
```

## ⚠️ Important Notes

### 1. Field Name Must Be "file"
```javascript
// ✅ Correct
formData.append('file', blob, 'recording.webm');

// ❌ Wrong
formData.append('audio', blob, 'recording.webm');
formData.append('recording', blob, 'recording.webm');
```

### 2. File Extension Helps
```javascript
// ✅ Good - explicit extension
formData.append('file', blob, 'recording.webm');

// ✅ Also works - service will detect from content type
formData.append('file', blob);
```

### 3. Supported Formats
- **File uploads**: MP3, WAV, M4A, FLAC
- **Microphone**: WebM, OGG, Opus
- All handled automatically by `preprocess.py`

## 🐛 Troubleshooting

### "Microphone doesn't work"
1. ✅ Check browser console for errors
2. ✅ Verify field name is `file` (not `audio`)
3. ✅ Ensure service is running on port 5001
4. ✅ Check CORS (already enabled in app.py)

### "No file provided" error
- ✅ Form field must be named `file`
- ✅ Use `FormData` with `formData.append('file', ...)`

### "Model not found"
- ✅ Ensure `cnn_tunning.h5` and `label_encoder.pkl` are in same directory as `app.py`
- ✅ Check file permissions

## 📊 Supported Accents (15 classes)

1. Arabic
2. **English** ⭐
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

## 📚 Documentation Files

- **QUICK_START.md** - 3-step setup guide
- **INTEGRATION_INSTRUCTIONS.md** - Complete integration guide with examples
- **MICROPHONE_ACCURACY_DOCUMENTATION.md** - ⭐ **COMPLETE technical documentation** explaining every detail of why microphone recordings work (652 lines!)
- **MICROPHONE_FLOW_DIAGRAM.md** - Visual flow diagrams showing old vs new implementation
- **README.md** - Basic overview
- **test_microphone.html** - Working test page

### 🔍 For Deep Understanding

If you want to understand **exactly** why microphone recordings work and why they failed before, read:
1. **MICROPHONE_ACCURACY_DOCUMENTATION.md** - Line-by-line analysis of every code detail
2. **MICROPHONE_FLOW_DIAGRAM.md** - Visual flowcharts showing the complete request flow

## ✅ Ready to Use!

Everything is set up and tested. The microphone recording issue is fixed. Just:

1. Install dependencies: `pip install -r requirements.txt`
2. Start service: `python app.py`
3. Integrate using the examples above

**The service now works with both file uploads AND microphone recordings!** 🎉

