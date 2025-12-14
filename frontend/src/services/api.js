import axios from 'axios';

const api = axios.create({
  baseURL: `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 90000  // ← 90 seconds default for all requests
});

export const clientsAPI = {
  getAll: (params = {}) => api.get('/clients/', { params }),
  getProfile: (clientId) => api.get(`/clients/${clientId}/profile`),      // ← Returns cached DB data
  getTimeline: (clientId) => api.get(`/clients/${clientId}/timeline`),
  getInsights: (clientId) => api.get(`/clients/${clientId}/insights`),
  triggerAnalysis: (clientId) => api.post(`/clients/${clientId}/analyze`, {}, {
    timeout: 90000  // ← Explicit 90s timeout for analysis
  }),
  triggerDemoAlert: (clientId) => api.post('/demo/trigger-alert', {  
    client_id: clientId
  }, {
    timeout: 90000  // 90s timeout for analysis
  })
};

export const actionsAPI = {
  create: (action) => api.post('/actions/', action),
  get: (actionId) => api.get(`/actions/${actionId}`),
};

export default api;
