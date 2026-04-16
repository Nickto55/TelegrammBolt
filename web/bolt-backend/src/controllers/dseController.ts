import { Response } from 'express';
import { Op } from 'sequelize';
import { DSE, User } from '../models';
import { logAction } from '../utils/logger';
import { AuthRequest } from '../middleware/auth';

export const getAllDSE = async (req: AuthRequest, res: Response) => {
  try {
    const { 
      search, 
      problem_type, 
      user_id, 
      status, 
      include_hidden,
      sort_by = 'date_desc',
      page = 1,
      limit = 20
    } = req.query;

    const where: any = { archived: false };
    
    if (!include_hidden || include_hidden !== '1') {
      where.hidden = false;
    }

    if (search) {
      where[Op.or] = [
        { dse: { [Op.iLike]: `%${search}%` } },
        { dse_name: { [Op.iLike]: `%${search}%` } },
        { description: { [Op.iLike]: `%${search}%` } }
      ];
    }

    if (problem_type) {
      where.problem_type = problem_type;
    }

    if (user_id) {
      where.user_id = user_id;
    }

    if (status) {
      where.status = status;
    }

    const order: any = [];
    switch (sort_by) {
      case 'date_desc':
        order.push(['datetime', 'DESC']);
        break;
      case 'date_asc':
        order.push(['datetime', 'ASC']);
        break;
      case 'dse_asc':
        order.push(['dse', 'ASC']);
        break;
      case 'dse_desc':
        order.push(['dse', 'DESC']);
        break;
      default:
        order.push(['datetime', 'DESC']);
    }

    const offset = (Number(page) - 1) * Number(limit);

    const { count, rows } = await DSE.findAndCountAll({
      where,
      include: [{ model: User, as: 'user', attributes: ['id', 'first_name', 'last_name'] }],
      order,
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
    console.error('Get all DSE error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const getDSEById = async (req: AuthRequest, res: Response) => {
  try {
    const { id } = req.params;

    const dse = await DSE.findByPk(id, {
      include: [{ model: User, as: 'user', attributes: ['id', 'first_name', 'last_name', 'photo_url'] }]
    });

    if (!dse) {
      return res.status(404).json({ error: 'DSE not found' });
    }

    res.json({ data: dse });
  } catch (error) {
    console.error('Get DSE by id error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const createDSE = async (req: AuthRequest, res: Response) => {
  try {
    const {
      dse,
      dse_name,
      problem_type,
      description,
      machine_number,
      installer_fio,
      programmer_name
    } = req.body;

    if (!dse || !problem_type) {
      return res.status(400).json({ error: 'DSE and problem_type are required' });
    }

    const newDSE = await DSE.create({
      dse,
      dse_name,
      problem_type,
      description,
      machine_number,
      installer_fio,
      programmer_name,
      datetime: new Date(),
      user_id: req.user.id,
      status: 'in_progress',
      hidden: false,
      archived: false
    });

    await logAction('success', `DSE ${dse} created`, 'CREATE_DSE', req.user.id, { dse_id: newDSE.id }, req.ip, req.headers['user-agent'] as string);

    res.status(201).json({
      success: true,
      data: newDSE
    });
  } catch (error) {
    console.error('Create DSE error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const updateDSE = async (req: AuthRequest, res: Response) => {
  try {
    const { id } = req.params;
    const updateData = req.body;

    const dse = await DSE.findByPk(id);

    if (!dse) {
      return res.status(404).json({ error: 'DSE not found' });
    }

    await dse.update(updateData);

    await logAction('success', `DSE ${dse.dse} updated`, 'UPDATE_DSE', req.user.id, { dse_id: id }, req.ip, req.headers['user-agent'] as string);

    res.json({
      success: true,
      data: dse
    });
  } catch (error) {
    console.error('Update DSE error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const deleteDSE = async (req: AuthRequest, res: Response) => {
  try {
    const { id } = req.params;

    const dse = await DSE.findByPk(id);

    if (!dse) {
      return res.status(404).json({ error: 'DSE not found' });
    }

    await dse.update({ hidden: true });

    await logAction('success', `DSE ${dse.dse} hidden`, 'HIDE_DSE', req.user.id, { dse_id: id }, req.ip, req.headers['user-agent'] as string);

    res.json({ success: true });
  } catch (error) {
    console.error('Delete DSE error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const restoreDSE = async (req: AuthRequest, res: Response) => {
  try {
    const { id } = req.params;

    const dse = await DSE.findByPk(id);

    if (!dse) {
      return res.status(404).json({ error: 'DSE not found' });
    }

    await dse.update({ hidden: false });

    await logAction('success', `DSE ${dse.dse} restored`, 'RESTORE_DSE', req.user.id, { dse_id: id }, req.ip, req.headers['user-agent'] as string);

    res.json({ success: true });
  } catch (error) {
    console.error('Restore DSE error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const getPendingRequests = async (req: AuthRequest, res: Response) => {
  try {
    const pending = await DSE.findAll({
      where: { status: 'pending' },
      include: [{ model: User, as: 'user', attributes: ['id', 'first_name', 'last_name'] }],
      order: [['created_at', 'DESC']]
    });

    res.json({ 
      success: true,
      requests: pending 
    });
  } catch (error) {
    console.error('Get pending requests error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const approveRequest = async (req: AuthRequest, res: Response) => {
  try {
    const { id } = req.params;

    const dse = await DSE.findByPk(id);

    if (!dse) {
      return res.status(404).json({ error: 'DSE not found' });
    }

    await dse.update({ status: 'in_progress' });

    await logAction('success', `DSE ${dse.dse} approved`, 'APPROVE_DSE', req.user.id, { dse_id: id }, req.ip, req.headers['user-agent'] as string);

    res.json({ success: true });
  } catch (error) {
    console.error('Approve request error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const rejectRequest = async (req: AuthRequest, res: Response) => {
  try {
    const { id } = req.params;

    const dse = await DSE.findByPk(id);

    if (!dse) {
      return res.status(404).json({ error: 'DSE not found' });
    }

    await dse.update({ archived: true, status: 'completed' });

    await logAction('success', `DSE ${dse.dse} rejected`, 'REJECT_DSE', req.user.id, { dse_id: id }, req.ip, req.headers['user-agent'] as string);

    res.json({ success: true });
  } catch (error) {
    console.error('Reject request error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const getDashboardStats = async (req: AuthRequest, res: Response) => {
  try {
    const totalDSE = await DSE.count({ where: { archived: false, hidden: false } });
    const activeUsers = await User.count({ where: { status: 'active' } });
    
    const oneWeekAgo = new Date();
    oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
    const recentDSE = await DSE.count({ 
      where: { 
        created_at: { [Op.gte]: oneWeekAgo },
        archived: false 
      } 
    });

    // Problem types statistics
    const problemTypes = await DSE.findAll({
      where: { archived: false, hidden: false },
      attributes: ['problem_type']
    });

    const problemTypeCounts: Record<string, number> = {};
    problemTypes.forEach((dse: any) => {
      const type = dse.problem_type;
      problemTypeCounts[type] = (problemTypeCounts[type] || 0) + 1;
    });

    res.json({
      total_dse: totalDSE,
      active_users: activeUsers,
      recent_dse: recentDSE,
      problem_types: problemTypeCounts
    });
  } catch (error) {
    console.error('Get dashboard stats error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const exportToExcel = async (req: AuthRequest, res: Response) => {
  try {
    const dseList = await DSE.findAll({
      where: { archived: false },
      include: [{ model: User, as: 'user', attributes: ['first_name', 'last_name'] }]
    });

    // For now, return JSON. In production, you'd use a library like xlsx
    res.setHeader('Content-Type', 'application/json');
    res.setHeader('Content-Disposition', 'attachment; filename=dse_export.json');
    res.json(dseList);
  } catch (error) {
    console.error('Export to Excel error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};
