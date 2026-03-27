import create from 'zustand';
import apiService from '../services/apiService';

export const useChatStore = create((set, get) => ({
  chats: [],
  currentChat: null,
  messages: [],
  isLoading: false,
  error: null,

  // Get Chats
  getChats: async () => {
    try {
      set({ isLoading: true, error: null });
      const response = await apiService.getChats();
      set({ chats: response.chats || [], isLoading: false });
      return response;
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Failed to fetch chats', 
        isLoading: false 
      });
      throw error;
    }
  },

  // Get chat messages
  getChatMessages: async (chatId, page = 1) => {
    try {
      set({ isLoading: true, error: null });
      const response = await apiService.getChatMessages(chatId, page);
      set({ 
        currentChat: { id: chatId },
        messages: response.messages || [], 
        isLoading: false 
      });
      return response;
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Failed to fetch messages', 
        isLoading: false 
      });
      throw error;
    }
  },

  // Send message
  sendMessage: async (chatId, message) => {
    try {
      set({ isLoading: true, error: null });
      const response = await apiService.sendMessage(chatId, message);
      
      const currentMessages = get().messages;
      set({ 
        messages: [...currentMessages, response.message],
        isLoading: false 
      });
      
      return response;
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Failed to send message', 
        isLoading: false 
      });
      throw error;
    }
  },

  // Clear error
  clearError: () => set({ error: null }),
}));
