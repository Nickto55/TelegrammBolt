import sequelize from '../config/database';
import User from './User';
import DSE from './DSE';
import Invite from './Invite';
import Message from './Message';
import Log from './Log';

// Sync all models with database
export const syncDatabase = async (force = false) => {
  try {
    await sequelize.sync({ force });
    console.log('Database synchronized successfully');
  } catch (error) {
    console.error('Error synchronizing database:', error);
    throw error;
  }
};

export { sequelize, User, DSE, Invite, Message, Log };
