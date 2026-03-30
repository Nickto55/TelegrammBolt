import { Response } from 'express';
import { Op } from 'sequelize';
import { Log, User } from '../models';
import { AuthRequest } from '../middleware/auth';

export const getLogs = async (req: AuthRequest, res: Response) => {
  try {
    const { level, action, user_id, start_date, end_date, page = 1, limit = 50 } = req.query;

    const where: any = {};

    if (level) {
      where.level = level;
    }

    if (action) {
      where.action = { [Op.iLike]: `%${action}%` };
    }

    if (user_id) {
      where.user_id = user_id;
    }

    if (start_date || end_date) {
      where.created_at = {};
      if (start_date) {
        where.created_at[Op.gte] = new Date(start_date as string);
      }
      if (end_date) {
        where.created_at[Op.lte] = new Date(end_date as string);
      }
    }

    const offset = (Number(page) - 1) * Number(limit);

    const { count, rows } = await Log.findAndCountAll({
      where,
      include: [
        { model: User, as: 'user', attributes: ['id', 'first_name', 'last_name'] }
      ],
      order: [['created_at', 'DESC']],
      limit: Number(limit),
      offset
    });

    res.json({
      data: rows,
      pagination: {
        total: count,
        page: Number(page),
        pages: Math.ceil(count / Number(limit)),
        limit: Number(limit)
      }
    });
  } catch (error) {
    console.error('Get logs error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const getLogStats = async (req: AuthRequest, res: Response) => {
  try {
    const totalLogs = await Log.count();
    const errorLogs = await Log.count({ where: { level: 'error' } });
    const warningLogs = await Log.count({ where: { level: 'warning' } });
    const infoLogs = await Log.count({ where: { level: 'info' } });
    const successLogs = await Log.count({ where: { level: 'success' } });

    // Get recent actions
    const recentActions = await Log.findAll({
      limit: 10,
      order: [['created_at', 'DESC']],
      include: [
        { model: User, as: 'user', attributes: ['first_name', 'last_name'] }
      ]
    });

    res.json({
      stats: {
        total: totalLogs,
        error: errorLogs,
        warning: warningLogs,
        info: infoLogs,
        success: successLogs
      },
      recent_actions: recentActions
    });
  } catch (error) {
    console.error('Get log stats error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const clearOldLogs = async (req: AuthRequest, res: Response) => {
  try {
    const { days = 30 } = req.body;

    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - days);

    const deleted = await Log.destroy({
      where: {
        created_at: { [Op.lt]: cutoffDate }
      }
    });

    res.json({
      success: true,
      deleted_count: deleted
    });
  } catch (error) {
    console.error('Clear old logs error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};
