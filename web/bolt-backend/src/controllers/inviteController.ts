import { Response } from 'express';
import { Op } from 'sequelize';
import { Invite, User } from '../models';
import { logAction } from '../utils/logger';
import { AuthRequest } from '../middleware/auth';

const generateInviteCode = () => {
  return 'BOLT-' + Math.random().toString(36).substring(2, 8).toUpperCase();
};

export const getAllInvites = async (req: AuthRequest, res: Response) => {
  try {
    const invites = await Invite.findAll({
      include: [
        { model: User, as: 'creator', attributes: ['first_name', 'last_name'] },
        { model: User, as: 'user', attributes: ['first_name', 'last_name'] }
      ],
      order: [['created_at', 'DESC']]
    });

    res.json({ data: invites });
  } catch (error) {
    console.error('Get all invites error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const createInvite = async (req: AuthRequest, res: Response) => {
  try {
    const { role } = req.body;

    const expiresAt = new Date();
    expiresAt.setDate(expiresAt.getDate() + 30);

    const invite = await Invite.create({
      code: generateInviteCode(),
      role: role || 'user',
      created_by: req.user.id,
      expires_at: expiresAt,
      status: 'active'
    });

    await logAction('success', `Invite ${invite.code} created`, 'CREATE_INVITE', req.user.id, { invite_id: invite.id }, req.ip, req.headers['user-agent'] as string);

    res.status(201).json({
      success: true,
      data: invite
    });
  } catch (error) {
    console.error('Create invite error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const useInvite = async (req: AuthRequest, res: Response) => {
  try {
    const { code } = req.body;

    const invite = await Invite.findOne({
      where: {
        code,
        status: 'active',
        expires_at: { [Op.gt]: new Date() }
      }
    });

    if (!invite) {
      return res.status(404).json({ error: 'Invalid or expired invite code' });
    }

    await invite.update({
      status: 'used',
      used_by: req.user.id,
      used_at: new Date()
    });

    await logAction('success', `Invite ${code} used`, 'USE_INVITE', req.user.id, { invite_id: invite.id }, req.ip, req.headers['user-agent'] as string);

    res.json({
      success: true,
      role: invite.role
    });
  } catch (error) {
    console.error('Use invite error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const deleteInvite = async (req: AuthRequest, res: Response) => {
  try {
    const { id } = req.params;

    const invite = await Invite.findByPk(id);

    if (!invite) {
      return res.status(404).json({ error: 'Invite not found' });
    }

    await invite.destroy();

    await logAction('success', `Invite ${invite.code} deleted`, 'DELETE_INVITE', req.user.id, { invite_id: id }, req.ip, req.headers['user-agent'] as string);

    res.json({ success: true });
  } catch (error) {
    console.error('Delete invite error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};
