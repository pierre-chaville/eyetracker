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
};

export const calibrationAPI = {
  start: async () => {
    const response = await apiClient.post('/api/calibration/start');
    return response.data;
  },
};

export default apiClient;

