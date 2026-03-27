import create from 'zustand';
import apiService from '../services/apiService';

export const useDSEStore = create((set, get) => ({
  dseList: [],
  selectedDSE: null,
  isLoading: false,
  error: null,
  pagination: { page: 1, limit: 20, total: 0 },

  // Get DSE List
  getDSEList: async (page = 1) => {
    try {
      set({ isLoading: true, error: null });
      const response = await apiService.getDSEList(page, 20);
      
      set({ 
        dseList: response.dse_records || [], 
        pagination: {
          page,
          limit: 20,
          total: response.total || 0,
        },
        isLoading: false 
      });
      
      return response;
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Failed to fetch DSE list', 
        isLoading: false 
      });
      throw error;
    }
  },

  // Get DSE Detail
  getDSEDetail: async (dseId) => {
    try {
      set({ isLoading: true, error: null });
      const response = await apiService.getDSEDetail(dseId);
      
      set({ 
        selectedDSE: response, 
        isLoading: false 
      });
      
      return response;
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Failed to fetch DSE details', 
        isLoading: false 
      });
      throw error;
    }
  },

  // Search DSE
  searchDSE: async (query) => {
    try {
      set({ isLoading: true, error: null });
      const response = await apiService.searchDSE(query);
      
      set({ 
        dseList: response.results || [], 
        isLoading: false 
      });
      
      return response;
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Search failed', 
        isLoading: false 
      });
      throw error;
    }
  },

  // Create DSE
  createDSE: async (dseData) => {
    try {
      set({ isLoading: true, error: null });
      const response = await apiService.createDSE(dseData);
      
      set({ 
        isLoading: false,
        selectedDSE: response 
      });
      
      return response;
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Failed to create DSE', 
        isLoading: false 
      });
      throw error;
    }
  },

  // Update DSE
  updateDSE: async (dseId, dseData) => {
    try {
      set({ isLoading: true, error: null });
      const response = await apiService.updateDSE(dseId, dseData);
      
      set({ 
        selectedDSE: response, 
        isLoading: false 
      });
      
      return response;
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Failed to update DSE', 
        isLoading: false 
      });
      throw error;
    }
  },

  // Clear error
  clearError: () => set({ error: null }),

  // Clear selected DSE
  clearSelectedDSE: () => set({ selectedDSE: null }),
}));
