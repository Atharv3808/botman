import axios from 'axios';

const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://botman-api.onrender.com' 
  : 'http://localhost:8000';

const client = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include auth token
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Add response interceptor to handle token refresh
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If error is 401 and we haven't tried to refresh yet
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
            refresh: refreshToken,
          });

          const { access } = response.data;
          localStorage.setItem('access_token', access);

          // Update header for original request
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return client(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed (token expired or invalid)
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

// Auth API
export const login = (credentials) => axios.post(`${API_BASE_URL}/auth/login/`, credentials);
export const signup = (userData) => axios.post(`${API_BASE_URL}/auth/signup/`, userData);

export const getBots = () => client.get('/bot/');
export const getBot = (id) => client.get(`/bot/${id}/`);
export const createBot = (data) => client.post('/bot/', data);
export const updateBot = (id, data) => client.patch(`/bot/${id}/`, data);
export const deleteBot = (id) => client.delete(`/bot/${id}/`);
export const publishBot = (id) => client.post(`/bot/${id}/publish/`);

export const getBotSettings = (id) => client.get(`/bot/${id}/`);
export const updateBotSettings = (id, data) => client.patch(`/bot/${id}/`, data);

export const getKnowledgeFiles = (botId) => client.get(`/bot/${botId}/knowledge/`);
export const uploadKnowledgeFile = (botId, formData) => client.post(`/bot/${botId}/knowledge/`, formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
});
export const deleteKnowledgeFile = (fileId) => client.delete(`/knowledge/${fileId}/`);
export const getKnowledgePreview = (fileId) => client.get(`/knowledge/${fileId}/preview/`);

export const chatTest = (data) => client.post('/chat/preview/', data);

// Analytics
export const getAnalyticsOverview = (botId, include_preview = false) => 
  client.get(`/analytics/${botId}/overview/`, { params: { include_preview } });

export const getAnalyticsGraph = (botId, include_preview = false) => 
  client.get(`/analytics/${botId}/graph/`, { params: { include_preview } });

export const getAnalyticsLive = (botId, include_preview = false) => 
  client.get(`/analytics/${botId}/live/`, { params: { include_preview } });

// Conversations
export const getConversations = (params) => client.get('/history/', { params });
export const getConversation = (id) => client.get(`/history/${id}/`);

export default client;
