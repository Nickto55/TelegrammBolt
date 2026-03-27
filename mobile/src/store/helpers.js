/**
 * Create Store Hook
 * Вспомогательная функция для создания store с error handling
 */

import create from 'zustand';

export const createAsyncStore = (initialState, actions) => {
  return create((set, get) => ({
    ...initialState,
    ...Object.keys(actions).reduce((acc, key) => {
      acc[key] = async (...args) => {
        const action = actions[key];
        try {
          await action(set, get, ...args);
        } catch (error) {
          console.error(`Error in ${key}:`, error);
          set({ error: error.message });
          throw error;
        }
      };
      return acc;
    }, {}),
  }));
};

/**
 * Async Thunk Helper
 * Для обработки async операций с loading состоянием
 */
export const createAsyncThunk = (asyncFn) => {
  return async (set, get, ...args) => {
    try {
      set({ isLoading: true, error: null });
      const result = await asyncFn(...args);
      set({ isLoading: false });
      return result;
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error.message || 'Unknown error'
      });
      throw error;
    }
  };
};
