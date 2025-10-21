export const SEGMENTS = {
  TREND_FOLLOWER: 'Trend Follower',
  MEAN_REVERTER: 'Mean Reverter',
  HEDGER: 'Hedger',
  TREND_SETTER: 'Trend Setter'
};

export const INSIGHT_TYPES = {
  SIGNAL: 'SIGNAL',
  ACTION: 'ACTION',
  OUTCOME: 'OUTCOME'
};

export const SEVERITY_LEVELS = {
  HIGH: 'HIGH',
  MEDIUM: 'MEDIUM',
  LOW: 'LOW',
  SUCCESS: 'SUCCESS'
};

export const MEDIA_PRESSURE = {
  HIGH: 'HIGH',
  MEDIUM: 'MEDIUM',
  LOW: 'LOW'
};

export const API_ENDPOINTS = {
  CLIENTS: '/clients',
  PROFILE: (id) => `/clients/${id}/profile`,
  TIMELINE: (id) => `/clients/${id}/timeline`,
  INSIGHTS: (id) => `/clients/${id}/insights`,
  MEDIA: (id) => `/clients/${id}/media`,
  ACTIONS: '/actions',
  ALERTS_STREAM: '/alerts/stream'
};
