import axios from 'axios';

const api = axios.create({
  baseURL: `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const clientsAPI = {
  getAll: (params = {}) => api.get('/clients/', { params }),
  getProfile: (clientId) => api.get(`/clients/${clientId}/profile`),      // ← Returns cached DB data
  getTimeline: (clientId) => api.get(`/clients/${clientId}/timeline`),
  getInsights: (clientId) => api.get(`/clients/${clientId}/insights`),
  triggerAnalysis: (clientId) => api.post(`/clients/${clientId}/analyze`), // ← NEW: Triggers agent analysis
};

export const actionsAPI = {
  create: (action) => api.post('/actions/', action),
  get: (actionId) => api.get(`/actions/${actionId}`),
};

export default api;
