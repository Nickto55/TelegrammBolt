import { DataTypes, Model, Optional } from 'sequelize';
import sequelize from '../config/database';
import User from './User';

export interface DSEAttributes {
  id: string;
  dse: string;
  dse_name?: string;
  problem_type: string;
  description?: string;
  machine_number?: string;
  installer_fio?: string;
  programmer_name?: string;
  datetime: Date;
  user_id: string;
  status: 'in_progress' | 'completed' | 'pending';
  hidden: boolean;
  archived: boolean;
  created_at?: Date;
  updated_at?: Date;
}

interface DSECreationAttributes extends Optional<DSEAttributes, 'id' | 'created_at' | 'updated_at'> {}

class DSE extends Model<DSEAttributes, DSECreationAttributes> implements DSEAttributes {
  public id!: string;
  public dse!: string;
  public dse_name!: string | undefined;
  public problem_type!: string;
  public description!: string | undefined;
  public machine_number!: string | undefined;
  public installer_fio!: string | undefined;
  public programmer_name!: string | undefined;
  public datetime!: Date;
  public user_id!: string;
  public status!: 'in_progress' | 'completed' | 'pending';
  public hidden!: boolean;
  public archived!: boolean;
  public readonly created_at!: Date;
  public readonly updated_at!: Date;
}

DSE.init(
  {
    id: {
      type: DataTypes.UUID,
      defaultValue: DataTypes.UUIDV4,
      primaryKey: true
    },
    dse: {
      type: DataTypes.STRING(50),
      allowNull: false
    },
    dse_name: {
      type: DataTypes.STRING(200),
      allowNull: true
    },
    problem_type: {
      type: DataTypes.STRING(100),
      allowNull: false
    },
    description: {
      type: DataTypes.TEXT,
      allowNull: true
    },
    machine_number: {
      type: DataTypes.STRING(50),
      allowNull: true
    },
    installer_fio: {
      type: DataTypes.STRING(200),
      allowNull: true
    },
    programmer_name: {
      type: DataTypes.STRING(200),
      allowNull: true
    },
    datetime: {
      type: DataTypes.DATE,
      allowNull: false,
      defaultValue: DataTypes.NOW
    },
    user_id: {
      type: DataTypes.UUID,
      allowNull: false,
      references: {
        model: User,
        key: 'id'
      }
    },
    status: {
      type: DataTypes.ENUM('in_progress', 'completed', 'pending'),
      defaultValue: 'in_progress'
    },
    hidden: {
      type: DataTypes.BOOLEAN,
      defaultValue: false
    },
    archived: {
      type: DataTypes.BOOLEAN,
      defaultValue: false
    }
  },
  {
    sequelize,
    tableName: 'dse',
    timestamps: true,
    underscored: true
  }
);

DSE.belongsTo(User, { foreignKey: 'user_id', as: 'user' });
User.hasMany(DSE, { foreignKey: 'user_id', as: 'dse' });

export default DSE;
