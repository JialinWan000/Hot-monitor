import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
})

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// 关键词 API
export const keywordsApi = {
  getAll: (params) => api.get('/keywords', { params }),
  get: (id) => api.get(`/keywords/${id}`),
  create: (data) => api.post('/keywords', data),
  update: (id, data) => api.put(`/keywords/${id}`, data),
  delete: (id) => api.delete(`/keywords/${id}`),
  toggle: (id) => api.post(`/keywords/${id}/toggle`),
}

// 热点 API
export const hotspotsApi = {
  getAll: (params) => api.get('/hotspots', { params }),
  get: (id) => api.get(`/hotspots/${id}`),
  getSources: () => api.get('/hotspots/sources'),
  markAsRead: (id) => api.post(`/hotspots/${id}/read`),
  markAllAsRead: () => api.post('/hotspots/read-all'),
  refresh: () => api.post('/hotspots/refresh'),
  search: (data) => api.post('/hotspots/search', data),
  delete: (id) => api.delete(`/hotspots/${id}`),
}

// 通知 API
export const notificationsApi = {
  getAll: (params) => api.get('/notifications', { params }),
  getSettings: () => api.get('/notifications/settings'),
  updateSettings: (data) => api.post('/notifications/settings', data),
  subscribe: (data) => api.post('/notifications/subscribe', data),
  unsubscribe: (endpoint) => api.post('/notifications/unsubscribe', { endpoint }),
  test: (type) => api.post('/notifications/test', null, { params: { notification_type: type } }),
}

// 系统 API
export const systemApi = {
  getDashboard: () => api.get('/system/dashboard'),
  getSettings: () => api.get('/system/settings'),
  updateSetting: (data) => api.post('/system/settings', data),
  getVapidKey: () => api.get('/system/vapid-public-key'),
  getInfo: () => api.get('/system/info'),
}

export default api
