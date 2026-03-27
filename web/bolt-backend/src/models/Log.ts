import { DataTypes, Model, Optional } from 'sequelize';
import sequelize from '../config/database';
import User from './User';

export interface LogAttributes {
  id: string;
  level: 'info' | 'warning' | 'error' | 'success';
  message: string;
  user_id?: string;
  action: string;
  details?: object;
  ip_address?: string;
  user_agent?: string;
  created_at?: Date;
}

interface LogCreationAttributes extends Optional<LogAttributes, 'id' | 'created_at'> {}

class Log extends Model<LogAttributes, LogCreationAttributes> implements LogAttributes {
  public id!: string;
  public level!: 'info' | 'warning' | 'error' | 'success';
  public message!: string;
  public user_id!: string | undefined;
  public action!: string;
  public details!: object | undefined;
  public ip_address!: string | undefined;
  public user_agent!: string | undefined;
  public readonly created_at!: Date;
}

Log.init(
  {
    id: {
      type: DataTypes.UUID,
      defaultValue: DataTypes.UUIDV4,
      primaryKey: true
    },
    level: {
      type: DataTypes.ENUM('info', 'warning', 'error', 'success'),
      defaultValue: 'info'
    },
    message: {
      type: DataTypes.TEXT,
      allowNull: false
    },
    user_id: {
      type: DataTypes.UUID,
      allowNull: true,
      references: {
        model: User,
        key: 'id'
      }
    },
    action: {
      type: DataTypes.STRING(100),
      allowNull: false
    },
    details: {
      type: DataTypes.JSON,
      allowNull: true
    },
    ip_address: {
      type: DataTypes.STRING(45),
      allowNull: true
    },
    user_agent: {
      type: DataTypes.STRING(500),
      allowNull: true
    }
  },
  {
    sequelize,
    tableName: 'logs',
    timestamps: true,
    underscored: true
  }
);

Log.belongsTo(User, { foreignKey: 'user_id', as: 'user' });

export default Log;
