import { Response } from 'express';
import bcrypt from 'bcryptjs';
import { User } from '../models';
import { logAction } from '../utils/logger';
import { AuthRequest } from '../middleware/auth';

export const getAllUsers = async (req: AuthRequest, res: Response) => {
  try {
    const { search, role, status } = req.query;

    const where: any = {};

    if (search) {
      where[Op.or] = [
        { first_name: { [Op.iLike]: `%${search}%` } },
        { last_name: { [Op.iLike]: `%${search}%` } },
        { username: { [Op.iLike]: `%${search}%` } },
        { email: { [Op.iLike]: `%${search}%` } }
      ];
    }

    if (role) {
      where.role = role;
    }

    if (status) {
      where.status = status;
    }

    const users = await User.findAll({
      where,
      attributes: ['id', 'first_name', 'last_name', 'username', 'email', 'photo_url', 'role', 'status', 'created_at', 'last_login'],
      order: [['created_at', 'DESC']]
    });

    res.json({ data: users });
  } catch (error) {
    console.error('Get all users error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const getUserById = async (req: AuthRequest, res: Response) => {
  try {
    const { id } = req.params;

    const user = await User.findByPk(id, {
      attributes: ['id', 'first_name', 'last_name', 'username', 'email', 'photo_url', 'role', 'auth_type', 'telegram_linked', 'status', 'created_at', 'last_login']
    });

    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    res.json({ data: user });
  } catch (error) {
    console.error('Get user by id error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const createUser = async (req: AuthRequest, res: Response) => {
  try {
    const { first_name, last_name, username, email, password, role } = req.body;

    if (!first_name || !username || !password) {
      return res.status(400).json({ error: 'First name, username and password are required' });
    }

    const existingUser = await User.findOne({
      where: { [Op.or]: [{ username }, { email }] }
    });

    if (existingUser) {
      return res.status(409).json({ error: 'Username or email already exists' });
    }

    const hashedPassword = await bcrypt.hash(password, 10);

    const user = await User.create({
      first_name,
      last_name,
      username,
      email,
      password: hashedPassword,
      role: role || 'user',
      auth_type: 'admin',
      status: 'active'
    });

    await logAction('success', `User ${username} created`, 'CREATE_USER', req.user.id, { created_user_id: user.id }, req.ip, req.headers['user-agent'] as string);

    res.status(201).json({
      success: true,
      data: {
        id: user.id,
        first_name: user.first_name,
        last_name: user.last_name,
        username: user.username,
        email: user.email,
        role: user.role,
        status: user.status
      }
    });
  } catch (error) {
    console.error('Create user error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const updateUser = async (req: AuthRequest, res: Response) => {
  try {
    const { id } = req.params;
    const { first_name, last_name, email, role, status } = req.body;

    const user = await User.findByPk(id);

    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    await user.update({ first_name, last_name, email, role, status });

    await logAction('success', `User ${user.username} updated`, 'UPDATE_USER', req.user.id, { updated_user_id: id }, req.ip, req.headers['user-agent'] as string);

    res.json({
      success: true,
      data: user
    });
  } catch (error) {
    console.error('Update user error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const deleteUser = async (req: AuthRequest, res: Response) => {
  try {
    const { id } = req.params;

    const user = await User.findByPk(id);

    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    if (user.id === req.user.id) {
      return res.status(400).json({ error: 'Cannot delete yourself' });
    }

    await user.destroy();

    await logAction('success', `User ${user.username} deleted`, 'DELETE_USER', req.user.id, { deleted_user_id: id }, req.ip, req.headers['user-agent'] as string);

    res.json({ success: true });
  } catch (error) {
    console.error('Delete user error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const toggleUserStatus = async (req: AuthRequest, res: Response) => {
  try {
    const { id } = req.params;

    const user = await User.findByPk(id);

    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    if (user.id === req.user.id) {
      return res.status(400).json({ error: 'Cannot change your own status' });
    }

    const newStatus = user.status === 'active' ? 'inactive' : 'active';
    await user.update({ status: newStatus });

    await logAction('success', `User ${user.username} status changed to ${newStatus}`, 'TOGGLE_USER_STATUS', req.user.id, { user_id: id }, req.ip, req.headers['user-agent'] as string);

    res.json({ success: true, status: newStatus });
  } catch (error) {
    console.error('Toggle user status error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const updateProfile = async (req: AuthRequest, res: Response) => {
  try {
    const { first_name, last_name, email } = req.body;

    const user = await User.findByPk(req.user.id);

    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    await user.update({ first_name, last_name, email });

    await logAction('success', 'Profile updated', 'UPDATE_PROFILE', req.user.id, {}, req.ip, req.headers['user-agent'] as string);

    res.json({
      success: true,
      data: user
    });
  } catch (error) {
    console.error('Update profile error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const changePassword = async (req: AuthRequest, res: Response) => {
  try {
    const { current_password, new_password } = req.body;

    const user = await User.findByPk(req.user.id);

    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    const isValidPassword = await bcrypt.compare(current_password, user.password || '');
    
    if (!isValidPassword) {
      return res.status(401).json({ error: 'Current password is incorrect' });
    }

    const hashedPassword = await bcrypt.hash(new_password, 10);
    await user.update({ password: hashedPassword });

    await logAction('success', 'Password changed', 'CHANGE_PASSWORD', req.user.id, {}, req.ip, req.headers['user-agent'] as string);

    res.json({ success: true });
  } catch (error) {
    console.error('Change password error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};
