/**
 * Validation Utilities
 */

export const isValidEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const isValidPassword = (password) => {
  return password && password.length >= 6;
};

export const isValidName = (name) => {
  return name && name.trim().length >= 2;
};

export const isValidPhone = (phone) => {
  const phoneRegex = /^[\d\s\-\+\(\)]+$/;
  return phone && phoneRegex.test(phone) && phone.replace(/\D/g, '').length >= 10;
};

export const validateEmail = (email) => {
  if (!email) {
    return 'Email обязателен';
  }
  if (!isValidEmail(email)) {
    return 'Некорректный email';
  }
  return null;
};

export const validatePassword = (password) => {
  if (!password) {
    return 'Пароль обязателен';
  }
  if (!isValidPassword(password)) {
    return 'Пароль должен быть не менее 6 символов';
  }
  return null;
};

export const validateName = (name) => {
  if (!name) {
    return 'Имя обязательно';
  }
  if (!isValidName(name)) {
    return 'Имя должно быть не менее 2 символов';
  }
  return null;
};
