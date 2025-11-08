# Debugging Logs Guide for LiveChat Component

## How to Access Logs

1. **Open Browser Developer Tools:**
   - Press `F12` or `Ctrl+Shift+I` (Windows/Linux)
   - Press `Cmd+Option+I` (Mac)
   - Or right-click on the page → "Inspect" → "Console" tab

2. **Filter Logs:**
   - Use the filter box in the console to search for specific messages
   - Filter by log level: `console.log`, `console.warn`, `console.error`

## All Debugging Logs in LiveChat Component

### Initial Greeting Logs

```javascript
// When initial greeting audio is received and playing
console.log('Playing initial greeting audio...', chatResponse.audio);

// When no audio is received for initial greeting
console.warn('No audio received for initial greeting, generating TTS...');

// When TTS is generated for initial greeting
console.log('Playing generated TTS audio...', audioBlob);

// When fallback TTS is generated
console.log('Playing fallback TTS audio...', audioBlob);
```

### Audio Playback Logs

```javascript
// When component is not mounted (shouldn't play audio)
console.log('Component not mounted, skipping audio playback');

// When no audio blob is provided
console.error('No audio blob provided to playAIResponseAudio');

// When starting audio playback
console.log('Starting audio playback...', { blobSize: audioBlob.size, blobType: audioBlob.type });

// When audio element is created
console.log('Audio element created, preparing to play...');

// When audio playback starts successfully
console.log('Audio playback started successfully');

// When autoplay is blocked
console.warn('Autoplay blocked by browser. Will attempt to play after user interaction.');

// When audio plays after user interaction
console.log('Audio playback started after user interaction');
```

### Message Processing Logs

```javascript
// When no audio is received for a message, generating TTS
console.log('No audio received, generating TTS for message...');
```

### Error Logs

```javascript
// Error loading saved conversation
console.error('Error loading saved conversation:', error);

// Error generating replay audio
console.error('Error generating replay audio:', error);

// Error saving conversation
console.error('Error saving conversation:', error);

// Error regenerating message audio
console.error('Error regenerating message audio:', error);

// Error generating TTS for initial greeting
console.error('Error generating TTS for initial greeting:', ttsError);

// Error generating initial greeting
console.error('Error generating initial greeting:', error);

// Error generating TTS for fallback greeting
console.error('Error generating TTS for fallback greeting:', ttsError);

// Error starting recording
console.error('Error starting recording:', error);

// Error processing audio
console.error('Error processing audio:', error);

// Error generating TTS for AI message
console.error('Error generating TTS for AI message:', ttsError);

// Error generating AI response
console.error('Error generating AI response:', error);

// Error generating TTS for fallback message
console.error('Error generating TTS for fallback message:', ttsError);

// Error playing audio
console.error('Error playing audio:', error);

// Still unable to play audio after user interaction
console.error('Still unable to play audio:', e);

// Audio playback blocked by browser
console.error('Audio playback blocked by browser. User interaction may be required.');

// Audio format not supported
console.error('Audio format not supported');

// Unknown audio playback error
console.error('Unknown audio playback error:', error);

// Error generating TTS for cleared conversation greeting
console.error('Error generating TTS for cleared conversation greeting:', ttsError);
```

## API Service Logs

### In `frontend/src/services/api.js`:

```javascript
// When audio base64 is received
console.log('Received audio base64, length:', audioBase64.length);

// When audio blob is created
console.log('Created audio blob:', { size: audioBlob.size, type: audioBlob.type });

// When no audio_base64 in response
console.warn('No audio_base64 in response:', response.data);

// Error converting base64 to blob
console.error('Error converting base64 to blob:', error);
```

## Common Log Sequences

### Successful Initial Greeting:
1. `Playing initial greeting audio...` (or `No audio received, generating TTS...`)
2. `Starting audio playback...` (with blob size and type)
3. `Audio element created, preparing to play...`
4. `Audio playback started successfully`

### When Audio is Missing:
1. `No audio received for initial greeting, generating TTS...`
2. `Playing generated TTS audio...`
3. `Starting audio playback...`
4. `Audio playback started successfully`

### When Autoplay is Blocked:
1. `Starting audio playback...`
2. `Audio element created, preparing to play...`
3. `Autoplay blocked by browser. Will attempt to play after user interaction.`
4. (After user clicks) `Audio playback started after user interaction`

### When Processing User Message:
1. `No audio received, generating TTS for message...` (if needed)
2. `Starting audio playback...`
3. `Audio playback started successfully`

## Tips for Debugging

1. **Clear the console** before testing to see fresh logs
2. **Filter by "audio"** to see only audio-related logs
3. **Filter by "error"** to see only error messages
4. **Check the Network tab** to see if API calls are successful
5. **Check the blob size** - should be > 0 if audio was generated
6. **Check blob type** - should be "audio/mpeg" or similar

## Expected Behavior

- **Initial greeting:** Should see logs showing audio generation and playback
- **User messages:** Should see "No audio received, generating TTS..." if backend doesn't provide audio
- **Audio playback:** Should see "Audio playback started successfully" for each message
- **Errors:** Should only see errors if something is actually broken

