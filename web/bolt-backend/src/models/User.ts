import { DataTypes, Model, Optional } from 'sequelize';
import sequelize from '../config/database';

export interface UserAttributes {
  id: string;
  first_name: string;
  last_name?: string;
  username?: string;
  email?: string;
  password?: string;
  photo_url?: string;
  role: 'admin' | 'responder' | 'initiator' | 'user';
  auth_type: 'telegram' | 'qr' | 'admin';
  telegram_id?: string;
  telegram_linked: boolean;
  status: 'active' | 'inactive' | 'banned';
  last_login?: Date;
  created_at?: Date;
  updated_at?: Date;
}

interface UserCreationAttributes extends Optional<UserAttributes, 'id' | 'created_at' | 'updated_at'> {}

class User extends Model<UserAttributes, UserCreationAttributes> implements UserAttributes {
  public id!: string;
  public first_name!: string;
  public last_name!: string | undefined;
  public username!: string | undefined;
  public email!: string | undefined;
  public password!: string | undefined;
  public photo_url!: string | undefined;
  public role!: 'admin' | 'responder' | 'initiator' | 'user';
  public auth_type!: 'telegram' | 'qr' | 'admin';
  public telegram_id!: string | undefined;
  public telegram_linked!: boolean;
  public status!: 'active' | 'inactive' | 'banned';
  public last_login!: Date | undefined;
  public readonly created_at!: Date;
  public readonly updated_at!: Date;
}

User.init(
  {
    id: {
      type: DataTypes.UUID,
      defaultValue: DataTypes.UUIDV4,
      primaryKey: true
    },
    first_name: {
      type: DataTypes.STRING(100),
      allowNull: false
    },
    last_name: {
      type: DataTypes.STRING(100),
      allowNull: true
    },
    username: {
      type: DataTypes.STRING(50),
      allowNull: true,
      unique: true
    },
    email: {
      type: DataTypes.STRING(255),
      allowNull: true,
      unique: true
    },
    password: {
      type: DataTypes.STRING(255),
      allowNull: true
    },
    photo_url: {
      type: DataTypes.STRING(500),
      allowNull: true
    },
    role: {
      type: DataTypes.ENUM('admin', 'responder', 'initiator', 'user'),
      defaultValue: 'user'
    },
    auth_type: {
      type: DataTypes.ENUM('telegram', 'qr', 'admin'),
      defaultValue: 'admin'
    },
    telegram_id: {
      type: DataTypes.STRING(50),
      allowNull: true,
      unique: true
    },
    telegram_linked: {
      type: DataTypes.BOOLEAN,
      defaultValue: false
    },
    status: {
      type: DataTypes.ENUM('active', 'inactive', 'banned'),
      defaultValue: 'active'
    },
    last_login: {
      type: DataTypes.DATE,
      allowNull: true
    }
  },
  {
    sequelize,
    tableName: 'users',
    timestamps: true,
    underscored: true
  }
);

export default User;
