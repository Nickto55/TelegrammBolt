import jwt, { SignOptions } from 'jsonwebtoken';

const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';
const JWT_EXPIRES_IN = process.env.JWT_EXPIRES_IN || '7d';

export const generateToken = (payload: object): string => {
  // Указываем тип для опций, чтобы TS не путал перегрузки функции
  const options: SignOptions = { 
    expiresIn: JWT_EXPIRES_IN as any // используем as any, так как тип в библиотеке очень строгий
  };
  
  return jwt.sign(payload, JWT_SECRET, options);
};

export const verifyToken = (token: string): any => {
  try {
    return jwt.verify(token, JWT_SECRET);
  } catch (error) {
    return null; // или выбросьте ошибку, если это предусмотрено логикой
  }
};
