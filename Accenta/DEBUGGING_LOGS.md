# Debugging Logs Guide

This guide explains how to access and interpret debugging logs for the Accenta application.

## Table of Contents
1. [Backend Logs](#backend-logs)
2. [Frontend Logs](#frontend-logs)
3. [Common Issues and Solutions](#common-issues-and-solutions)
4. [API Request/Response Logging](#api-requestresponse-logging)

---

## Backend Logs

### Accessing Backend Logs

The backend logs are displayed in the PowerShell window where you started the backend server.

**To view backend logs:**
1. Open the PowerShell window where `start_backend.ps1` is running
2. All logs are printed directly to the console
3. Logs include timestamps, log levels, and detailed error messages

### Log Levels

- **INFO**: Normal operation messages
- **WARNING**: Non-critical issues (e.g., missing optional dependencies)
- **ERROR**: Critical errors that may affect functionality
- **DEBUG**: Detailed debugging information (if enabled)

### Key Backend Log Messages

#### Startup Logs
```
INFO:     Starting Accenta backend...
INFO:     ✓ Database connected
INFO:     Application startup complete.
```

#### Gemini Connection Logs
```
INFO:     ✓ Gemini API connected and working with model: models/gemini-2.5-flash
```
or
```
ERROR:    Gemini connection test failed: [error details]
WARNING:  No Google API key found - chat will use fallback responses
```

#### Chat Request Logs
```
INFO:     Received audio file: [size] bytes
INFO:     Transcribing audio with Whisper...
INFO:     Whisper transcribed text: '[transcribed text]' (detected language: en)
INFO:     Detecting user's accent from audio...
INFO:     Detected user accent: american (confidence: 0.65, method: heuristic)
INFO:     Analyzing pronunciation with Gemini...
INFO:     Using Gemini model: models/gemini-2.5-flash to generate response
INFO:     Gemini generated response successfully (length: [number])
INFO:     Generated TTS audio: [size] bytes
```

#### Error Logs
```
ERROR:    Chat with audio upload failed: [error message]
ERROR:    Transcription failed: [error details]
ERROR:    TTS generation failed: [error details]
```

---

## Frontend Logs

### Accessing Frontend Logs

**Browser Console (Recommended):**
1. Open your browser (Chrome, Firefox, Edge)
2. Press `F12` or right-click → "Inspect"
3. Go to the **Console** tab
4. All frontend logs will appear here

**PowerShell Window:**
- The frontend PowerShell window shows build/compilation messages
- Look for "Compiled successfully!" or error messages

### Key Frontend Log Messages

#### Audio Processing
```
✅ Created audio blob: { size: [number], type: 'audio/mpeg' }
Playing AI response audio...
Received audio base64, length: [number]
```

#### API Requests
```
POST http://localhost:8000/api/chat/message/audio/upload
Response: { transcribed_text: '...', ai_message: '...' }
```

#### Errors
```
❌ Error converting base64 to blob: [error]
Error processing audio: [error details]
Network Error: [error message]
```

---

## Common Issues and Solutions

### Issue: "CORS request did not succeed"

**Symptoms:**
- Browser console shows CORS errors
- Network requests fail with status (null)

**Solution:**
1. Check if backend is running: `http://localhost:8000/health`
2. Verify CORS configuration in `backend/app.py`
3. Ensure frontend and backend are on correct ports (3000 and 8000)

**Debug Logs:**
- Backend: Check for "Application startup complete"
- Frontend: Check browser console for CORS errors

---

### Issue: "Wally not talking" / No audio playback

**Symptoms:**
- Wally's message appears but no audio plays
- Audio blob is empty or null

**Solution:**
1. Check browser console for audio errors
2. Verify ElevenLabs API key in backend logs
3. Check for autoplay restrictions (browser may block autoplay)

**Debug Logs to Check:**
```
Frontend Console:
- "✅ Created audio blob: { size: [number] }"
- "Playing AI response audio..."
- "Audio blob is empty!" (if error)

Backend Logs:
- "Generated TTS audio: [size] bytes"
- "TTS generation failed: [error]" (if error)
```

---

### Issue: "Processing message" stuck

**Symptoms:**
- Frontend shows "Processing your message..." indefinitely
- No response from backend

**Solution:**
1. Check backend PowerShell window for errors
2. Verify Gemini API is connected
3. Check if accent detection is timing out

**Debug Logs to Check:**
```
Backend:
- "Transcribing audio with Whisper..."
- "Analyzing pronunciation with Gemini..."
- "Generating conversational response with Gemini..."
- Any ERROR messages
```

---

### Issue: "Gemini not generating responses"

**Symptoms:**
- Wally gives generic/fallback responses
- No contextually relevant replies

**Solution:**
1. Check Gemini connection status: `http://localhost:8000/api/chat/status`
2. Verify GOOGLE_API_KEY in backend/.env
3. Check backend logs for Gemini errors

**Debug Logs to Check:**
```
Backend:
- "Gemini connection test failed: [error]"
- "Using Gemini model: [model_name] to generate response"
- "Gemini generated response successfully"
- "Gemini generation failed: [error]"
```

---

### Issue: "Whisper transcription not working"

**Symptoms:**
- No transcribed text appears
- "Could not transcribe audio" error

**Solution:**
1. Verify OPENAI_API_KEY in backend/.env
2. Check audio file size and format
3. Ensure microphone permissions are granted

**Debug Logs to Check:**
```
Backend:
- "Transcribing audio with Whisper..."
- "Whisper transcribed text: '[text]'"
- "Transcription failed: [error]"

Frontend:
- "Error processing audio: [error]"
- Check microphone access errors
```

---

## API Request/Response Logging

### Backend API Endpoints

**Health Check:**
```
GET http://localhost:8000/health
Response: { status, database, gemini }
```

**Chat Status:**
```
GET http://localhost:8000/api/chat/status
Response: { gemini_available, gemini_status, gemini_error }
```

**Chat Message (Audio Upload):**
```
POST http://localhost:8000/api/chat/message/audio/upload
Request: FormData with audio_file, user_id, session_id, etc.
Response: { transcribed_text, ai_message, pronunciation_score, audio_base64, ... }
```

### Frontend API Calls

**Check Browser Network Tab:**
1. Open browser DevTools (F12)
2. Go to **Network** tab
3. Filter by "XHR" or "Fetch"
4. Click on requests to see:
   - Request headers and body
   - Response data
   - Status codes
   - Timing information

---

## Enabling More Detailed Logs

### Backend

Edit `backend/app.py` to change log level:
```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
```

### Frontend

Add console logs in components:
```javascript
console.log('Debug info:', data);
console.error('Error:', error);
console.warn('Warning:', warning);
```

---

## Log File Locations

### Backend
- Logs are printed to console (PowerShell window)
- No log files are created by default
- To save logs to file, redirect output:
  ```powershell
  .\start_backend.ps1 > backend_logs.txt 2>&1
  ```

### Frontend
- Browser console (F12 → Console tab)
- Network requests (F12 → Network tab)
- React DevTools (if installed)

---

## Quick Debugging Checklist

When reporting issues, check:

- [ ] Backend is running (`http://localhost:8000/health`)
- [ ] Frontend is running (`http://localhost:3000`)
- [ ] Browser console shows no errors
- [ ] Backend PowerShell window shows no errors
- [ ] API keys are configured (check backend/.env)
- [ ] Network requests are successful (check Network tab)
- [ ] Audio permissions are granted
- [ ] Gemini connection status is "connected"

---

## Example Debugging Session

**Problem:** Wally not responding to user messages

**Steps:**
1. Check backend logs: "Gemini connection test failed" → API key issue
2. Check frontend console: "Network Error" → Backend not running
3. Check browser Network tab: Request to `/api/chat/message/audio/upload` returns 500
4. Check backend logs: "Transcription failed: OpenAI API key invalid"
5. Solution: Update OPENAI_API_KEY in backend/.env

---

## Contact & Support

If you encounter issues not covered here:
1. Check all logs (backend console + browser console)
2. Note the exact error messages
3. Check the timestamps to correlate frontend/backend events
4. Share the relevant log excerpts when asking for help

---

**Last Updated:** 2025-11-08
