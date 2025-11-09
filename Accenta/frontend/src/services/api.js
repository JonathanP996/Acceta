/**
 * API Service - Handles all backend communication
 */

import axios from 'axios';
import API_BASE_URL, { API_ENDPOINTS } from '../config/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for debugging blob responses
api.interceptors.response.use(
  (response) => {
    // Log blob responses for debugging
    if (response.config.responseType === 'blob') {
      console.log('📦 Blob response interceptor:', {
        url: response.config.url,
        status: response.status,
        dataType: typeof response.data,
        isBlob: response.data instanceof Blob,
        size: response.data?.size,
        type: response.data?.type
      });
    }
    return response;
  },
  (error) => {
    console.error('❌ Axios error:', error);
    return Promise.reject(error);
  }
);

// Auth services
export const authService = {
  signup: async (email, username, password) => {
    try {
      const response = await api.post(API_ENDPOINTS.SIGNUP, {
        email,
        username,
        password,
      }, {
        headers: {
          'Content-Type': 'application/json',
        },
      });
      return response.data;
    } catch (error) {
      // Handle network errors
      if (!error.response) {
        console.error('Network error details:', error);
        throw new Error('Network error: Could not connect to server. Make sure the backend is running on http://localhost:8000');
      }
      console.error('Signup error response:', error.response?.data);
      throw error;
    }
  },

  login: async (email, password) => {
    try {
      const response = await api.post(API_ENDPOINTS.LOGIN, {
        email,
        password,
      });
      if (response.data.user_id) {
        localStorage.setItem('auth_token', response.data.user_id);
        localStorage.setItem('user', JSON.stringify(response.data));
      }
      return response.data;
    } catch (error) {
      // Handle network errors
      if (!error.response) {
        throw new Error('Network error: Could not connect to server. Make sure the backend is running on http://localhost:8000');
      }
      throw error;
    }
  },

  getUser: async (userId) => {
    const response = await api.get(API_ENDPOINTS.GET_USER(userId));
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
  },

  getCurrentUser: () => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },

  isAuthenticated: () => {
    return !!localStorage.getItem('auth_token');
  },
};

// Accent Detection Service
export const accentDetectionService = {
  detectAccent: async (audioBlob) => {
    const formData = new FormData();
    // CRITICAL: Match working HTML exactly - use 'recording.wav' filename
    // Backend detects browser recordings by filename pattern
    formData.append('audio_file', audioBlob, 'recording.wav');
    
    const response = await api.post(API_ENDPOINTS.DETECT_ACCENT, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 30000, // 30 second timeout
    });
    return response.data;
  },
};

// TTS services
export const ttsService = {
  generateSpeech: async (text, voiceId = null, accent = null, robotic = false) => {
    try {
      console.log('🎤 TTS Request:', { text: text.substring(0, 50), voiceId, accent, robotic });
      console.log('🎤 TTS Endpoint:', `${API_BASE_URL}/api/tts/generate`);
      
      const response = await api.post(
        `${API_BASE_URL}/api/tts/generate`,
        { text, voice_id: voiceId, accent, robotic },
        { 
          responseType: 'blob', // Important: get audio as blob
          timeout: 30000 // 30 second timeout
        }
      );
      
      console.log('🎤 TTS Response received:', {
        status: response.status,
        statusText: response.statusText,
        headers: response.headers,
        dataType: typeof response.data,
        dataSize: response.data?.size || 'unknown',
        dataConstructor: response.data?.constructor?.name || 'unknown'
      });
      
      // Validate response
      if (!response.data) {
        throw new Error('No data in TTS response');
      }
      
      // Check if it's already a Blob
      if (response.data instanceof Blob) {
        console.log('✅ TTS Response is already a Blob:', {
          size: response.data.size,
          type: response.data.type
        });
        return response.data;
      }
      
      // If it's not a Blob, try to convert it
      console.warn('⚠️ TTS Response is not a Blob, attempting conversion');
      if (typeof response.data === 'string') {
        // Might be base64 encoded
        const audioBytes = Uint8Array.from(atob(response.data), c => c.charCodeAt(0));
        const blob = new Blob([audioBytes], { type: 'audio/mpeg' });
        console.log('✅ Converted string to Blob:', { size: blob.size, type: blob.type });
        return blob;
      }
      
      // Try to create blob from whatever we got
      const blob = new Blob([response.data], { type: 'audio/mpeg' });
      console.log('✅ Created Blob from response data:', { size: blob.size, type: blob.type });
      return blob;
      
    } catch (error) {
      console.error('❌ TTS Service Error:', error);
      console.error('Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        statusText: error.response?.statusText,
        headers: error.response?.headers
      });
      
      // If it's a network error, provide helpful message
      if (!error.response) {
        throw new Error(`Network error: Could not connect to TTS service at ${API_BASE_URL}. Make sure the backend is running.`);
      }
      
      // If it's an HTTP error, include status info
      throw new Error(`TTS generation failed: ${error.response?.status} ${error.response?.statusText || error.message}`);
    }
  },
};

