import { DataTypes, Model, Optional } from 'sequelize';
import sequelize from '../config/database';
import User from './User';

export interface InviteAttributes {
  id: string;
  code: string;
  role: 'admin' | 'responder' | 'initiator' | 'user';
  created_by: string;
  created_at?: Date;
  expires_at: Date;
  used_by?: string;
  used_at?: Date;
  status: 'active' | 'used' | 'expired';
}

interface InviteCreationAttributes extends Optional<InviteAttributes, 'id' | 'created_at'> {}

class Invite extends Model<InviteAttributes, InviteCreationAttributes> implements InviteAttributes {
  public id!: string;
  public code!: string;
  public role!: 'admin' | 'responder' | 'initiator' | 'user';
  public created_by!: string;
  public expires_at!: Date;
  public used_by!: string | undefined;
  public used_at!: Date | undefined;
  public status!: 'active' | 'used' | 'expired';
  public readonly created_at!: Date;
}

Invite.init(
  {
    id: {
      type: DataTypes.UUID,
      defaultValue: DataTypes.UUIDV4,
      primaryKey: true
    },
    code: {
      type: DataTypes.STRING(50),
      allowNull: false,
      unique: true
    },
    role: {
      type: DataTypes.ENUM('admin', 'responder', 'initiator', 'user'),
      defaultValue: 'user'
    },
    created_by: {
      type: DataTypes.UUID,
      allowNull: false,
      references: {
        model: User,
        key: 'id'
      }
    },
    expires_at: {
      type: DataTypes.DATE,
      allowNull: false
    },
    used_by: {
      type: DataTypes.UUID,
      allowNull: true,
      references: {
        model: User,
        key: 'id'
      }
    },
    used_at: {
      type: DataTypes.DATE,
      allowNull: true
    },
    status: {
      type: DataTypes.ENUM('active', 'used', 'expired'),
      defaultValue: 'active'
    }
  },
  {
    sequelize,
    tableName: 'invites',
    timestamps: true,
    underscored: true
  }
);

Invite.belongsTo(User, { foreignKey: 'created_by', as: 'creator' });
Invite.belongsTo(User, { foreignKey: 'used_by', as: 'user' });

export default Invite;
