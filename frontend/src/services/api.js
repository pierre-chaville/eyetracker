import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const eyeTrackingAPI = {
  start: async () => {
    const response = await apiClient.post('/api/eye-tracking/start');
    return response.data;
  },
  
  stop: async () => {
    const response = await apiClient.post('/api/eye-tracking/stop');
    return response.data;
  },
  
  getStatus: async () => {
    const response = await apiClient.get('/api/eye-tracking/status');
    return response.data;
  },
};

export const communicationAPI = {
  interpret: async (gazePoints, context = null) => {
    const response = await apiClient.post('/api/communication/interpret', {
      gaze_points: gazePoints,
      context,
    });
    return response.data;
  },
  
  getChoices: async (conversationHistory = [], userId = null, caregiverId = null, currentText = null) => {
    const response = await apiClient.post('/api/communication/choices', {
      conversation_history: conversationHistory,
      user_id: userId,
      caregiver_id: caregiverId,
      current_text: currentText,
    });
    return response.data;
  },
};

export const calibrationAPI = {
  start: async () => {
    const response = await apiClient.post('/api/calibration/start');
    return response.data;
  },
  
  process: async (calibrationData) => {
    const response = await apiClient.post('/api/calibration/process', calibrationData);
    return response.data;
  },
};

export const usersAPI = {
  list: async (skip = 0, limit = 100, activeOnly = false) => {
    const response = await apiClient.get('/api/users', {
      params: { skip, limit, active_only: activeOnly },
    });
    return response.data;
  },
  
  get: async (userId) => {
    const response = await apiClient.get(`/api/users/${userId}`);
    return response.data;
  },
  
  create: async (userData) => {
    const response = await apiClient.post('/api/users', userData);
    return response.data;
  },
  
  update: async (userId, userData) => {
    const response = await apiClient.put(`/api/users/${userId}`, userData);
    return response.data;
  },
  
  delete: async (userId) => {
    const response = await apiClient.delete(`/api/users/${userId}`);
    return response.data;
  },
};

export const caregiversAPI = {
  list: async (skip = 0, limit = 100) => {
    const response = await apiClient.get('/api/caregivers', {
      params: { skip, limit },
    });
    return response.data;
  },
  
  get: async (caregiverId) => {
    const response = await apiClient.get(`/api/caregivers/${caregiverId}`);
    return response.data;
  },
  
  create: async (caregiverData) => {
    const response = await apiClient.post('/api/caregivers', caregiverData);
    return response.data;
  },
  
  update: async (caregiverId, caregiverData) => {
    const response = await apiClient.put(`/api/caregivers/${caregiverId}`, caregiverData);
    return response.data;
  },
  
  delete: async (caregiverId) => {
    const response = await apiClient.delete(`/api/caregivers/${caregiverId}`);
    return response.data;
  },
};

export const configAPI = {
  get: async () => {
    const response = await apiClient.get('/api/config');
    return response.data;
  },
  
  update: async (configData) => {
    const response = await apiClient.put('/api/config', configData);
    return response.data;
  },
};

export default apiClient;

