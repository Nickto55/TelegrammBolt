import create from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import apiService from '../services/apiService';

export const useAuthStore = create((set, get) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,

  // Initialize auth state on app start
  initializeAuth: async () => {
    try {
      set({ isLoading: true });
      const token = await AsyncStorage.getItem('authToken');
      
      if (token) {
        // Verify token is still valid
        const user = await apiService.getCurrentUser();
        set({ 
          user, 
          isAuthenticated: true, 
          isLoading: false,
          error: null 
        });
      } else {
        set({ isLoading: false });
      }
    } catch (error) {
      console.error('Auth initialization error:', error);
      set({ isLoading: false });
    }
  },

  // Login
  login: async (email, password) => {
    try {
      set({ isLoading: true, error: null });
      const response = await apiService.login(email, password);
      
      await AsyncStorage.setItem('authToken', response.token);
      await AsyncStorage.setItem('user', JSON.stringify(response.user));
      
      set({ 
        user: response.user, 
        isAuthenticated: true, 
        isLoading: false 
      });
      
      return response;
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Login failed', 
        isLoading: false 
      });
      throw error;
    }
  },

  // Register
  register: async (email, password, fullName) => {
    try {
      set({ isLoading: true, error: null });
      const response = await apiService.register(email, password, fullName);
      
      set({ 
        isLoading: false, 
        error: null 
      });
      
      return response;
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Registration failed', 
        isLoading: false 
      });
      throw error;
    }
  },

  // Link Telegram
  linkTelegram: async (linkingCode) => {
    try {
      set({ isLoading: true, error: null });
      const response = await apiService.linkTelegram(linkingCode);
      
      set({ 
        user: response.user, 
        isLoading: false 
      });
      
      return response;
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Failed to link Telegram', 
        isLoading: false 
      });
      throw error;
    }
  },

  // Logout
  logout: async () => {
    try {
      await AsyncStorage.removeItem('authToken');
      await AsyncStorage.removeItem('user');
      
      set({ 
        user: null, 
        isAuthenticated: false, 
        error: null 
      });
    } catch (error) {
      console.error('Logout error:', error);
    }
  },

  // Update user
  updateUser: (user) => {
    set({ user });
  },

  // Clear error
  clearError: () => set({ error: null }),
}));
