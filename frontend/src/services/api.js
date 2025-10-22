import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const clientsAPI = {
  getAll: (params = {}) => api.get('/clients', { params }),
  getProfile: (clientId) => api.get(`/clients/${clientId}/profile`),
  getTimeline: (clientId) => api.get(`/clients/${clientId}/timeline`),
  getInsights: (clientId) => api.get(`/clients/${clientId}/insights`),
  getMedia: (clientId) => api.get(`/clients/${clientId}/media`),
};

export const actionsAPI = {
  create: (action) => api.post('/actions', action),
  get: (actionId) => api.get(`/actions/${actionId}`),
};

export default api;
