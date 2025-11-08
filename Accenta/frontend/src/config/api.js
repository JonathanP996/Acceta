/**
 * API Configuration
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  // Auth
  SIGNUP: `${API_BASE_URL}/api/auth/signup`,
  LOGIN: `${API_BASE_URL}/api/auth/login`,
  GET_USER: (userId) => `${API_BASE_URL}/api/auth/user/${userId}`,
  
  // Analysis
  ANALYZE_ACCENT: `${API_BASE_URL}/api/analyze_accent`,
  ANALYZE_ACCENT_MULTI: `${API_BASE_URL}/api/analyze_accent_multi`,
  
  // Chat
  CHAT_MESSAGE: `${API_BASE_URL}/api/chat/message`,
  CHAT_MESSAGE_AUDIO: `${API_BASE_URL}/api/chat/message/audio`,
  CHAT_MESSAGE_AUDIO_UPLOAD: `${API_BASE_URL}/api/chat/message/audio/upload`,
  
  // WebSocket
  WS_PRACTICE: (sessionId) => `ws://localhost:8000/ws/practice/${sessionId}`,
};

export default API_BASE_URL;

