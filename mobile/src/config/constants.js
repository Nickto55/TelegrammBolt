/**
 * Types and Constants for the App
 */

export const USER_ROLES = {
  ADMIN: 'admin',
  MANAGER: 'manager',
  USER: 'user',
  GUEST: 'guest',
};

export const DSE_STATUS = {
  PENDING: 'pending',
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
  REJECTED: 'rejected',
  ARCHIVED: 'archived',
};

export const DSE_STATUS_LABELS = {
  pending: 'На заседании',
  in_progress: 'В работе',
  completed: 'Завершено',
  rejected: 'Отклонено',
  archived: 'Архивировано',
};

export const HTTP_STATUS_CODES = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  INTERNAL_SERVER_ERROR: 500,
  SERVICE_UNAVAILABLE: 503,
};

export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Ошибка сети. Пожалуйста, проверьте подключение к интернету',
  SERVER_ERROR: 'Ошибка сервера. Попробуйте позже',
  UNAUTHORIZED: 'Требуется вход',
  FORBIDDEN: 'Доступ запрещен',
  NOT_FOUND: 'Данные не найдены',
  VALIDATION_ERROR: 'Ошибка валидации',
  UNKNOWN_ERROR: 'Произошла неизвестная ошибка',
};

export const ASYNC_STATES = {
  IDLE: 'idle',
  LOADING: 'loading',
  SUCCESS: 'success',
  ERROR: 'error',
};
