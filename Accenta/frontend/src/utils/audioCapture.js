/**
 * Web Audio API - Audio Capture Utility
 * Records audio at 16kHz, 16-bit WAV format
 */

class AudioCapture {
  constructor() {
    this.mediaRecorder = null;
    this.audioContext = null;
    this.stream = null;
    this.chunks = [];
    this.isRecording = false;
    this.analyser = null;
    this.microphone = null;
    this.dataArray = null;
    this.volumeCallback = null;
    this.volumeAnimationFrame = null;
  }

  async initialize() {
    try {
      // Request microphone access
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      // Create AudioContext for processing
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: 16000,
      });

      // Create analyser for real-time volume monitoring
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 256;
      this.analyser.smoothingTimeConstant = 0.8;
      this.microphone = this.audioContext.createMediaStreamSource(this.stream);
      this.microphone.connect(this.analyser);
      this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);

      // Create MediaRecorder
      const options = {
        mimeType: 'audio/webm;codecs=opus',
        audioBitsPerSecond: 16000,
      };

      this.mediaRecorder = new MediaRecorder(this.stream, options);

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.chunks.push(event.data);
        }
      };

      return true;
    } catch (error) {
      console.error('Error initializing audio capture:', error);
      throw new Error('Microphone access denied or not available');
    }
  }

  startRecording(volumeCallback = null) {
    if (!this.mediaRecorder) {
      throw new Error('Audio capture not initialized');
    }

    this.chunks = [];
    this.isRecording = true;
    this.volumeCallback = volumeCallback;
    this.mediaRecorder.start();
    
    // Start volume monitoring if callback provided
    if (this.volumeCallback && this.analyser) {
      this.monitorVolume();
    }
  }

  monitorVolume() {
    if (!this.isRecording || !this.analyser) return;
    
    // Use time domain data for volume (amplitude)
    this.analyser.getByteTimeDomainData(this.dataArray);
    
    // Calculate RMS (Root Mean Square) for volume
    let sum = 0;
    for (let i = 0; i < this.dataArray.length; i++) {
      const normalized = (this.dataArray[i] - 128) / 128; // Normalize to -1 to 1
      sum += normalized * normalized;
    }
    const rms = Math.sqrt(sum / this.dataArray.length);
    const normalizedVolume = Math.min(1, rms * 3); // Scale and clamp to 0-1
    
    // Call callback with volume
    if (this.volumeCallback) {
      this.volumeCallback(normalizedVolume);
    }
    
    // Continue monitoring
    this.volumeAnimationFrame = requestAnimationFrame(() => this.monitorVolume());
  }

  stopRecording() {
    return new Promise((resolve, reject) => {
      if (!this.mediaRecorder || !this.isRecording) {
        reject(new Error('Not recording'));
        return;
      }

      // Stop volume monitoring
      if (this.volumeAnimationFrame) {
        cancelAnimationFrame(this.volumeAnimationFrame);
        this.volumeAnimationFrame = null;
      }
      this.volumeCallback = null;

      this.mediaRecorder.onstop = async () => {
        this.isRecording = false;
        try {
          const audioBlob = new Blob(this.chunks, { type: 'audio/webm' });
          const wavBlob = await this.convertToWAV(audioBlob);
          resolve(wavBlob);
        } catch (error) {
          reject(error);
        }
      };

      this.mediaRecorder.stop();
    });
  }

  async convertToWAV(audioBlob) {
    // Convert WebM to WAV format
    const arrayBuffer = await audioBlob.arrayBuffer();
    const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);

    // Convert to 16-bit PCM WAV
    const wav = this.audioBufferToWav(audioBuffer);
    return new Blob([wav], { type: 'audio/wav' });
  }

  audioBufferToWav(buffer) {
    const length = buffer.length;
    const sampleRate = buffer.sampleRate;
    const arrayBuffer = new ArrayBuffer(44 + length * 2);
    const view = new DataView(arrayBuffer);

    // WAV header
    const writeString = (offset, string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    };

    writeString(0, 'RIFF');
    view.setUint32(4, 36 + length * 2, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(36, 'data');
    view.setUint32(40, length * 2, true);

    // Convert float samples to 16-bit PCM
    let offset = 44;
    for (let i = 0; i < length; i++) {
      const sample = Math.max(-1, Math.min(1, buffer.getChannelData(0)[i]));
      view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);
      offset += 2;
    }

    return arrayBuffer;
  }

  cleanup() {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
    }
    if (this.audioContext) {
      this.audioContext.close();
    }
    this.mediaRecorder = null;
    this.audioContext = null;
    this.stream = null;
  }
}

export default AudioCapture;

