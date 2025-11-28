import axios from 'axios';

const api = axios.create({
  baseURL: `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const clientsAPI = {
  getAll: (params = {}) => api.get('/clients/', { params }),           // ✅ Added /
  getProfile: (clientId) => api.get(`/clients/${clientId}/profile/`),  // ✅ Added /
  getTimeline: (clientId) => api.get(`/clients/${clientId}/timeline/`),// ✅ Added /
  getInsights: (clientId) => api.get(`/clients/${clientId}/insights/`),// ✅ Added /
  getMedia: (clientId) => api.get(`/clients/${clientId}/media/`),      // ✅ Added /
};

export const actionsAPI = {
  create: (action) => api.post('/actions/', action),                   // ✅ Added /
  get: (actionId) => api.get(`/actions/${actionId}/`),                 // ✅ Added /
};

export default api;
