# Frontend Fixes to Match Working HTML

## Date: 2025-11-08

## Critical Differences Found and Fixed

### ✅ 1. Sample Rate in getUserMedia (CRITICAL - FIXED)

**Issue**: Our code requested 16kHz, but working HTML uses 44.1kHz.

**Before**:
```javascript
stream = await navigator.mediaDevices.getUserMedia({
  audio: {
    sampleRate: 16000,  // WRONG!
    ...
  }
});
```

**After** (matches working HTML):
```javascript
stream = await navigator.mediaDevices.getUserMedia({
  audio: {
    sampleRate: 44100,  // CORRECT - matches working HTML
    channelCount: 1,
    echoCancellation: true,
    noiseSuppression: true,
  }
});
```

**Impact**: This was causing the audio to be recorded at the wrong sample rate, leading to incorrect preprocessing.

---

### ✅ 2. MediaRecorder Bitrate Constraint (FIXED)

**Issue**: Our code constrained bitrate to 16kbps, but working HTML doesn't constrain it.

**Before**:
```javascript
let options = {
  mimeType: 'audio/webm;codecs=opus',
  audioBitsPerSecond: 16000,  // WRONG - constrains quality
};
```

**After** (matches working HTML):
```javascript
let options = {
  mimeType: mimeType,  // No bitrate constraint - let browser use default
};
```

**Impact**: Constraining bitrate reduces audio quality, which affects feature extraction.

---

### ✅ 3. MIME Type Selection (FIXED)

**Issue**: Our code had a different fallback order.

**After** (matches working HTML):
```javascript
let mimeType = 'audio/webm';
if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
  mimeType = 'audio/webm;codecs=opus';
} else if (MediaRecorder.isTypeSupported('audio/webm')) {
  mimeType = 'audio/webm';
} else if (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) {
  mimeType = 'audio/ogg;codecs=opus';
} else if (MediaRecorder.isTypeSupported('audio/mp4')) {
  mimeType = 'audio/mp4';
}
```

---

### ✅ 4. MediaRecorder Start Timeslice (FIXED)

**Issue**: Our code didn't use timeslice parameter.

**Before**:
```javascript
this.mediaRecorder.start();
```

**After** (matches working HTML):
```javascript
this.mediaRecorder.start(100); // Collect data every 100ms
```

**Impact**: Ensures data is available when recording stops.

---

### ✅ 5. WAV Quantization Method (CRITICAL - FIXED)

**Issue**: We changed to symmetric quantization, but working HTML uses asymmetric.

**Before** (our "fix"):
```javascript
// Symmetric quantization
const quantized = Math.max(-32768, Math.min(32767, Math.round(sample * 32767)));
```

**After** (matches working HTML):
```javascript
// Asymmetric quantization (matches working HTML exactly)
const quantized = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
```

**Impact**: The model was trained with asymmetric quantization, so we must match it exactly.

---

### ✅ 6. Filename for API (FIXED)

**Issue**: We used `recording.webm.wav`, but working HTML uses `recording.wav`.

**Before**:
```javascript
formData.append('audio_file', audioBlob, 'recording.webm.wav');
```

**After** (matches working HTML):
```javascript
formData.append('audio_file', audioBlob, 'recording.wav');
```

**Impact**: Backend detects browser recordings by filename pattern.

---

### ✅ 7. Blob Type from MediaRecorder (FIXED)

**Issue**: We hardcoded `'audio/webm'`, but should use actual mimeType.

**Before**:
```javascript
const audioBlob = new Blob(this.chunks, { type: 'audio/webm' });
```

**After** (matches working HTML):
```javascript
const mimeType = this.mediaRecorder.mimeType || 'audio/webm';
const audioBlob = new Blob(this.chunks, { type: mimeType });
```

---

## Summary of All Changes

| Component | Before | After | Match HTML |
|-----------|--------|-------|------------|
| getUserMedia sampleRate | 16000 | 44100 | ✅ |
| MediaRecorder bitrate | Constrained (16kbps) | Unconstrained | ✅ |
| MIME type selection | Different order | Matches HTML | ✅ |
| MediaRecorder.start() | No timeslice | start(100) | ✅ |
| WAV quantization | Symmetric | Asymmetric | ✅ |
| Filename | recording.webm.wav | recording.wav | ✅ |
| Blob type | Hardcoded | From MediaRecorder | ✅ |

---

## Expected Impact

After these fixes, the frontend audio capture should:
1. ✅ Record at correct sample rate (44.1kHz)
2. ✅ Use optimal audio quality (no bitrate constraint)
3. ✅ Match the exact quantization method used in training
4. ✅ Send files with correct filename pattern for backend detection

**The microphone input should now match the working HTML implementation exactly.**

---

## Testing

After these fixes:
1. Test microphone recording
2. Verify predictions match test file accuracy
3. Compare with working HTML results

All preprocessing should now be identical between microphone input and test files.

