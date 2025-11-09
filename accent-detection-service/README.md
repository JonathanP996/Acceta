# Accent Detection Service

A Python Flask service for detecting speech accents from audio files or microphone recordings.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the service:**
   ```bash
   python app.py
   ```

3. **Test it:**
   ```bash
   curl http://localhost:5001/health
   ```

## Features

- ✅ Detects 15 different accents
- ✅ Supports file uploads (MP3, WAV, M4A, FLAC)
- ✅ Supports microphone recordings (WebM, OGG, Opus)
- ✅ RESTful API
- ✅ CORS enabled
- ✅ Returns top 3 predictions with confidence scores

## API

- `GET /health` - Health check
- `POST /detect-accent` - Detect accent from audio file

See `INTEGRATION_INSTRUCTIONS.md` for detailed usage examples.

## Files

- `app.py` - Flask API server
- `accent_detector.py` - Detection module
- `preprocess.py` - Audio preprocessing
- `cnn_tunning.h5` - Trained model
- `label_encoder.pkl` - Label encoder

## Supported Accents

Arabic, English, French, German, Hindi, Italian, Japanese, Korean, Malayalam, Mandarin, Russian, Spanish, Tamil, Thai, Turkish

