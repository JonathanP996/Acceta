# Differences Between Test Files (MP3) and Microphone Recordings (WebM→WAV)

## Critical Differences That Could Affect Accuracy

### 1. **Audio Format & Conversion Chain**
- **Test Files**: MP3 format → Direct librosa.load()
- **Microphone**: WebM/Opus → Converted to WAV in browser → Sent as WAV
- **Issue**: Double conversion (WebM→WAV) may introduce artifacts
- **Location**: `frontend/src/utils/audioCapture.js:195-203`

### 2. **Sample Rate Handling**
- **Frontend Request**: Requests 16kHz (`sampleRate: 16000`)
- **AudioContext**: May use different native rate (typically 44.1kHz or 48kHz)
- **Backend Preprocessing**: Expects 44.1kHz (`target_sample_rate=44100`)
- **Issue**: Sample rate mismatch between frontend request and backend expectation
- **Location**: 
  - Frontend: `audioCapture.js:36`
  - Backend: `preprocess.py:7`

### 3. **Resampling Quality**
- **MP3 Files**: Uses default librosa resampling
- **WebM/OGG Files**: Uses `kaiser_best` resampling (higher quality)
- **WAV from Microphone**: Uses default resampling (may be lower quality)
- **Issue**: Different resampling algorithms = different MFCC features
- **Location**: `preprocess.py:28-33`

### 4. **File Extension Detection**
- **Frontend Sends**: `recording.wav` (filename)
- **Backend Logic**: Checks filename first, then content-type
- **Issue**: If filename is `.wav`, uses default resampling (not `kaiser_best`)
- **Location**: `accent_detection.py:90-104`

### 5. **Audio Duration**
- **Training Data**: Exactly 5 seconds
- **Microphone Recording**: Variable length (user-controlled)
- **Preprocessing**: Takes first 5 seconds if longer, uses all if shorter
- **Issue**: Short recordings (< 0.5s) are rejected, but 1-4 second recordings may have less data
- **Location**: `preprocess.py:40-45`

### 6. **Audio Quality & Noise**
- **Test Files**: Professional recordings, clean audio
- **Microphone**: Real-time recording, may have:
  - Background noise
  - Echo cancellation artifacts
  - Auto gain control adjustments
  - Noise suppression artifacts
- **Location**: `audioCapture.js:37-39`

### 7. **Top N Predictions Display**
- **This Model**: Returns `top_predictions` and `all_predictions` (shows all 15 classes)
- **Other Model**: May only show top 1-3 predictions
- **Issue**: User sees more options, can identify correct prediction even if not #1
- **Location**: `accent_detection.py:141-142`

### 8. **Uncertainty Detection**
- **This Model**: Flags low confidence (< 50-60%) and shows warning
- **Other Model**: May not have uncertainty detection
- **Issue**: User is warned when prediction is uncertain
- **Location**: `accent_detection.py:115-135`

### 9. **Model Singleton Pattern**
- **This Model**: Loads once, cached in memory
- **Other Model**: May reload or use different instance
- **Issue**: Consistency vs. memory usage tradeoff
- **Location**: `accent_detection.py:41-64`

### 10. **Audio Normalization**
- **Preprocessing**: Global mean/std normalization
- **Epsilon**: `1e-8` to prevent division by zero
- **NaN Handling**: `np.nan_to_num` to handle invalid values
- **Issue**: Different normalization could affect predictions
- **Location**: `preprocess.py:50-66`

### 11. **MFCC Feature Extraction**
- **Parameters**: `n_mfcc=13`, `target_sample_rate=44100`
- **Method**: `librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)`
- **Issue**: Must match training exactly
- **Location**: `preprocess.py:48`

### 12. **Audio Buffer Conversion**
- **Frontend**: Converts WebM → AudioBuffer → WAV
- **Process**: Float32 samples → 16-bit PCM
- **Issue**: Quantization and conversion may lose information
- **Location**: `audioCapture.js:205-241`

### 13. **Content-Type vs Filename**
- **Frontend Sends**: Blob with `type: 'audio/wav'` but filename `recording.wav`
- **Backend Checks**: Filename first, then content-type
- **Issue**: If filename is `.wav`, uses default resampling (not optimized for browser recordings)
- **Location**: `accent_detection.py:90-104`

### 14. **Audio Context Sample Rate**
- **Frontend**: AudioContext may use 44.1kHz, 48kHz, or other
- **Backend**: Expects 44.1kHz
- **Issue**: Mismatch requires resampling, which can introduce artifacts
- **Location**: `audioCapture.js:56-59`

### 15. **Recording Constraints**
- **Frontend**: Requests specific constraints (echo cancellation, noise suppression, etc.)
- **Backend**: No knowledge of these constraints
- **Issue**: Preprocessing may not account for audio processing already done
- **Location**: `audioCapture.js:33-40`

## Recommended Fixes

1. **Force WebM/OGG Detection**: Check content-type or actual file format, not just filename
2. **Match Sample Rate**: Ensure frontend sends at 44.1kHz or backend handles 16kHz properly
3. **Use Consistent Resampling**: Always use `kaiser_best` for browser recordings
4. **Add Audio Quality Checks**: Validate audio quality before processing
5. **Log Audio Metadata**: Log sample rate, duration, format for debugging

