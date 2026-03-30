import { Log } from '../models';

export const logAction = async (
  level: 'info' | 'warning' | 'error' | 'success',
  message: string,
  action: string,
  userId?: string,
  details?: object,
  ipAddress?: string,
  userAgent?: string
) => {
  try {
    await Log.create({
      level,
      message,
      action,
      user_id: userId,
      details,
      ip_address: ipAddress,
      user_agent: userAgent
    });
  } catch (error) {
    console.error('Failed to log action:', error);
  }
};
