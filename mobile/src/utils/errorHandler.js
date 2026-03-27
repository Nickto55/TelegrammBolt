import axios from 'axios';

/**
 * Error Handler for API calls
 */
export class ApiError extends Error {
  constructor(message, statusCode = null, data = null) {
    super(message);
    this.statusCode = statusCode;
    this.data = data;
  }
}

/**
 * Handle API errors
 */
export const handleApiError = (error) => {
  console.error('API Error:', error);

  if (error.response) {
    // Server responded with error status
    const { status, data } = error.response;
    const message = data?.message || data?.error || 'Произошла ошибка сервера';
    return new ApiError(message, status, data);
  } else if (error.request) {
    // Request made but no response
    return new ApiError('Нет соединения с сервером', null);
  } else {
    // Error in request setup
    return new ApiError('Ошибка: ' + error.message);
  }
};

/**
 * Format error message for UI
 */
export const formatErrorMessage = (error) => {
  if (error instanceof ApiError) {
    return error.message;
  }
  return error?.message || 'Произошла неизвестная ошибка';
};

/**
 * Retry logic for failed requests
 */
export const retryRequest = async (fn, maxAttempts = 3, delay = 1000) => {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxAttempts - 1) throw error;
      // Exponential backoff
      await new Promise((resolve) =>
        setTimeout(resolve, delay * Math.pow(2, i))
      );
    }
  }
};
