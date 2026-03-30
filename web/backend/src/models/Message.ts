import { DataTypes, Model, Optional } from 'sequelize';
import sequelize from '../config/database';
import User from './User';
import DSE from './DSE';

export interface MessageAttributes {
  id: string;
  content: string;
  sender_id: string;
  receiver_id?: string;
  dse_id?: string;
  room_id?: string;
  is_read: boolean;
  attachments?: string[];
  created_at?: Date;
  updated_at?: Date;
}

interface MessageCreationAttributes extends Optional<MessageAttributes, 'id' | 'created_at' | 'updated_at'> {}

class Message extends Model<MessageAttributes, MessageCreationAttributes> implements MessageAttributes {
  public id!: string;
  public content!: string;
  public sender_id!: string;
  public receiver_id!: string | undefined;
  public dse_id!: string | undefined;
  public room_id!: string | undefined;
  public is_read!: boolean;
  public attachments!: string[] | undefined;
  public readonly created_at!: Date;
  public readonly updated_at!: Date;
}

Message.init(
  {
    id: {
      type: DataTypes.UUID,
      defaultValue: DataTypes.UUIDV4,
      primaryKey: true
    },
    content: {
      type: DataTypes.TEXT,
      allowNull: false
    },
    sender_id: {
      type: DataTypes.UUID,
      allowNull: false,
      references: {
        model: User,
        key: 'id'
      }
    },
    receiver_id: {
      type: DataTypes.UUID,
      allowNull: true,
      references: {
        model: User,
        key: 'id'
      }
    },
    dse_id: {
      type: DataTypes.UUID,
      allowNull: true,
      references: {
        model: DSE,
        key: 'id'
      }
    },
    room_id: {
      type: DataTypes.STRING(100),
      allowNull: true
    },
    is_read: {
      type: DataTypes.BOOLEAN,
      defaultValue: false
    },
    attachments: {
      type: DataTypes.JSON,
      allowNull: true
    }
  },
  {
    sequelize,
    tableName: 'messages',
    timestamps: true,
    underscored: true
  }
);

Message.belongsTo(User, { foreignKey: 'sender_id', as: 'sender' });
Message.belongsTo(User, { foreignKey: 'receiver_id', as: 'receiver' });
Message.belongsTo(DSE, { foreignKey: 'dse_id', as: 'dse' });

export default Message;
