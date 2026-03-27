import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('bolt_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('bolt_token');
      localStorage.removeItem('bolt_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),
  
  telegramAuth: (userData: any) =>
    api.post('/auth/telegram', userData),
  
  qrAuth: (inviteCode: string) =>
    api.post('/auth/qr', { invite_code: inviteCode }),
  
  getMe: () =>
    api.get('/auth/me'),
  
  getPermissions: () =>
    api.get('/auth/permissions')
};

// DSE API
export const dseApi = {
  getAll: (params?: any) =>
    api.get('/dse', { params }),
  
  getById: (id: string) =>
    api.get(`/dse/${id}`),
  
  create: (data: any) =>
    api.post('/dse', data),
  
  update: (id: string, data: any) =>
    api.put(`/dse/${id}`, data),
  
  delete: (id: string) =>
    api.delete(`/dse/${id}`),
  
  restore: (id: string) =>
    api.post(`/dse/${id}/restore`),
  
  getPending: () =>
    api.get('/dse/pending'),
  
  approve: (id: string) =>
    api.post(`/dse/${id}/approve`),
  
  reject: (id: string) =>
    api.post(`/dse/${id}/reject`),
  
  getStats: () =>
    api.get('/dse/stats'),
  
  exportExcel: () =>
    api.get('/dse/export/excel', { responseType: 'blob' })
};

// Users API
export const usersApi = {
  getAll: (params?: any) =>
    api.get('/users', { params }),
  
  getById: (id: string) =>
    api.get(`/users/${id}`),
  
  create: (data: any) =>
    api.post('/users', data),
  
  update: (id: string, data: any) =>
    api.put(`/users/${id}`, data),
  
  delete: (id: string) =>
    api.delete(`/users/${id}`),
  
  toggleStatus: (id: string) =>
    api.post(`/users/${id}/toggle-status`),
  
  updateProfile: (data: any) =>
    api.put('/users/profile/me', data),
  
  changePassword: (currentPassword: string, newPassword: string) =>
    api.post('/users/profile/change-password', { 
      current_password: currentPassword, 
      new_password: newPassword 
    })
};

// Invites API
export const invitesApi = {
  getAll: () =>
    api.get('/invites'),
  
  create: (role: string) =>
    api.post('/invites', { role }),
  
  use: (code: string) =>
    api.post('/invites/use', { code }),
  
  delete: (id: string) =>
    api.delete(`/invites/${id}`)
};

// Messages API
export const messagesApi = {
  getAll: (params?: any) =>
    api.get('/messages', { params }),
  
  getRooms: () =>
    api.get('/messages/rooms'),
  
  getUnreadCount: () =>
    api.get('/messages/unread-count'),
  
  send: (data: any) =>
    api.post('/messages', data),
  
  markAsRead: (id: string) =>
    api.put(`/messages/${id}/read`)
};

// Logs API
export const logsApi = {
  getAll: (params?: any) =>
    api.get('/logs', { params }),
  
  getStats: () =>
    api.get('/logs/stats'),
  
  clearOld: (days: number) =>
    api.post('/logs/clear', { days })
};

export default api;
