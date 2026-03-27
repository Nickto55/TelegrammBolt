import axios from 'axios/dist/browser/axios.cjs';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:5000';
const API_TIMEOUT = parseInt(process.env.API_TIMEOUT || '30000');

class ApiService {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor
    this.client.interceptors.request.use(
      async (config) => {
        const token = await AsyncStorage.getItem('authToken');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Add response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expired - trigger logout
          AsyncStorage.removeItem('authToken');
          AsyncStorage.removeItem('user');
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth Endpoints
  async login(email, password) {
    const response = await this.client.post('/api/auth/login', {
      email,
      password,
    });
    return response.data;
  }

  async register(email, password, fullName) {
    const response = await this.client.post('/api/auth/register', {
      email,
      password,
      full_name: fullName,
    });
    return response.data;
  }

  async linkTelegram(linkingCode) {
    const response = await this.client.post('/api/auth/link-telegram', {
      linking_code: linkingCode,
    });
    return response.data;
  }

  async getCurrentUser() {
    const response = await this.client.get('/api/auth/profile');
    return response.data;
  }

  // DSE Endpoints
  async getDSEList(page = 1, limit = 20) {
    const response = await this.client.get('/api/dse/list', {
      params: { page, limit },
    });
    return response.data;
  }

  async getDSEDetail(dseId) {
    const response = await this.client.get(`/api/dse/${dseId}`);
    return response.data;
  }

  async searchDSE(query) {
    const response = await this.client.get('/api/dse/search', {
      params: { q: query },
    });
    return response.data;
  }

  async createDSE(dseData) {
    const response = await this.client.post('/api/dse/create', dseData);
    return response.data;
  }

  async updateDSE(dseId, dseData) {
    const response = await this.client.put(`/api/dse/${dseId}`, dseData);
    return response.data;
  }

  // Chat Endpoints
  async getChats() {
    const response = await this.client.get('/api/chat/list');
    return response.data;
  }

  async getChatMessages(chatId, page = 1) {
    const response = await this.client.get(`/api/chat/${chatId}/messages`, {
      params: { page },
    });
    return response.data;
  }

  async sendMessage(chatId, message) {
    const response = await this.client.post(`/api/chat/${chatId}/message`, {
      text: message,
    });
    return response.data;
  }

  // Invites Endpoints
  async getInvites() {
    const response = await this.client.get('/api/invites/list');
    return response.data;
  }

  async createInvite(expiryDays = 7) {
    const response = await this.client.post('/api/invites/create', {
      expiry_days: expiryDays,
    });
    return response.data;
  }

  async useInvite(inviteCode) {
    const response = await this.client.post('/api/invites/use', {
      invite_code: inviteCode,
    });
    return response.data;
  }

  // User Management
  async updateProfile(profileData) {
    const response = await this.client.post('/api/user/profile/update', profileData);
    return response.data;
  }

  async changePassword(oldPassword, newPassword) {
    const response = await this.client.post('/api/user/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    });
    return response.data;
  }

  // File Upload
  async uploadFile(fileUri, fileName) {
    const formData = new FormData();
    formData.append('file', {
      uri: fileUri,
      name: fileName,
      type: 'image/jpeg',
    });

    const response = await this.client.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  // PDF Export
  async exportDSEPDF(dseId) {
    const response = await this.client.get(`/api/dse/${dseId}/export-pdf`, {
      responseType: 'blob',
    });
    return response.data;
  }
}

export const apiService = new ApiService();
export default apiService;