// Chat services
export const chatService = {
  sendMessage: async (data) => {
    const response = await api.post(API_ENDPOINTS.CHAT_MESSAGE, data);
    return response.data;
  },
  
  sendMessageWithAudio: async (data) => {
    const response = await api.post(API_ENDPOINTS.CHAT_MESSAGE_AUDIO, data);
    
    // Convert base64 audio to blob
    let audioBlob = null;
    if (response.data.audio_base64) {
      try {
        const audioBase64 = response.data.audio_base64;
        console.log('Received audio base64, length:', audioBase64.length);
        
        // Validate base64 string
        if (!audioBase64 || audioBase64.length === 0) {
          console.warn('Empty audio_base64 string received');
        } else {
          try {
            const audioBytes = Uint8Array.from(atob(audioBase64), c => c.charCodeAt(0));
            audioBlob = new Blob([audioBytes], { type: 'audio/mpeg' });
            console.log('✅ Created audio blob:', { 
              size: audioBlob.size, 
              type: audioBlob.type,
              firstBytes: Array.from(audioBytes.slice(0, 10))
            });
            
            // Validate blob
            if (audioBlob.size === 0) {
              console.error('❌ Created audio blob is empty!');
              audioBlob = null;
            } else if (audioBlob.size < 100) {
              console.warn('⚠️ Audio blob is very small, might be invalid:', audioBlob.size);
            } else {
              console.log('✅ Audio blob is valid and ready to play');
            }
          } catch (conversionError) {
            console.error('❌ Error converting base64 to blob:', conversionError);
            audioBlob = null;
          }
        }
      } catch (error) {
        console.error('Error converting base64 to blob:', error);
        audioBlob = null;
      }
    } else {
      console.warn('No audio_base64 in response. Response keys:', Object.keys(response.data || {}));
    }
    
    return {
      audio: audioBlob,
      message: response.data.ai_message,
      pronunciation_feedback: response.data.pronunciation_feedback,
    };
  },
  
  sendMessageWithAudioUpload: async (audioBlob, userData, conversationHistory) => {
    // Create FormData for file upload
    const formData = new FormData();
    formData.append('audio_file', audioBlob, 'recording.wav');
    formData.append('user_id', userData.user_id);
    formData.append('session_id', `chat_${Date.now()}`);
    formData.append('language', userData.language);
    formData.append('target_accent', userData.target_accent);
    
    // Add conversation history as JSON string
    if (conversationHistory && conversationHistory.length > 0) {
      formData.append('conversation_history', JSON.stringify(conversationHistory));
    }
    
    const response = await api.post(API_ENDPOINTS.CHAT_MESSAGE_AUDIO_UPLOAD, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000, // 60 second timeout to prevent hanging
    });
    
    // Convert base64 audio to blob
    let audioBlobResponse = null;
    if (response.data.audio_base64) {
      try {
        const audioBase64 = response.data.audio_base64;
        console.log('Received audio base64, length:', audioBase64.length);
        
        if (!audioBase64 || audioBase64.length === 0) {
          console.warn('Empty audio_base64 string received');
        } else {
          try {
            const audioBytes = Uint8Array.from(atob(audioBase64), c => c.charCodeAt(0));
            audioBlobResponse = new Blob([audioBytes], { type: 'audio/mpeg' });
            console.log('✅ Created audio blob:', { 
              size: audioBlobResponse.size, 
              type: audioBlobResponse.type
            });
            
            if (audioBlobResponse.size === 0) {
              console.error('❌ Created audio blob is empty!');
              audioBlobResponse = null;
            }
          } catch (conversionError) {
            console.error('❌ Error converting base64 to blob:', conversionError);
            audioBlobResponse = null;
          }
        }
      } catch (error) {
        console.error('Error converting base64 to blob:', error);
        audioBlobResponse = null;
      }
    } else {
      console.warn('No audio_base64 in response. Response keys:', Object.keys(response.data || {}));
    }
    
    return {
      audio: audioBlobResponse,
      message: response.data.ai_message,
      transcribed_text: response.data.transcribed_text,
      pronunciation_score: response.data.pronunciation_score,
      pronunciation_feedback: response.data.pronunciation_feedback,
      struggle_areas: response.data.struggle_areas || [],
    };
  },
};

export default api;

