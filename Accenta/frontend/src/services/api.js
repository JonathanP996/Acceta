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

// Analysis services
export const analysisService = {
  analyzeAccent: async (formData) => {
    const response = await api.post(API_ENDPOINTS.ANALYZE_ACCENT, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

export default api;

