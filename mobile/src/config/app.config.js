/**
 * App Configuration
 * Основные конфигурационные параметры приложения
 */

export const APP_CONFIG = {
  // Версия приложения
  VERSION: '1.0.0',
  
  // API Configuration
  API: {
    // Получить URL из .env или использовать default
    BASE_URL: process.env.API_BASE_URL || 'http://localhost:5000',
    TIMEOUT: parseInt(process.env.API_TIMEOUT || '30000'),
    RETRY_ATTEMPTS: 3,
    RETRY_DELAY: 1000,
  },

  // Feature Flags
  FEATURES: {
    PUSH_NOTIFICATIONS: process.env.ENABLE_PUSH_NOTIFICATIONS === 'true',
    OFFLINE_MODE: process.env.ENABLE_OFFLINE_MODE !== 'false',
    QR_SCANNER: true,
    FILE_UPLOAD: true,
  },

  // Security
  SECURITY: {
    USE_SECURE_STORAGE: process.env.SECURE_STORAGE_ENABLED !== 'false',
    TOKEN_STORAGE_KEY: '@auth_token',
    SESSION_TIMEOUT: 30 * 60 * 1000, // 30 minutes
  },

  // UI Configuration
  UI: {
    PRIMARY_COLOR: '#000080',
    SECONDARY_COLOR: '#2196f3',
    ERROR_COLOR: '#f44336',
    SUCCESS_COLOR: '#4caf50',
    WARNING_COLOR: '#ff9800',
    DARK_COLOR: '#333',
    LIGHT_COLOR: '#f5f5f5',
  },

  // Pagination
  PAGINATION: {
    DEFAULT_PAGE_SIZE: 20,
    MAX_PAGE_SIZE: 100,
  },

  // Cache
  CACHE: {
    ENABLED: true,
    TTL: 5 * 60 * 1000, // 5 minutes
  },

  // Validation
  VALIDATION: {
    MIN_PASSWORD_LENGTH: 6,
    MIN_NAME_LENGTH: 2,
    MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
  },
};

export default APP_CONFIG;
